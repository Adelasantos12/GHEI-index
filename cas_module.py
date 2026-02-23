import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score
import shap
from utils import log
from config import OUTPUT_DIR
import os

os.makedirs(OUTPUT_DIR, exist_ok=True)


def model_pillarD(panel: pd.DataFrame):
    # Nonlinear model explaining Pillar D with A, B, C (+ WPI if available)
    cols = ['pillar_A_eq','pillar_B_eq','pillar_C_eq']
    if 'D_WPI' in panel.columns:
        cols.append('D_WPI')
    X = panel[cols].fillna(0)
    y = panel['pillar_D_eq'].fillna(0)
    model = GradientBoostingRegressor(random_state=42)
    model.fit(X, y)
    preds = model.predict(X)
    panel['pillarD_pred'] = preds
    panel['pillarD_resid'] = y - preds
    # SHAP
    explainer = shap.Explainer(model, X)
    shap_values = explainer(X)
    # Save mean |SHAP|
    mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
    for i, c in enumerate(cols):
        panel[f'SHAP_{c}'] = mean_abs_shap[i]
    log("CAS SHAP computed for Pillar D.", "pipeline.log")
    panel.to_csv(os.path.join(OUTPUT_DIR, "panel_cas.csv"), index=False)
    return panel


def lagged_dynamics(panel: pd.DataFrame):
    # Models with lags: B_{t-1} -> A_t ; C_{t-1} -> B_t ; A_{t-1} -> D_t
    panel = panel.sort_values(['ISO','year'])
    panel['A_lag'] = panel.groupby('ISO')['pillar_A_eq'].shift(1)
    panel['B_lag'] = panel.groupby('ISO')['pillar_B_eq'].shift(1)
    panel['C_lag'] = panel.groupby('ISO')['pillar_C_eq'].shift(1)
    panel['D_lag'] = panel.groupby('ISO')['pillar_D_eq'].shift(1)

    def fit_resid(ycol, xcol):
        df = panel.dropna(subset=[ycol, xcol])
        if df.empty:
            return None
        from sklearn.linear_model import LinearRegression
        m = LinearRegression().fit(df[[xcol]], df[ycol])
        panel.loc[df.index, f'{ycol}_pred'] = m.predict(df[[xcol]])
        panel.loc[df.index, f'{ycol}_resid'] = df[ycol] - panel.loc[df.index, f'{ycol}_pred']
        return m

    fit_resid('pillar_A_eq', 'B_lag')
    fit_resid('pillar_B_eq', 'C_lag')
    fit_resid('pillar_D_eq', 'A_lag')

    log("Lagged dynamics modeled.", "pipeline.log")
    panel.to_csv(os.path.join(OUTPUT_DIR, "panel_cas_lag.csv"), index=False)
    return panel


def dependency_network(panel: pd.DataFrame):
    # Partial correlations via precision matrix approximation
    cols = ['pillar_A_eq','pillar_B_eq','pillar_C_eq','pillar_D_eq']
    df = panel[cols].dropna()
    if df.empty:
        return panel
    cov = np.cov(df.values, rowvar=False)
    try:
        prec = np.linalg.inv(cov)
        # Partial corr between i and j
        p_corr = np.zeros_like(cov)
        for i in range(len(cols)):
            for j in range(len(cols)):
                if i == j:
                    p_corr[i, j] = 1
                else:
                    p_corr[i, j] = -prec[i, j] / np.sqrt(prec[i, i] * prec[j, j])
        # Store mean abs partial corr per link
        for i in range(len(cols)):
            for j in range(i+1, len(cols)):
                panel[f'pcorr_{cols[i]}_{cols[j]}'] = p_corr[i, j]
        log("Dependency network computed.", "pipeline.log")
    except Exception as e:
        log(f"Dependency network failed: {e}", "pipeline.log")
    panel.to_csv(os.path.join(OUTPUT_DIR, "panel_cas_dep.csv"), index=False)
    return panel
