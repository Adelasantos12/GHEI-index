import pandas as pd
import numpy as np
import os

def load_dashboard_data():
    # Load main panel
    df = pd.read_csv('final_panel.csv')

    # Load country names mapping
    try:
        names_df = pd.read_csv('D_WPI_Long_format.csv')
        iso_to_name = names_df.set_index('ISO')['Country'].to_dict()
    except:
        iso_to_name = {}

    df['CountryName'] = df['ISO'].map(iso_to_name).fillna(df['ISO'])

    # Load CAS data (prefer dep version which has lags/SHAP/residuals)
    try:
        if os.path.exists('panel_cas_dep.csv'):
            df_cas = pd.read_csv('panel_cas_dep.csv')
        else:
            df_cas = pd.read_csv('panel_cas.csv')
    except:
        df_cas = pd.DataFrame()

    # Load sensitivity
    try:
        df_topk = pd.read_csv('sensitivity_topk.csv')
    except:
        df_topk = pd.DataFrame()

    return {
        'main': df,
        'cas': df_cas,
        'topk': df_topk,
        'iso_map': iso_to_name
    }

def get_pillar_cols(variant='eq'):
    return [f'pillar_A_{variant}', f'pillar_B_{variant}', f'pillar_C_{variant}', f'pillar_D_{variant}']

def get_metadata():
    return {
        'pillars': {
            'A': 'Preparedness & Health Security',
            'B': 'Domestic Efforts & Health System',
            'C': 'International Cooperation & WHO Participation',
            'D': 'Structural Power & Global Health Leadership'
        },
        'indices': {
            'GHEI': 'Global Health Engagement Index (Raw)',
            'GHEI_adj': 'GHEI Adjusted (Residuals from WPI)',
            'GHEI_raw': 'GHEI before structural adjustment'
        }
    }
