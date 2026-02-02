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

def get_metadata_en():
    return {
        'pillars': {
            'A': 'Health Capacity (Pillar A)',
            'B': 'Effort and Resilience (Pillar B)',
            'C': 'Political–Legal Commitment (Pillar C)',
            'D': 'WHO Governance Engagement (Pillar D)'
        },
        'pillar_desc': {
            'A': 'Implemented preparedness and compliance (e-SPAR overall score; GHS Index overall score). Represents the minimum technical infrastructure.',
            'B': 'Sustained material commitment (health expenditure % GDP, disaster risk reduction implementation, UHC coverage). Reflects internal commitment to systemic resilience.',
            'C': 'Domestic institutionalisation of health norms (health policies, plans, strategies, and formal recognition of the right to health).',
            'D': 'Effective participation in global health governance (participation frequency, decision-making roles, and leadership positions within WHO governing bodies).'
        },
        'indices': {
            'GHEI': 'GHEI Index (Absolute)',
            'GHEI_adj': 'Adjusted GHEI (Relative Effort)',
            'GHEI_raw': 'GHEI without penalties'
        },
        'descriptions': {
            'GHEI': 'Total observed contribution to the global health system.',
            'GHEI_adj': 'Relative contribution that discounts the advantage of economic power (WPI). Identifies countries that "punch above their weight".',
            'NoExclusion': 'Guarantee of non-discriminatory access to health services. Its absence penalises international leadership.'
        },
        'indicators': {
            'e_spar_mm_global': 'SPAR Capacity (WHO Self-Assessment)',
            'ghs_index_mm_global': 'Global Health Security Index',
            'hexp_gdp_mm_global': 'Health Expenditure (% of GDP)',
            'uhc_index_mm_global': 'Universal Health Coverage (UHC) Index',
            'health_policy_mm_global': 'International Health Policies',
            'national_plan_mm_global': 'National Health Plans',
            'national_strategy_mm_global': 'National Health Strategies',
            'recognition_mm_global': 'Recognition of Int. Norms',
            'participation_event_it_mm_global': 'Participation Frequency (Presence)',
            'leadership_event_it_mm_global': 'Leadership Roles (Agency)',
            'decision_event_it_mm_global': 'Decision-making Roles',
            'admin_event_it_mm_global': 'Administrative Roles',
            'role_type_it_mm_global': 'Diversity of Roles',
            'disaster_risk_oriented_mm_global': 'Disaster Risk Management',
            'NoExclusion_mm_global': 'No-Exclusion Index'
        }
    }
