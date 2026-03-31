from flask import Flask, render_template, request, send_file, jsonify, url_for
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from pathlib import Path
from model_utils import RecommendationEngine
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import plotly

app = Flask(__name__)
engine = RecommendationEngine()

# Paths
base_dir = Path(__file__).resolve().parent
data_path = base_dir / 'data' / 'antibiograms_clean.csv'
resist_path = base_dir / 'data' / 'resist_rate_pair.csv'

# Bacteria, countries, sites lists for forms
if data_path.exists():
    df_data = pd.read_csv(data_path)
    bacteria_list = sorted(df_data['bacteria'].unique().tolist())
    countries_list = sorted(df_data['country'].unique().tolist())
    sites_list = sorted(df_data['site'].unique().tolist())
else:
    df_data = pd.DataFrame()
    bacteria_list = []
    countries_list = []
    sites_list = []

@app.route('/')
def home():
    # Basic KPIs
    kpis = {
        'total_records': len(df_data) if not df_data.empty else 0,
        'countries': len(countries_list),
        'pathogens': len(bacteria_list),
        'antibiotics': 23
    }
    return render_template('index.html', kpis=kpis)

@app.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    results = None
    cocktails = []
    selection = None
    
    if request.method == 'POST':
        bacteria = request.form.get('bacteria')
        country = request.form.get('country')
        site = request.form.get('site')
        
        if bacteria and country and site:
            results = engine.predict(bacteria, country, site)
            cocktails = engine.get_cocktails(results)
            selection = {'bacteria': bacteria, 'country': country, 'site': site}
            
    return render_template('recommendation.html', 
                           bacteria_list=bacteria_list, 
                           countries_list=countries_list, 
                           sites_list=sites_list,
                           results=results,
                           cocktails=cocktails,
                           selection=selection)

@app.route('/heatmap')
def heatmap():
    if not resist_path.exists():
        return "Données de heatmap introuvables. Veuillez exécuter generate_mock_data.py.", 404
        
    df_rates = pd.read_csv(resist_path)
    
    # Pivot for heatmap: bacteria x antibiotic (avg across countries)
    pivot_df = df_rates.groupby(['bacteria', 'antibiotic'])['resistance_rate'].mean().unstack()
    
    fig = px.imshow(pivot_df, 
                    labels=dict(x="Antibiotique", y="Bactérie", color="Taux de Résistance"),
                    x=pivot_df.columns,
                    y=pivot_df.index,
                    color_continuous_scale="RdYlGn_r",
                    title="Heatmap Globale de Résistance (Moyenne par pays)")
    
    heatmap_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('heatmap.html', heatmap_json=heatmap_json)

@app.route('/statistics')
def statistics():
    if df_data.empty:
        return "Données statistiques introuvables. Veuillez exécuter generate_mock_data.py.", 404

    # Top pathogens
    pathogen_counts = df_data['bacteria'].value_counts().reset_index()
    pathogen_counts.columns = ['Bacteria', 'Count']
    fig_pathogens = px.bar(pathogen_counts, x='Bacteria', y='Count', title="Top Pathogènes")
    
    # Resistance trends (S/I/R distribution)
    ab_cols = engine.antibiotics
    all_res = df_data[ab_cols].melt()
    res_dist = all_res['value'].value_counts().reset_index()
    res_dist.columns = ['Status', 'Count']
    res_dist['Status'] = res_dist['Status'].map({0: 'Sensible', 1: 'Résistant', 2: 'Incertain'})
    fig_res = px.pie(res_dist, values='Count', names='Status', title="Répartition S/I/R Globale")
    
    stats_json = {
        'pathogens': fig_pathogens.to_json(),
        'resistance': fig_res.to_json()
    }
    
    kpis = {
        'total_records': len(df_data)
    }
    
    return render_template('statistics.html', stats_json=stats_json, kpis=kpis)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    bacteria = request.form.get('bacteria')
    country = request.form.get('country')
    site = request.form.get('site')
    results_json = request.form.get('results')
    results = json.loads(results_json) if results_json else []
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Global Biotek - Rapport de Recommandation")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 80, f"Bactérie: {bacteria}")
    p.drawString(100, height - 100, f"Pays: {country}")
    p.drawString(100, height - 120, f"Site: {site}")
    
    p.line(100, height - 130, 500, height - 130)
    
    p.drawString(100, height - 150, "Top 10 Antibiotiques Recommandés:")
    y = height - 170
    for res in results[:10]:
        p.drawString(120, y, f"- {res['antibiotic']}: {res['status']} ({res['confidence']}%)")
        y -= 20
        if y < 50:
            p.showPage()
            y = height - 50
            
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(100, 50, "Note: Ce rapport est généré par une IA et ne remplace pas l'avis d'un médecin.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"recommendation_{bacteria}.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
