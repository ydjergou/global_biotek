import pandas as pd
import numpy as np
import os
from pathlib import Path

# Create data directory
base_dir = Path(__file__).resolve().parent
data_dir = base_dir / 'data'
data_dir.mkdir(parents=True, exist_ok=True)

# Bacteria (ESKAPE)
bacteria = [
    'Enterococcus faecium', 'Staphylococcus aureus', 'Klebsiella pneumoniae',
    'Acinetobacter baumannii', 'Pseudomonas aeruginosa', 'Enterobacter species',
    'Escherichia coli', 'Proteus mirabilis', 'Serratia marcescens'
]

# ECOWAS Countries (8)
countries = ['Benin', 'Burkina Faso', 'Ivory Coast', 'Ghana', 'Mali', 'Nigeria', 'Senegal', 'Togo']

# Collection Sites (6)
sites = ['Blood', 'Urine', 'Pus', 'Sputum', 'CSF', 'Wound']

# Antibiotics (23)
antibiotics = [
    'Amoxicillin/Clavulanate', 'Ampicillin', 'Ceftriaxone', 'Ceftazidime', 'Cefotaxime',
    'Cefepime', 'Imipenem', 'Meropenem', 'Ertapenem', 'Ciprofloxacin',
    'Levofloxacin', 'Gentamicin', 'Amikacin', 'Tobramycin', 'Trimethoprim/Sulfamethoxazole',
    'Tetracycline', 'Doxycycline', 'Clindamycin', 'Erythromycin', 'Linezolid',
    'Vancomycin', 'Piperacillin/Tazobactam', 'Nitrofurantoin'
]

# Generate antibiograms_clean.csv
# User mentioned 64k records
num_records = 64000
data = []

for _ in range(num_records):
    record = {
        'bacteria': np.random.choice(bacteria),
        'country': np.random.choice(countries),
        'site': np.random.choice(sites)
    }
    # Add antibiotic resistance results (0: Sensitive, 1: Resistant, 2: Intermediate)
    for ab in antibiotics:
        res = np.random.choice([0, 1, 2], p=[0.6, 0.3, 0.1])
        record[ab] = res
    data.append(record)

df_antibiograms = pd.DataFrame(data)
df_antibiograms.to_csv(data_dir / 'antibiograms_clean.csv', index=False)

# Generate resist_rate_pair.csv (for heatmap/stats)
resist_rates = []
for bact in bacteria:
    for ab in antibiotics:
        for country in countries:
            rate = np.random.uniform(0.1, 0.9)
            resist_rates.append({
                'bacteria': bact,
                'antibiotic': ab,
                'country': country,
                'resistance_rate': rate
            })

df_resist_rates = pd.DataFrame(resist_rates)
df_resist_rates.to_csv(data_dir / 'resist_rate_pair.csv', index=False)

print(f"Mock data generated successfully in {data_dir} folder.")
