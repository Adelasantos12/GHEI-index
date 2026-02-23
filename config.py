import os

PROJECT_ROOT = "."
DATA_DIR = PROJECT_ROOT
LOG_DIR = PROJECT_ROOT
OUTPUT_DIR = PROJECT_ROOT
DOCS_DIR = PROJECT_ROOT

# Required filenames as per normative contract
FILES = {
    "notion": os.path.join(PROJECT_ROOT, "Notion.xlsx"),
    "A_e_SPAR": os.path.join(DATA_DIR, "A_e-SPAR.xlsx"),
    "A_GHSIndex": os.path.join(DATA_DIR, "A_GHSIndex.csv"),
    "B_DisasterRisk": os.path.join(DATA_DIR, "B_DisasterRisk.csv"),
    "B_efforts": os.path.join(DATA_DIR, "B_efforts.xlsx"),
    "B_HealthExpenditure": os.path.join(DATA_DIR, "B_HealthExpenditure_percentageGDP.csv"),
    "B_HealthPolicy": os.path.join(DATA_DIR, "B_HealthPolicy.csv"),
    "B_NationalPlan": os.path.join(DATA_DIR, "B_NationalPlan.csv"),
    "B_NationalStrategy": os.path.join(DATA_DIR, "B_NationalStrategy.csv"),
    "B_recognition": os.path.join(DATA_DIR, "B_recognition.csv"),
    "B_UHCIndex": os.path.join(DATA_DIR, "B_UHCIndex.csv"),
    "C_Exclusiones": os.path.join(DATA_DIR, "C_Exclusiones.xlsx"),
    "C_participation": os.path.join(DATA_DIR, "C_participation_clean.csv"),
    "D_WPI": os.path.join(DATA_DIR, "D_WPI_Long_format.csv"),
}
