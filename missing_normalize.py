import pandas as pd
import numpy as np
from .utils import log, minmax_scale
from .config import OUTPUT_DIR
import os

os.makedirs(OUTPUT_DIR, exist_ok=True)

PILLAR_COMPONENTS = {
    'A': ['e_spar','ghs_index'],
    'B': ['hexp_gdp','disaster_risk','efforts_A','uhc_index'],
    'C': ['health_policy','national_plan','national_strategy','recognition'],
    'D': ['participation_event_it','decision_event_it','leadership_event_it','admin_event_it','role_type_it'],
}

ORDINALS = set(['health_policy','national_plan','national_strategy','recognition','role_type_it'])


def handle_missing(panel: pd.DataFrame):
    # Temporal interpolation for quantitative series only (within-country)
    qseries = [c for c in panel.columns if c in (set(PILLAR_COMPONENTS['A']) | set(PILLAR_COMPONENTS['B']) | set(PILLAR_COMPONENTS['D'])) and c not in ORDINALS]
    panel = panel.sort_values(['ISO','year'])
    for col in qseries:
        panel[col] = panel.groupby('ISO')[col].transform(lambda s: s.interpolate(method='linear', limit_direction='both'))
        panel[f'{col}_flag'] = np.where(panel[f'{col}_flag'] == 'missing', 'imputed', panel[f'{col}_flag'])
    # Event carried-forward flags already effectively handled in step function
    for col in ['health_policy','national_plan','national_strategy']:
        panel[f'{col}_flag'] = np.where(panel[col].notna(), 'carried_forward', panel[f'{col}_flag'])
    return panel


def normalize(panel: pd.DataFrame):
    # Orientation: higher is better. DisasterRisk is in [0,1] with higher worse; flip if needed
    if 'disaster_risk' in panel.columns:
        panel['disaster_risk_oriented'] = 1 - panel['disaster_risk']
    else:
        panel['disaster_risk_oriented'] = np.nan
    # NoExclusion already 1 good

    # Global min-max
    for col in ['e_spar','ghs_index','hexp_gdp','efforts_A','efforts_B','uhc_index','health_policy','national_plan','national_strategy','recognition',
                'participation_event_it','decision_event_it','leadership_event_it','admin_event_it','role_type_it','disaster_risk_oriented','NoExclusion']:
        if col in panel.columns:
            panel[f'{col}_mm_global'] = minmax_scale(panel[col])
    # Year min-max
    for col in ['e_spar','ghs_index','hexp_gdp','efforts_A','efforts_B','uhc_index','health_policy','national_plan','national_strategy','recognition',
                'participation_event_it','decision_event_it','leadership_event_it','admin_event_it','role_type_it','disaster_risk_oriented']:
        if col in panel.columns:
            panel[f'{col}_mm_year'] = minmax_scale(panel[col], by_year=panel['year'])
    log("Normalization completed (global and per-year).", "pipeline.log")
    panel.to_csv(os.path.join(OUTPUT_DIR, "panel_normalized.csv"), index=False)
    return panel
