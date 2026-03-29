import pandas as pd
import numpy as np
import os

def load_dashboard_data():
    # Load main panel
    df = pd.read_csv('final_panel.csv')

    # Load country names mapping from A_GHSIndex.csv (usually more comprehensive)
    iso_to_name = {}
    try:
        if os.path.exists('A_GHSIndex.csv'):
            names_df = pd.read_csv('A_GHSIndex.csv')
            # Assuming first column is Country and second is ISO
            # Let's try to be smart about column names
            col_country = names_df.columns[0]
            col_iso = names_df.columns[1]
            iso_to_name = names_df[[col_iso, col_country]].drop_duplicates().set_index(col_iso)[col_country].to_dict()
        elif os.path.exists('D_WPI_Long_format.csv'):
            names_df = pd.read_csv('D_WPI_Long_format.csv')
            iso_to_name = names_df.set_index('ISO')['Country'].to_dict()
    except Exception as e:
        print(f"Error loading country names: {e}")

    df['CountryName'] = df['ISO'].map(iso_to_name).fillna(df['ISO'])

    # Load CAS data
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

def get_metadata_es():
    return {
        'pillars': {
            'A': 'Capacidad y Seguridad Sanitaria (Pilar A)',
            'B': 'Esfuerzos Nacionales y Sistema de Salud (Pilar B)',
            'C': 'Cooperación Internacional (Pilar C)',
            'D': 'Poder Estructural y Liderazgo (Pilar D)'
        },
        'indices': {
            'GHEI': 'Índice GHEI (Bruto)',
            'GHEI_adj': 'GHEI Ajustado (Residuo de Poder Estructural)',
            'GHEI_raw': 'GHEI antes de ajustes'
        },
        'descriptions': {
            'GHEI': 'Mide la contribución global a la salud basada en 4 pilares.',
            'GHEI_adj': 'Ajusta el GHEI eliminando la influencia del poder estructural (PIB/WPI), resaltando el "sobre-esfuerzo".',
            'NoExclusion': 'Penalización aplicada a países con políticas de salud excluyentes.'
        }
    }
