import os

# Base directory: one level up from src/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Logs and outputs in root
DATA_DIR = PROJECT_ROOT
LOG_DIR = PROJECT_ROOT
OUTPUT_DIR = PROJECT_ROOT
DOCS_DIR = PROJECT_ROOT

# Required filenames - all are in the root in this environment
FILES = {
    "notion": os.path.join(PROJECT_ROOT, "Notion.xlsx"),
    "A_e_SPAR": os.path.join(PROJECT_ROOT, "A_e-SPAR.xlsx"),
    "A_GHSIndex": os.path.join(PROJECT_ROOT, "A_GHSIndex.csv"),
    "B_DisasterRisk": os.path.join(PROJECT_ROOT, "B_DisasterRisk.csv"),
    "B_efforts": os.path.join(PROJECT_ROOT, "B_efforts.xlsx"),
    "B_HealthExpenditure": os.path.join(PROJECT_ROOT, "B_HealthExpenditure_percentageGDP.csv"),
    "B_HealthPolicy": os.path.join(PROJECT_ROOT, "B_HealthPolicy.csv"),
    "B_NationalPlan": os.path.join(PROJECT_ROOT, "B_NationalPlan.csv"),
    "B_NationalStrategy": os.path.join(PROJECT_ROOT, "B_NationalStrategy.csv"),
    "B_recognition": os.path.join(PROJECT_ROOT, "B_recognition.csv"),
    "B_UHCIndex": os.path.join(PROJECT_ROOT, "B_UHCIndex.csv"),
    "C_Exclusiones": os.path.join(PROJECT_ROOT, "C_Exclusiones.xlsx"),
    "C_participation": os.path.join(PROJECT_ROOT, "C_participation_clean.csv"),
    "D_WPI": os.path.join(PROJECT_ROOT, "D_WPI_Long_format.csv"),
}
