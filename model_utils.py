import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
import pickle
import os
from pathlib import Path

class RecommendationEngine:
    def __init__(self, data_path=None):
        self.base_dir = Path(__file__).resolve().parent
        if data_path is None:
            self.data_path = self.base_dir / 'data' / 'antibiograms_clean.csv'
        else:
            self.data_path = Path(data_path)
            
        self.models_dir = self.base_dir / 'models'
        self.model_file = self.models_dir / 'engine.pkl'
        
        self.models = {}
        self.label_encoders = {}
        self.antibiotics = [
            'Amoxicillin/Clavulanate', 'Ampicillin', 'Ceftriaxone', 'Ceftazidime', 'Cefotaxime',
            'Cefepime', 'Imipenem', 'Meropenem', 'Ertapenem', 'Ciprofloxacin',
            'Levofloxacin', 'Gentamicin', 'Amikacin', 'Tobramycin', 'Trimethoprim/Sulfamethoxazole',
            'Tetracycline', 'Doxycycline', 'Clindamycin', 'Erythromycin', 'Linezolid',
            'Vancomycin', 'Piperacillin/Tazobactam', 'Nitrofurantoin'
        ]
        self.features = ['bacteria', 'country', 'site']
        self.load_or_train()

    def load_or_train(self):
        if self.model_file.exists():
            with open(self.model_file, 'rb') as f:
                state = pickle.load(f)
                self.models = state['models']
                self.label_encoders = state['label_encoders']
        else:
            self.train()

    def train(self):
        print(f"Training models using {self.data_path}...")
        if not self.data_path.exists():
            raise FileNotFoundError(f"Le fichier de données est introuvable à l'emplacement : {self.data_path}. Veuillez d'abord exécuter generate_mock_data.py.")
            
        df = pd.read_csv(self.data_path)
        
        # Prepare encoders
        for feat in self.features:
            le = LabelEncoder()
            df[feat] = le.fit_transform(df[feat])
            self.label_encoders[feat] = le
        
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        for ab in self.antibiotics:
            df_ab = df[self.features + [ab]].dropna()
            X = df_ab[self.features]
            y = df_ab[ab]
            
            model = GradientBoostingClassifier(n_estimators=50, max_depth=3)
            model.fit(X, y)
            self.models[ab] = model
            
        with open(self.model_file, 'wb') as f:
            pickle.dump({'models': self.models, 'label_encoders': self.label_encoders}, f)
        print("Models trained and saved.")

    def predict(self, bacteria, country, site):
        input_data = pd.DataFrame([{
            'bacteria': self.label_encoders['bacteria'].transform([bacteria])[0],
            'country': self.label_encoders['country'].transform([country])[0],
            'site': self.label_encoders['site'].transform([site])[0]
        }])
        
        results = []
        for ab, model in self.models.items():
            probs = model.predict_proba(input_data)[0]
            classes = model.classes_
            prob_map = dict(zip(classes, probs))
            
            s_prob = prob_map.get(0, 0.0)
            r_prob = prob_map.get(1, 0.0)
            i_prob = prob_map.get(2, 0.0)
            
            if s_prob > 0.7:
                status = 'Sensible'
                confidence = s_prob
            elif r_prob > 0.7:
                status = 'Résistant'
                confidence = r_prob
            else:
                status = 'Incertain'
                confidence = max(s_prob, r_prob, i_prob)
                
            results.append({
                'antibiotic': ab,
                'status': status,
                'confidence': round(confidence * 100, 1),
                's_prob': s_prob,
                'r_prob': r_prob,
                'i_prob': i_prob
            })
            
        results = sorted(results, key=lambda x: x['s_prob'], reverse=True)
        return results

    def get_cocktails(self, predictions):
        sensible = [p for p in predictions if p['status'] == 'Sensible'][:4]
        cocktails = []
        if len(sensible) >= 2:
            cocktails.append({
                'pair': (sensible[0]['antibiotic'], sensible[1]['antibiotic']),
                'score': round((sensible[0]['s_prob'] + sensible[1]['s_prob']) / 2 * 100, 1)
            })
            if len(sensible) >= 4:
                cocktails.append({
                    'pair': (sensible[2]['antibiotic'], sensible[3]['antibiotic']),
                    'score': round((sensible[2]['s_prob'] + sensible[3]['s_prob']) / 2 * 100, 1)
                })
        return cocktails

if __name__ == "__main__":
    engine = RecommendationEngine()
    res = engine.predict('Staphylococcus aureus', 'Senegal', 'Blood')
    print(res[:5])
