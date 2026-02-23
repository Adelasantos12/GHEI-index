import pandas as pd
import numpy as np
from utils import log, entropy_weights, pca_weights, corr_elimination
from config import OUTPUT_DIR
import os

os.makedirs(OUTPUT_DIR, exist_ok=True)


# Minimum component presence per pillar (50% rule)
MIN_PRESENT = {
    'A': 1,  # 2 components -> need at least 1
    'B': 2,  # 4 components -> need at least 2
    'C': 2,  # 4 components -> need at least 2
    'D': 3,  # 5 components -> need at least 3
}


def pillar_scores(panel: pd.DataFrame, norm_suffix='_mm_global', efforts_variant='A'):
    # Build dataframe of normalized components
    A = panel[[f'e_spar{norm_suffix}', f'ghs_index{norm_suffix}']]
    if efforts_variant == 'A':
        eff = f'efforts_A{norm_suffix}'
    else:
        eff = f'efforts_B{norm_suffix}'
    B = panel[[f'hexp_gdp{norm_suffix}', f'disaster_risk_oriented{norm_suffix}', eff, f'uhc_index{norm_suffix}']]
    C = panel[[f'health_policy{norm_suffix}', f'national_plan{norm_suffix}', f'national_strategy{norm_suffix}', f'recognition{norm_suffix}']]
    D = panel[[f'participation_event_it{norm_suffix}', f'decision_event_it{norm_suffix}', f'leadership_event_it{norm_suffix}', f'admin_event_it{norm_suffix}', f'role_type_it{norm_suffix}']]



    # Equal weights baseline
    # Equal weights baseline (apply 50% presence rule)
    A_present = A.notna().sum(axis=1)
    B_present = B.notna().sum(axis=1)
    C_present = C.notna().sum(axis=1)
    D_present = D.notna().sum(axis=1)
    panel['pillar_A_eq'] = A.mean(axis=1)
    panel.loc[A_present < MIN_PRESENT['A'], 'pillar_A_eq'] = np.nan
    panel['pillar_B_eq'] = B.mean(axis=1)
    panel.loc[B_present < MIN_PRESENT['B'], 'pillar_B_eq'] = np.nan
    panel['pillar_C_eq'] = C.mean(axis=1)
    panel.loc[C_present < MIN_PRESENT['C'], 'pillar_C_eq'] = np.nan
    panel['pillar_D_eq'] = D.mean(axis=1)
    panel.loc[D_present < MIN_PRESENT['D'], 'pillar_D_eq'] = np.nan

    # PCA weights
    try:
        wA = pca_weights(A)
        wB = pca_weights(B)
        wC = pca_weights(C)
        wD = pca_weights(D)
    except Exception:
        wA = np.repeat(1/len(A.columns), len(A.columns))
        wB = np.repeat(1/len(B.columns), len(B.columns))
        wC = np.repeat(1/len(C.columns), len(C.columns))
        wD = np.repeat(1/len(D.columns), len(D.columns))
    panel['pillar_A_pca'] = (A * wA).sum(axis=1)
    panel['pillar_B_pca'] = (B * wB).sum(axis=1)
    panel['pillar_C_pca'] = (C * wC).sum(axis=1)
    panel['pillar_D_pca'] = (D * wD).sum(axis=1)

    # Entropy weights
    wA_e = entropy_weights(A)
    wB_e = entropy_weights(B)
    wC_e = entropy_weights(C)
    wD_e = entropy_weights(D)
    panel['pillar_A_ent'] = (A * wA_e.values).sum(axis=1)
    panel['pillar_B_ent'] = (B * wB_e.values).sum(axis=1)
    panel['pillar_C_ent'] = (C * wC_e.values).sum(axis=1)
    panel['pillar_D_ent'] = (D * wD_e.values).sum(axis=1)

    # Correlation elimination report
    dropA = corr_elimination(A)
    dropB = corr_elimination(B)
    dropC = corr_elimination(C)
    dropD = corr_elimination(D)
    log(f"Correlation-based elimination A:{dropA} B:{dropB} C:{dropC} D:{dropD}", "pipeline.log")

    # Choose equal weights pillars for main index
    panel['pillar_D_eq_adj'] = panel['pillar_D_eq'] * panel['NoExclusion_mm_global'].fillna(1)
    return panel


def final_index(panel: pd.DataFrame, pillar_variant='eq', lambda_penalty=1.0):
    # Geometric aggregation of pillars
    A = panel[f'pillar_A_{pillar_variant}']
    B = panel[f'pillar_B_{pillar_variant}']
    C = panel[f'pillar_C_{pillar_variant}']
    D = panel[f'pillar_D_{pillar_variant}']
    # Adjust D by NoExclusion (already done for eq as pillar_D_eq_adj)
    if pillar_variant == 'eq':
        D = panel['pillar_D_eq_adj']
    weights = np.array([1.0, 1.0, 1.0, 1.0])
    ghei_raw = np.power((A ** weights[0]) * (B ** weights[1]) * (C ** weights[2]) * (D ** weights[3]), 1/weights.sum())
    # Penalize entire index by NoExclusion^lambda
    ghei = ghei_raw * np.power(panel['NoExclusion_mm_global'].fillna(1.0), lambda_penalty)
    panel['GHEI_raw'] = ghei_raw
    panel['GHEI'] = ghei

    # --- Robustness: Arithmetic Aggregation ---
    panel['GHEI_arith'] = (A + B + C + D) / 4.0

    # Calculate Spearman correlation
    rho_global = panel[['GHEI_raw', 'GHEI_arith']].corr(method='spearman').iloc[0, 1]

    # By year
    rhos = {}
    for y, g in panel.groupby('year'):
        if len(g) > 1:
            rhos[int(y)] = g[['GHEI_raw', 'GHEI_arith']].corr(method='spearman').iloc[0, 1]

    latest_year = int(panel['year'].max())
    latest_df = panel[panel['year'] == latest_year]

    # Robustness Exports
    import json

    summary = {
        'rho_global': rho_global,
        'rho_by_year': rhos,
        'latest_year': latest_year,
        'top_raw': latest_df.nlargest(10, 'GHEI_raw')[['ISO', 'GHEI_raw']].to_dict(orient='records'),
        'bottom_raw': latest_df.nsmallest(10, 'GHEI_raw')[['ISO', 'GHEI_raw']].to_dict(orient='records'),
        'top_arith': latest_df.nlargest(10, 'GHEI_arith')[['ISO', 'GHEI_arith']].to_dict(orient='records'),
        'bottom_arith': latest_df.nsmallest(10, 'GHEI_arith')[['ISO', 'GHEI_arith']].to_dict(orient='records')
    }

    with open(os.path.join(OUTPUT_DIR, "robustness_summary.json"), "w") as f:
        json.dump(summary, f, indent=4)

    panel[['ISO', 'year', 'GHEI_raw', 'GHEI_arith']].to_csv(os.path.join(OUTPUT_DIR, "robustness_aggregation.csv"), index=False)

    log("Final index computed.", "pipeline.log")
    panel.to_csv(os.path.join(OUTPUT_DIR, "panel_index.csv"), index=False)
    return panel


def wpi_adjust(panel: pd.DataFrame):
    # WPI residualization with robust handling and fallback to normalized GHEI
    from sklearn.linear_model import LinearRegression
    # choose X column
    if 'WPI' in panel.columns:
        xcol = 'WPI'
    elif 'wpi_val' in panel.columns:
        xcol = 'wpi_val'
    else:
        g = panel['GHEI']
        panel['GHEI_adj'] = (g - g.min()) / (g.max() - g.min()) if g.max() != g.min() else g*0
        log("WPI not available; GHEI_adj set to normalized GHEI.", "pipeline.log")
        panel.to_csv(os.path.join(OUTPUT_DIR, "panel_index_adj.csv"), index=False)
        return panel
    # drop rows with missing inputs
    df2 = panel.dropna(subset=['GHEI', xcol]).copy()
    if df2.empty or df2[xcol].nunique() < 2:
        g = panel['GHEI']
        panel['GHEI_adj'] = (g - g.min()) / (g.max() - g.min()) if g.max() != g.min() else g*0
        log("Insufficient data for WPI adjustment; fallback to normalized GHEI.", "pipeline.log")
        panel.to_csv(os.path.join(OUTPUT_DIR, "panel_index_adj.csv"), index=False)
        return panel
    X = df2[[xcol]]
    y = df2['GHEI']
    model = LinearRegression()
    try:
        model.fit(X, y)
        resid = y - model.predict(X)
        # rescale to [0,1]
        rmin, rmax = resid.min(), resid.max()
        ghei_adj = (resid - rmin) / (rmax - rmin) if rmax != rmin else resid*0
        # initialize and assign
        panel['GHEI_adj'] = np.nan
        panel.loc[df2.index, 'GHEI_adj'] = ghei_adj
        # fill remaining with normalized GHEI
        g = panel['GHEI']
        norm_g = (g - g.min()) / (g.max() - g.min()) if g.max() != g.min() else g*0
        panel['GHEI_adj'] = panel['GHEI_adj'].fillna(norm_g)
        log("GHEI adjusted by WPI residualization (with fallback fill).", "pipeline.log")
    except Exception as e:
        g = panel['GHEI']
        panel['GHEI_adj'] = (g - g.min()) / (g.max() - g.min()) if g.max() != g.min() else g*0
        log(f"WPI adjustment failed: {e}; fallback to normalized GHEI.", "pipeline.log")
    panel.to_csv(os.path.join(OUTPUT_DIR, "panel_index_adj.csv"), index=False)
    return panel
