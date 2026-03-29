import pandas as pd
from src.ingest_validate import validate
from src.panel_build import build_panel
from src.missing_normalize import handle_missing, normalize
from src.index_model import pillar_scores, final_index, wpi_adjust
from src.cas_module import model_pillarD, lagged_dynamics, dependency_network
from src.sensitivity import monte_carlo
from src.report import make_codebook, export_final
from src.config import OUTPUT_DIR
import os


def run():
    data = validate()
    panel = build_panel(data)
    panel = handle_missing(panel)
    panel = normalize(panel)
    panel = pillar_scores(panel, norm_suffix='_mm_global', efforts_variant='A')
    panel = final_index(panel, pillar_variant='eq', lambda_penalty=1.0)
    panel = wpi_adjust(panel)
    panel = model_pillarD(panel)
    panel = lagged_dynamics(panel)
    panel = dependency_network(panel)
    monte_carlo(panel, n_iter=200, top_k=10)
    make_codebook()
    export_final(panel)
    print(f"Pipeline completed. Outputs in {OUTPUT_DIR}")


if __name__ == "__main__":
    run()
