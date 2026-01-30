import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dashboard_data import load_dashboard_data, get_pillar_cols, get_metadata

# Initialize data
data = load_dashboard_data()
df = data['main']
df_cas = data['cas']
df_topk = data['topk']
metadata = get_metadata()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # For Gunicorn

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Global Health Engagement Index (GHEI)", className="text-center mt-4"), width=12),
        dbc.Col(html.P("Interactive Analytics Dashboard for Global Health Contributions", className="text-center mb-4"), width=12)
    ]),

    dbc.Row([
        # Sidebar Filters
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Global Filters"),
                dbc.CardBody([
                    html.Label("Select Countries:"),
                    dcc.Dropdown(
                        id='country-selector',
                        options=[{'label': row['CountryName'], 'value': row['ISO']} for _, row in df[['ISO', 'CountryName']].drop_duplicates().sort_values('CountryName').iterrows()],
                        value=['USA', 'GBR', 'FRA'],
                        multi=True
                    ),
                    html.Br(),
                    html.Label("Select Year:"),
                    dcc.Dropdown(
                        id='year-selector',
                        options=[{'label': str(y), 'value': y} for y in sorted(df['year'].unique(), reverse=True)],
                        value=df['year'].max()
                    ),
                    html.Br(),
                    html.Label("Pillar Variant:"),
                    dbc.RadioItems(
                        id='variant-selector',
                        options=[
                            {'label': 'Equal Weights (Baseline)', 'value': 'eq'},
                            {'label': 'PCA Weights', 'value': 'pca'},
                            {'label': 'Entropy Weights', 'value': 'ent'}
                        ],
                        value='eq'
                    )
                ])
            ], className="mb-4"),

            dbc.Card([
                dbc.CardHeader("Export"),
                dbc.CardBody([
                    dbc.Button("Download CSV Data", id="btn-csv", color="primary", className="w-100"),
                    dcc.Download(id="download-dataframe-csv"),
                ])
            ]),

            html.Div(id='mini-glossary', className="mt-4 small text-muted", children=[
                html.P([html.B("GHEI:"), " Raw index value."]),
                html.P([html.B("GHEI_adj:"), " Index adjusted by structural power (WPI) residuals."]),
                html.P([html.B("NoExclusion:"), " Penalty for exclusionary health practices."])
            ])
        ], width=3),

        # Main Tabs
        dbc.Col([
            dbc.Tabs([
                # Tab 1: Temporal
                dbc.Tab(label="Temporal Exploration", children=[
                    html.Div([
                        html.H4("Temporal Evolution of GHEI and Pillars", className="mt-4"),
                        dcc.Graph(id='line-ghei-evolution'),
                        dcc.Graph(id='line-pillar-evolution')
                    ])
                ]),

                # Tab 2: Cross-sectional
                dbc.Tab(label="Cross-sectional Comparison", children=[
                    html.Div([
                        html.H4("Cross-sectional Rankings and Distributions", className="mt-4"),
                        dbc.Row([
                            dbc.Col(dcc.Graph(id='bar-ranking'), width=8),
                            dbc.Col(dcc.Graph(id='violin-distribution'), width=4)
                        ]),
                        html.H5("Top-K Probability (Sensitivity)", className="mt-4"),
                        dcc.Graph(id='bar-topk')
                    ])
                ]),

                # Tab 3: Structural Diagnosis
                dbc.Tab(label="Structural Diagnosis", children=[
                    html.Div([
                        html.H4("Structural Diagnosis: GHEI vs WPI", className="mt-4"),
                        dbc.Checkbox(id='show-adj-toggle', label="Show Adjusted GHEI?", value=False),
                        dcc.Graph(id='scatter-wpi'),
                        html.H5("Pillar Decomposition (Relative Contribution)", className="mt-4"),
                        dcc.Graph(id='stacked-pillar-contrib')
                    ])
                ]),

                # Tab 4: WHO Engagement (Pillar D)
                dbc.Tab(label="WHO Engagement (Pillar D)", children=[
                    html.Div([
                        html.H4("Pillar D Components & Exclusion Impact", className="mt-4"),
                        dbc.Row([
                            dbc.Col(dcc.Graph(id='bar-pillar-d-components'), width=7),
                            dbc.Col(dcc.Graph(id='scatter-noexclusion'), width=5)
                        ])
                    ])
                ]),

                # Tab 5: CAS Results
                dbc.Tab(label="CAS Results", children=[
                    html.Div([
                        html.H4("Complex Adaptive Systems (CAS) Analytics", className="mt-4"),
                        dbc.Row([
                            dbc.Col(dcc.Graph(id='bar-shap-importance'), width=6),
                            dbc.Col(dcc.Graph(id='heatmap-lags'), width=6)
                        ]),
                        html.H5("Non-linear Dependencies", className="mt-4"),
                        dcc.Graph(id='scatter-dependency')
                    ])
                ]),

                # Tab 6: Traceability
                dbc.Tab(label="Traceability", children=[
                    html.Div([
                        html.H4("Calculation Traceability", className="mt-4"),
                        html.P("Select a single country to see details:"),
                        dcc.Dropdown(id='trace-country', options=[{'label': n, 'value': i} for i, n in data['iso_map'].items()], value='USA'),
                        html.Br(),
                        html.Div(id='trace-table-container')
                    ])
                ])
            ], id="tabs-main")
        ], width=9)
    ])
], fluid=True)

# --- Callbacks ---

@app.callback(
    Output('line-ghei-evolution', 'figure'),
    [Input('country-selector', 'value')]
)
def update_ghei_evolution(countries):
    filtered = df[df['ISO'].isin(countries)]
    fig = px.line(filtered, x='year', y='GHEI', color='CountryName', markers=True,
                 title="Evolution of GHEI")
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('line-pillar-evolution', 'figure'),
    [Input('country-selector', 'value'), Input('variant-selector', 'value')]
)
def update_pillar_evolution(countries, variant):
    cols = get_pillar_cols(variant)
    filtered = df[df['ISO'].isin(countries)]

    # Melt for long format
    melted = filtered.melt(id_vars=['year', 'CountryName'], value_vars=cols,
                          var_name='Pillar', value_name='Score')

    fig = px.line(melted, x='year', y='Score', color='CountryName', line_dash='Pillar',
                 markers=True, title=f"Evolution of Pillars (Variant: {variant})")
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('bar-ranking', 'figure'),
    [Input('year-selector', 'value')]
)
def update_ranking(year):
    filtered = df[df['year'] == year].sort_values('GHEI', ascending=False).head(20)
    fig = px.bar(filtered, x='CountryName', y='GHEI', color='GHEI',
                title=f"Top 20 Countries by GHEI in {year}")
    fig.update_layout(xaxis={'categoryorder':'total descending'}, template='plotly_white')
    return fig

@app.callback(
    Output('violin-distribution', 'figure'),
    [Input('year-selector', 'value'), Input('variant-selector', 'value')]
)
def update_distribution(year, variant):
    cols = get_pillar_cols(variant)
    filtered = df[df['year'] == year]
    melted = filtered.melt(value_vars=cols, var_name='Pillar', value_name='Score')
    fig = px.violin(melted, x='Pillar', y='Score', box=True, points='all',
                   title=f"Pillar Score Distributions ({year})")
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('bar-topk', 'figure'),
    [Input('country-selector', 'value')]
)
def update_topk(countries):
    if df_topk.empty: return go.Figure()
    filtered = df_topk[df_topk['ISO'].isin(countries)]
    # We need country names
    filtered = filtered.copy()
    filtered['CountryName'] = filtered['ISO'].map(data['iso_map'])

    fig = px.bar(filtered, x='CountryName', y='prob_top_k',
                title="Probability of being in Top-K (Sensitivity Analysis)")
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('scatter-wpi', 'figure'),
    [Input('year-selector', 'value'), Input('show-adj-toggle', 'value')]
)
def update_wpi_scatter(year, show_adj):
    filtered = df[df['year'] == year]
    # WPI might be in df if merged, or we might need it from pillar_D (structural)
    # Actually wpi_val is in df_cas
    if 'wpi_val' not in filtered.columns and not df_cas.empty:
        wpi_data = df_cas[df_cas['year'] == year][['ISO', 'wpi_val']]
        filtered = filtered.merge(wpi_data, on='ISO', how='left')

    y_col = 'GHEI_adj' if show_adj else 'GHEI'
    fig = px.scatter(filtered, x='wpi_val', y=y_col, hover_name='CountryName',
                    trendline="ols", title=f"GHEI vs Structural Power (WPI) in {year}")
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('stacked-pillar-contrib', 'figure'),
    [Input('country-selector', 'value'), Input('year-selector', 'value'), Input('variant-selector', 'value')]
)
def update_pillar_contrib(countries, year, variant):
    cols = get_pillar_cols(variant)
    filtered = df[(df['ISO'].isin(countries)) & (df['year'] == year)]

    melted = filtered.melt(id_vars=['CountryName'], value_vars=cols, var_name='Pillar', value_name='Score')

    fig = px.bar(melted, x='CountryName', y='Score', color='Pillar', barmode='stack',
                title=f"Pillar Contribution in {year}")
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('bar-pillar-d-components', 'figure'),
    [Input('country-selector', 'value'), Input('year-selector', 'value')]
)
def update_pillar_d(countries, year):
    # Pillar D components (raw or normalized) from df_cas or df
    comp_cols = ['participation_event_it_mm_global', 'decision_event_it_mm_global',
                 'leadership_event_it_mm_global', 'admin_event_it_mm_global', 'role_type_it_mm_global']

    if df_cas.empty: return go.Figure()

    filtered = df_cas[(df_cas['ISO'].isin(countries)) & (df_cas['year'] == year)]
    melted = filtered.melt(id_vars=['ISO'], value_vars=comp_cols, var_name='Component', value_name='Score')
    melted['CountryName'] = melted['ISO'].map(data['iso_map'])

    fig = px.bar(melted, x='Component', y='Score', color='CountryName', barmode='group',
                title=f"WHO Engagement Components (Pillar D) - {year}")
    fig.update_layout(template='plotly_white', xaxis_tickangle=-45)
    return fig

@app.callback(
    Output('scatter-noexclusion', 'figure'),
    [Input('year-selector', 'value')]
)
def update_exclusion_scatter(year):
    filtered = df[df['year'] == year]
    fig = px.scatter(filtered, x='NoExclusion', y='pillar_D_eq', hover_name='CountryName',
                    title=f"Pillar D vs NoExclusion Penalty ({year})")
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('bar-shap-importance', 'figure'),
    [Input('variant-selector', 'value')]
)
def update_shap(variant):
    # Aggregated SHAP from df_cas
    shap_cols = [f'SHAP_pillar_A_{variant}', f'SHAP_pillar_B_{variant}', f'SHAP_pillar_C_{variant}']
    if df_cas.empty or not all(c in df_cas.columns for c in shap_cols):
        return go.Figure().update_layout(title="SHAP Data not available for this variant")

    mean_shap = df_cas[shap_cols].abs().mean().reset_index()
    mean_shap.columns = ['Pillar', 'Mean_Abs_SHAP']

    fig = px.bar(mean_shap, x='Pillar', y='Mean_Abs_SHAP', title="Feature Importance (Mean |SHAP|)")
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('heatmap-lags', 'figure'),
    [Input('country-selector', 'value')]
)
def update_lags(countries):
    # Use lag columns from df_cas
    lag_cols = ['A_lag', 'B_lag', 'C_lag', 'D_lag']
    if df_cas.empty or not any(c in df_cas.columns for c in lag_cols):
        return go.Figure().update_layout(title="Temporal Lag data not available")

    # Only use columns that exist
    existing_lags = [c for c in lag_cols if c in df_cas.columns]

    filtered = df_cas[df_cas['ISO'].isin(countries)]
    if filtered.empty:
        filtered = df_cas # Fallback to all if none selected

    corr = filtered[existing_lags].corr()
    fig = px.imshow(corr, text_auto=True, title="Temporal Correlation Matrix (Lags)")
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('scatter-dependency', 'figure'),
    [Input('variant-selector', 'value')]
)
def update_dep(variant):
    # Partial dependency plot: GHEI vs Pillars or Residuals
    if df_cas.empty:
        return go.Figure().update_layout(title="Dependency data not available")

    # We can plot Residuals vs Predicted to show non-linearities or just Pillar vs GHEI
    y_col = f'pillar_D_{variant}_resid' if f'pillar_D_{variant}_resid' in df_cas.columns else 'pillarD_resid'
    x_col = 'wpi_val'

    if y_col not in df_cas.columns or x_col not in df_cas.columns:
         return go.Figure().update_layout(title="Residual/WPI data not available for dependency plot")

    fig = px.scatter(df_cas, x=x_col, y=y_col, color='year',
                    trendline="lowess",
                    title=f"Non-linear Effects: {y_col} vs {x_col} (LOWESS)")
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('trace-table-container', 'children'),
    [Input('trace-country', 'value'), Input('year-selector', 'value')]
)
def update_traceability(iso, year):
    row = df[(df['ISO'] == iso) & (df['year'] == year)]
    if row.empty: return "No data for selected country/year"

    # Flags
    flag_cols = [c for c in df.columns if 'flag' in c]
    flags = row[flag_cols].iloc[0].to_dict()

    # Raw vs Normalized
    # We can show a few key variables
    vars_to_show = ['e_spar', 'ghs_index', 'hexp_gdp', 'uhc_index']
    trace_data = []
    for v in vars_to_show:
        norm_v = f"{v}_mm_global"
        raw_v = v # Might be in df_cas
        raw_val = "N/A"
        if not df_cas.empty:
            raw_row = df_cas[(df_cas['ISO'] == iso) & (df_cas['year'] == year)]
            if v in raw_row.columns:
                raw_val = raw_row[v].iloc[0]

        norm_val = row[norm_v].iloc[0] if norm_v in row.columns else "N/A"
        flag_val = flags.get(f"{v}_flag", "N/A")

        trace_data.append({
            "Variable": v,
            "Raw Value": raw_val,
            "Normalized (Global)": norm_val,
            "Status": flag_val
        })

    table = dash_table.DataTable(
        data=trace_data,
        columns=[{"name": i, "id": i} for i in ["Variable", "Raw Value", "Normalized (Global)", "Status"]],
        style_cell={'textAlign': 'left'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
    )

    formula = html.Div([
        html.B("Applied Formula: "),
        html.Code("GHEI = (Pillar_A + Pillar_B + Pillar_C + Pillar_D) / 4"),
        html.Br(),
        html.B("Pillar D (WHO Engagement) is adjusted by NoExclusion penalty.")
    ], className="mt-3 p-3 border rounded bg-light")

    return [table, formula]

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-csv", "n_clicks"),
    prevent_initial_call=True,
)
def download_csv(n_clicks):
    return dcc.send_data_frame(df.to_csv, "ghei_data_export.csv")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
