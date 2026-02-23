import pandas as pd
import numpy as np
from config import FILES, OUTPUT_DIR
from utils import log
import os

os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_YEARS = list(range(2010, 2024))


def _read(fp):
    if fp.endswith('.xlsx'):
        return pd.read_excel(fp)
    else:
        try:
            return pd.read_csv(fp, encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(fp, encoding="latin-1")


def step_forward(event_df, year_col="year", value_col="value", iso_col="ISO"):
    # Keep latest value forward within TARGET_YEARS; before first observation -> NaN
    df = event_df[[iso_col, year_col, value_col]].copy()
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
    out = []
    for iso, g in df.groupby(iso_col):
        g = g.dropna(subset=[year_col]).sort_values(year_col)
        if g.empty:
            continue
        first_year = g[year_col].min()
        last_val = np.nan
        mapping = {}
        for y in TARGET_YEARS:
            if y < first_year:
                mapping[y] = np.nan
            else:
                # update last_val if a record exists at y
                if y in set(g[year_col]):
                    last_val = g.loc[g[year_col] == y, value_col].iloc[0]
                mapping[y] = last_val
        tmp = pd.DataFrame({"ISO": iso, "year": TARGET_YEARS, value_col: [mapping[y] for y in TARGET_YEARS]})
        out.append(tmp)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["ISO","year",value_col])


def build_panel(data: dict):
    part = _read(FILES['C_participation'])
    # rename columns to standard
    part_cols = {c: c for c in part.columns}
    # standard lower-case
    part.columns = [c.strip() for c in part.columns]
    # Identify ISO, year
    iso_col = 'ISO' if 'ISO' in part.columns else 'iso'
    year_col = 'year' if 'year' in part.columns else 'Year'
    base = part[[iso_col, year_col]].drop_duplicates()
    base = base[(base[year_col] >= 2010) & (base[year_col] <= 2023)]
    base = base.rename(columns={iso_col: 'ISO', year_col: 'year'})

    panel = base.copy()

    # Merge annual variables
    def annual_merge(fp, cols_map):
        df = _read(fp)
        # standardize columns
        if 'year' not in df.columns and 'Year' in df.columns:
            df = df.rename(columns={'Year': 'year'})
        if 'ISO' not in df.columns and 'iso' in df.columns:
            df = df.rename(columns={'iso': 'ISO'})
        # ensure year numeric
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        # drop redundant country labels to avoid duplicate columns in merges
        if 'Country' in df.columns:
            df = df.drop(columns=['Country'])
        # apply indicator renaming
        df = df.rename(columns=cols_map)
        # keep only necessary columns for merge
        ind_col = list(cols_map.values())[0]
        keep_cols = [c for c in ['ISO', 'year', ind_col] if c in df.columns]
        df = df[keep_cols]
        # also drop any existing 'Country' columns in panel before merge
        pmerge = panel.drop(columns=[c for c in panel.columns if c.startswith('Country')], errors='ignore')
        return pmerge.merge(df, on=['ISO','year'], how='left')

    panel = annual_merge(FILES['A_e_SPAR'], {'Promedio_total': 'e_spar'})
    panel = annual_merge(FILES['A_GHSIndex'], {'OVERALL SCORE': 'ghs_index'})
    panel = annual_merge(FILES['B_DisasterRisk'], {'value': 'disaster_risk'})
    panel = annual_merge(FILES['B_HealthExpenditure'], {'value': 'hexp_gdp'})
    panel = annual_merge(FILES['B_UHCIndex'], {'value': 'uhc_index'})
    # WPI
    panel = annual_merge(FILES['D_WPI'], {'value': 'wpi_val'})

    # Event variables step function
    def event_prepare(fp):
        df = _read(fp)
        # standardize columns
        if 'year' not in df.columns and 'Year' in df.columns:
            df = df.rename(columns={'Year':'year'})
        iso = 'ISO' if 'ISO' in df.columns else ('...3' if '...3' in df.columns else 'iso')
        val = 'value' if 'value' in df.columns else 'Value'
        return step_forward(df.rename(columns={iso:'ISO'}), year_col='year', value_col=val, iso_col='ISO')

    hp = event_prepare(FILES['B_HealthPolicy']).rename(columns={'value':'health_policy'})
    np_ = event_prepare(FILES['B_NationalPlan']).rename(columns={'value':'national_plan'})
    ns = event_prepare(FILES['B_NationalStrategy']).rename(columns={'value':'national_strategy'})

    panel = panel.merge(hp, on=['ISO','year'], how='left')
    panel = panel.merge(np_, on=['ISO','year'], how='left')
    panel = panel.merge(ns, on=['ISO','year'], how='left')

    # Recognition has no year; assign step function with implicit year? Treat as constant from recognition year onwards
    rec = _read(FILES['B_recognition'])
    # Try to infer columns
    iso = 'ISO' if 'ISO' in rec.columns else 'iso'
    val = 'value' if 'value' in rec.columns else 'Value'
    # We don't have year in this file; Notion says only year recorded elsewhere; we will treat recognition value as constant for all TARGET_YEARS
    rec_expanded = panel[['ISO','year']].drop_duplicates().merge(rec[[iso, val]].rename(columns={iso:'ISO'}), on='ISO', how='left')
    panel = panel.merge(rec_expanded.rename(columns={val:'recognition'}), on=['ISO','year'], how='left')

    # Participation (pillar D components)
    part_vars = _read(FILES['C_participation']).rename(columns={'country':'Country','ISO':'ISO','year':'year'})
    use_cols = ['ISO','year','participation_event_it','decision_event_it','leadership_event_it','admin_event_it','role_type_it']
    part_vars = part_vars[use_cols]
    # Aggregate participation to unique ISO-year per schema
    part_vars = part_vars.groupby(['ISO','year'], as_index=False).agg({
        'participation_event_it':'sum',
        'decision_event_it':'sum',
        'leadership_event_it':'sum',
        'admin_event_it':'sum',
        'role_type_it':'max'
    })
    panel = panel.merge(part_vars, on=['ISO','year'], how='left')

    # Exclusions
    excl = _read(FILES['C_Exclusiones'])
    # standardize columns
    if 'Year' in excl.columns and 'ISO' in excl.columns and 'Value' in excl.columns:
        excl = excl.rename(columns={'Year':'year','Value':'Exclusion'})
    else:
        # alternative format
        if 'year' not in excl.columns and 'Year' in excl.columns:
            excl = excl.rename(columns={'Year':'year'})
        if 'value' in excl.columns:
            excl = excl.rename(columns={'value':'Exclusion'})
    excl['Exclusion'] = 1  # any record indicates exclusion that year
    panel = panel.merge(excl[['ISO','year','Exclusion']], on=['ISO','year'], how='left')
    panel['Exclusion'] = panel['Exclusion'].fillna(0)
    panel['NoExclusion'] = 1 - panel['Exclusion']

    # Efforts scenarios
    efforts = _read(FILES['B_efforts'])
    iso = 'ISO' if 'ISO' in efforts.columns else 'iso'
    val = 'Value' if 'Value' in efforts.columns else 'value'
    EffA = panel[['ISO','year']].merge(efforts[[iso, val]].rename(columns={iso:'ISO', val:'efforts_A'}), on='ISO', how='left')
    EffB = panel[['ISO','year']].copy()
    EffB['efforts_B'] = np.where(EffB['year'] == 2023,
                                 EffA['efforts_A'],
                                 np.nan)
    panel = panel.merge(EffA[['ISO','year','efforts_A']], on=['ISO','year'], how='left')
    panel = panel.merge(EffB[['ISO','year','efforts_B']], on=['ISO','year'], how='left')

    # Flags initialization
    for col in ['e_spar','ghs_index','disaster_risk','hexp_gdp','uhc_index','health_policy','national_plan','national_strategy','recognition',
                'participation_event_it','decision_event_it','leadership_event_it','admin_event_it','role_type_it','efforts_A','efforts_B']:
        flag_col = f"{col}_flag"
        panel[flag_col] = np.where(panel[col].notna(), 'observed', 'missing')

    log(f"Panel built: {panel.shape} rows", "pipeline.log")
    panel.to_csv(os.path.join(OUTPUT_DIR, "panel_raw.csv"), index=False)
    return panel
