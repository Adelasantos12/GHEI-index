import pandas as pd
import numpy as np
import os

from .config import LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)

class ValidationError(Exception):
    pass

def log(msg: str, fname: str = "pipeline.log"):
    path = os.path.join(LOG_DIR, fname)
    with open(path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def minmax_scale(series, by_year=None):
    if by_year is None:
        v = series.astype(float)
        return (v - v.min()) / (v.max() - v.min()) if v.max() != v.min() else v * 0
    else:
        def scale_grp(g):
            v = g.astype(float)
            return (v - v.min()) / (v.max() - v.min()) if v.max() != v.min() else v * 0
        return series.groupby(by_year).transform(scale_grp)


def entropy_weights(df: pd.DataFrame):
    # Columns are indicators (already normalized to [0,1])
    X = df.replace([np.inf, -np.inf], np.nan).fillna(0).clip(0, 1)
    # Compute information entropy per indicator
    eps = 1e-9
    # Normalize per indicator to sum to 1 across observations
    P = X / (X.sum(axis=0) + eps)
    E = -np.log(X.shape[0] + eps) * (P * np.log(P + eps)).sum(axis=0)
    d = 1 - E / (np.log(X.shape[0] + eps))
    w = d / (d.sum() + eps)
    return w


def pca_weights(df: pd.DataFrame, n_components=1):
    from sklearn.decomposition import PCA
    X = df.replace([np.inf, -np.inf], np.nan).fillna(0)
    pca = PCA(n_components=n_components)
    pca.fit(X)
    # Use absolute loadings of first component as weights
    loadings = np.abs(pca.components_[0])
    w = loadings / loadings.sum()
    return w


def corr_elimination(df: pd.DataFrame, threshold=0.9):
    corr = df.corr().abs()
    to_drop = set()
    for i in range(len(corr.columns)):
        for j in range(i):
            if corr.iloc[i, j] > threshold:
                to_drop.add(corr.columns[i])
    return list(to_drop)
