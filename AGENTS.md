# GHEI Interactive Dashboard

This dashboard is designed to explore the Global Health Engagement Index (GHEI) outputs.

## Running Locally
1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `python dashboard.py`
3. Open `http://localhost:8050`

## Deployment
Ready for deployment on Railway or similar platforms using the provided `Procfile` and `requirements.txt`.
The main entry point for WSGI is `dashboard:server`.

## Data
The dashboard consumes:
- `final_panel.csv`: Main index results.
- `panel_cas.csv`: CAS/SHAP values.
- `sensitivity_topk.csv`: Sensitivity analysis.
- `D_WPI_Long_format.csv`: Country name mapping and WPI values.
