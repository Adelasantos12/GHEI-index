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
            'D': 'Liderazgo y Participación (Pilar D)'
        },
        'pillar_desc': {
            'A': 'Evalúa las capacidades básicas de detección, respuesta y seguridad sanitaria según estándares internacionales (SPAR/GHS). Representa la infraestructura técnica mínima.',
            'B': 'Mide la inversión nacional en salud, preparación ante desastres y cobertura universal. Refleja el compromiso interno con la resiliencia sistémica.',
            'C': 'Analiza la adopción de políticas globales, estrategias nacionales y reconocimiento de normas internacionales. Muestra la alineación con la gobernanza global.',
            'D': 'Cuantifica la presencia y roles de liderazgo en asambleas y organismos de la OMS. Representa la agencia política en el sistema internacional.'
        },
        'indices': {
            'GHEI': 'Índice GHEI (Absoluto)',
            'GHEI_adj': 'GHEI Ajustado (Esfuerzo Relativo)',
            'GHEI_raw': 'GHEI sin penalizaciones'
        },
        'descriptions': {
            'GHEI': 'Contribución total observada al sistema de salud global.',
            'GHEI_adj': 'Contribución relativa que descuenta la ventaja del poder económico (WPI). Identifica países que "superan su peso".',
            'NoExclusion': 'Garantía de acceso no discriminatorio a servicios de salud. Su ausencia penaliza el liderazgo internacional.'
        },
        'indicators': {
            'e_spar_mm_global': 'Capacidad SPAR (Autoevaluación OMS)',
            'ghs_index_mm_global': 'Índice Global Health Security',
            'hexp_gdp_mm_global': 'Gasto en Salud (% PIB)',
            'uhc_index_mm_global': 'Índice de Cobertura Universal (UHC)',
            'health_policy_mm_global': 'Políticas de Salud Internacional',
            'national_plan_mm_global': 'Planes Nacionales de Salud',
            'national_strategy_mm_global': 'Estrategias Sanitarias Nacionales',
            'recognition_mm_global': 'Reconocimiento de Normas Int.',
            'participation_event_it_mm_global': 'Frecuencia de Participación (Presencia)',
            'leadership_event_it_mm_global': 'Roles de Liderazgo (Agencia)',
            'decision_event_it_mm_global': 'Roles de Decisión',
            'admin_event_it_mm_global': 'Roles Administrativos',
            'role_type_it_mm_global': 'Diversidad de Roles',
            'disaster_risk_oriented_mm_global': 'Gestión de Riesgo de Desastres',
            'NoExclusion_mm_global': 'Índice de No Exclusión'
        }
    }
