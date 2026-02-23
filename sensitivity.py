import numpy as np
import pandas as pd
from config import OUTPUT_DIR
from utils import log
import os

os.makedirs(OUTPUT_DIR, exist_ok=True)


def monte_carlo(panel: pd.DataFrame, n_iter=200, top_k=10):
    ranks = []
    ISOs = panel['ISO'].values
    for i in range(n_iter):
        # Random weights for pillars
        w = np.random.dirichlet(np.ones(4))
        A = panel['pillar_A_eq'].values
        B = panel['pillar_B_eq'].values
        C = panel['pillar_C_eq'].values
        D = panel['pillar_D_eq_adj'].values if 'pillar_D_eq_adj' in panel.columns else panel['pillar_D_eq'].values
        ghei_raw = np.power((A ** w[0]) * (B ** w[1]) * (C ** w[2]) * (D ** w[3]), 1/np.sum(w))
        # penalty lambda
        lam = np.random.uniform(0.5, 1.5)
        ghei = ghei_raw * np.power(panel['NoExclusion_mm_global'].fillna(1.0).values, lam)
        # Different normalization choice randomly
        if np.random.rand() < 0.5:
            ghei = (ghei - ghei.min()) / (ghei.max() - ghei.min()) if ghei.max() != ghei.min() else ghei*0
        order = np.argsort(-ghei)
        ranks.append(ISOs[order])
    ranks = np.array(ranks)
    # Compute top-k probability
    probs = {}
    for iso in np.unique(ISOs):
        probs[iso] = np.mean([iso in r[:top_k] for r in ranks])
    out = pd.DataFrame({"ISO": list(probs.keys()), "prob_top_k": list(probs.values())})
    out.to_csv(os.path.join(OUTPUT_DIR, "sensitivity_topk.csv"), index=False)
    log("Monte Carlo sensitivity completed.", "pipeline.log")
    return out
