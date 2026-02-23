import pandas as pd
import os
from config import OUTPUT_DIR, DOCS_DIR
from utils import log

os.makedirs(DOCS_DIR, exist_ok=True)


def make_codebook():
    content = """Codebook and methodology
    - Variables, pillars, normalization strategies, aggregation formulas.
    - All transformations follow the Notion.xlsx schema.
    - Flags: observed, imputed, carried_forward, missing.
    - Final outputs: panel_normalized.csv, panel_index.csv, panel_index_adj.csv, sensitivity_topk.csv.
    """
    with open(os.path.join(DOCS_DIR, "codebook.md"), "w", encoding="utf-8") as f:
        f.write(content)
    log("Codebook generated.", "pipeline.log")


def export_final(panel: pd.DataFrame):
    cols = ['ISO','year','NoExclusion']
    # normalized variables
    norm_cols = [c for c in panel.columns if c.endswith('_mm_global') or c.endswith('_mm_year')]
    pillars = [c for c in panel.columns if c.startswith('pillar_')]
    finals = ['GHEI','GHEI_raw','GHEI_adj','GHEI_arith']
    flags = [c for c in panel.columns if c.endswith('_flag')]
    out = panel[cols + norm_cols + pillars + finals + flags]
    out.to_csv(os.path.join(OUTPUT_DIR, "final_panel.csv"), index=False)
    log("Final dataset exported.", "pipeline.log")
