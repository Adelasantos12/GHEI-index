import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dashboard_data import load_dashboard_data, get_pillar_cols, get_metadata_es

# Initialize data
data = load_dashboard_data()
df = data['main']
df_cas = data['cas']
df_topk = data['topk']
meta = get_metadata_es()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
server = app.server

# --- Custom Components ---

def make_header():
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Guía Rápida", href="#")),
        ],
        brand="GHEI Dashboard: Analítica de Salud Global",
        brand_href="#",
        color="primary",
        dark=True,
        className="mb-4"
    )

def make_sidebar():
    return dbc.Card([
        dbc.CardHeader(html.H5("Configuración y Filtros", className="mb-0")),
        dbc.CardBody([
            html.Label("1. Seleccione Países:", className="fw-bold"),
            dcc.Dropdown(
                id='country-selector',
                options=[{'label': row['CountryName'], 'value': row['ISO']} for _, row in df[['ISO', 'CountryName']].drop_duplicates().sort_values('CountryName').iterrows()],
                value=['USA', 'MEX', 'BRA', 'ESP'],
                multi=True,
                placeholder="Buscar país..."
            ),
            html.Small("Puede seleccionar múltiples países para comparar.", className="text-muted"),

            html.Br(), html.Br(),
            html.Label("2. Año de Análisis:", className="fw-bold"),
            dcc.Dropdown(
                id='year-selector',
                options=[{'label': str(y), 'value': y} for y in sorted(df['year'].unique(), reverse=True)],
                value=df['year'].max()
            ),

            html.Br(),
            html.Label("3. Método de Pesaje:", className="fw-bold"),
            dbc.RadioItems(
                id='variant-selector',
                options=[
                    {'label': 'Pesos Iguales (Base)', 'value': 'eq'},
                    {'label': 'Análisis PCA', 'value': 'pca'},
                    {'label': 'Entropía', 'value': 'ent'}
                ],
                value='eq'
            ),
            html.Small("Diferentes formas de calcular la importancia de cada pilar.", className="text-muted"),
        ])
    ], className="shadow-sm")

def make_info_card(title, text):
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, className="card-title fw-bold text-primary"),
            html.P(text, className="card-text small")
        ])
    ], className="mb-2 shadow-sm border-start border-primary border-4")

# --- Layout ---

app.layout = html.Div([
    make_header(),
    dbc.Container([
        dbc.Row([
            # Sidebar
            dbc.Col([
                make_sidebar(),
                html.Div([
                    html.Hr(),
                    html.H6("Conceptos Clave", className="fw-bold"),
                    make_info_card("GHEI Bruto", "Puntaje total basado en el desempeño observado."),
                    make_info_card("GHEI Ajustado", "Puntaje que elimina la ventaja del poder económico (PIB), premiando a quien hace más con menos."),
                    make_info_card("Pilar D", "Participación y liderazgo dentro de la OMS."),
                ], className="mt-4")
            ], width=3),

            # Content
            dbc.Col([
                dbc.Tabs([
                    # Tab 1: Evolución Temporal
                    dbc.Tab(label="📈 Evolución Temporal", tab_id="tab-temporal", children=[
                        html.Div([
                            html.Div([
                                html.H4("¿Cómo ha cambiado el índice con el tiempo?", className="mt-4"),
                                html.P("Este gráfico muestra la trayectoria del GHEI. Un aumento indica una mayor contribución relativa a la salud global."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dcc.Graph(id='line-ghei-evolution'),
                            html.Hr(),
                            html.H5("Desglose por Pilares", className="mt-4"),
                            html.P("Vea cómo evolucionan las cuatro áreas principales (A, B, C, D) para los países seleccionados."),
                            dcc.Graph(id='line-pillar-evolution')
                        ], className="p-3")
                    ]),

                    # Tab 2: Rankings
                    dbc.Tab(label="🏆 Rankings y Comparación", tab_id="tab-rank", children=[
                        html.Div([
                            html.Div([
                                html.H4("¿Quiénes lideran el índice?", className="mt-4"),
                                html.P("Comparación transversal de los 20 países con mayor puntaje en el año seleccionado."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dbc.Row([
                                dbc.Col(dcc.Graph(id='bar-ranking'), width=8),
                                dbc.Col([
                                    html.H5("Distribución de Puntajes"),
                                    html.P("¿Cómo se concentran los países en cada pilar?", className="small"),
                                    dcc.Graph(id='violin-distribution')
                                ], width=4)
                            ]),
                            html.Hr(),
                            html.H5("Sensibilidad (Probabilidad de estar en el Top)"),
                            html.P("Muestra la robustez del ranking: ¿Qué tan probable es que el país sea realmente un líder?", className="small"),
                            dcc.Graph(id='bar-topk')
                        ], className="p-3")
                    ]),

                    # Tab 3: Estructura vs Desempeño
                    dbc.Tab(label="⚖️ Estructura vs Esfuerzo", tab_id="tab-struct", children=[
                        html.Div([
                            html.Div([
                                html.H4("Poder Estructural vs. Contribución Real", className="mt-4"),
                                html.P("¿Contribuyen los países solo porque son ricos? El eje X muestra el poder estructural (WPI) y el eje Y el GHEI."),
                                html.P("Los países arriba de la línea roja están contribuyendo MÁS de lo esperado para su nivel de poder."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dbc.Switch(id='show-adj-toggle', label="Ver GHEI Ajustado (Residuos)", value=False, className="mb-2"),
                            dcc.Graph(id='scatter-wpi'),
                            html.Hr(),
                            html.H5("Composición del Índice (A-D)"),
                            html.P("Muestra cuánto aporta cada pilar al puntaje final del país seleccionado."),
                            dcc.Graph(id='stacked-pillar-contrib')
                        ], className="p-3")
                    ]),

                    # Tab 4: Engagement OMS
                    dbc.Tab(label="🇺🇳 Liderazgo OMS (Pilar D)", tab_id="tab-who", children=[
                        html.Div([
                            html.Div([
                                html.H4("Detalle del Pilar D: Participación en la OMS", className="mt-4"),
                                html.P("Analiza roles de liderazgo, participación en asambleas y cumplimiento de normativas."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Componentes de Participación"),
                                    dcc.Graph(id='bar-pillar-d-components')
                                ], width=7),
                                dbc.Col([
                                    html.H5("Impacto de Exclusión"),
                                    html.P("¿Cómo afecta la penalización por políticas excluyentes al puntaje de liderazgo?", className="small"),
                                    dcc.Graph(id='scatter-noexclusion')
                                ], width=5)
                            ])
                        ], className="p-3")
                    ]),

                    # Tab 5: Analítica Avanzada
                    dbc.Tab(label="🧠 Analítica (CAS)", tab_id="tab-cas", children=[
                        html.Div([
                            html.Div([
                                html.H4("Resultados de Sistemas Adaptativos Complejos", className="mt-4"),
                                html.P("Esta sección analiza relaciones no lineales y la importancia estadística de cada variable."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Importancia de Variables (SHAP)"),
                                    html.P("¿Qué pilares influyen más en el resultado final?", className="small"),
                                    dcc.Graph(id='bar-shap-importance')
                                ], width=6),
                                dbc.Col([
                                    html.H5("Correlaciones Temporales"),
                                    html.P("Relación entre los rezagos históricos de los pilares.", className="small"),
                                    dcc.Graph(id='heatmap-lags')
                                ], width=6)
                            ]),
                            html.Hr(),
                            html.H5("Dependencias No Lineales"),
                            html.P("Muestra cómo cambia el esfuerzo (residuo) a medida que aumenta el poder estructural.", className="small"),
                            dcc.Graph(id='scatter-dependency')
                        ], className="p-3")
                    ]),

                    # Tab 6: Trazabilidad
                    dbc.Tab(label="🔍 Auditoría de Datos", tab_id="tab-trace", children=[
                        html.Div([
                            html.Div([
                                html.H4("Trazabilidad y Transparencia", className="mt-4"),
                                html.P("Consulte los valores originales (crudos) y normalizados para un país específico."),
                            ], className="p-3 bg-light rounded mb-4"),
                            html.Label("Seleccione un país para auditar:", className="fw-bold"),
                            dcc.Dropdown(id='trace-country', options=[{'label': n, 'value': i} for i, n in data['iso_map'].items()], value='MEX'),
                            html.Br(),
                            html.Div(id='trace-table-container'),
                            html.Div([
                                dbc.Button("Descargar Datos Completos (CSV)", id="btn-csv", color="success", className="mt-3"),
                                dcc.Download(id="download-dataframe-csv"),
                            ])
                        ], className="p-3")
                    ])
                ], id="tabs-main", active_tab="tab-temporal")
            ], width=9)
        ])
    ], fluid=True, className="pb-5")
])

# --- Callbacks ---

@app.callback(
    Output('line-ghei-evolution', 'figure'),
    [Input('country-selector', 'value')]
)
def update_ghei_evolution(countries):
    if not countries: return go.Figure().update_layout(title="Seleccione al menos un país")
    filtered = df[df['ISO'].isin(countries)]
    fig = px.line(filtered, x='year', y='GHEI', color='CountryName', markers=True,
                 title="Evolución del Índice GHEI", labels={'year':'Año', 'GHEI':'Puntaje GHEI', 'CountryName':'País'})
    fig.update_layout(template='plotly_white', hovermode='x unified')
    return fig

@app.callback(
    Output('line-pillar-evolution', 'figure'),
    [Input('country-selector', 'value'), Input('variant-selector', 'value')]
)
def update_pillar_evolution(countries, variant):
    if not countries: return go.Figure().update_layout(title="Seleccione al menos un país")
    cols = get_pillar_cols(variant)
    filtered = df[df['ISO'].isin(countries)]

    melted = filtered.melt(id_vars=['year', 'CountryName'], value_vars=cols,
                          var_name='Pillar', value_name='Score')

    # Clean pillar names for legend
    melted['Pillar'] = melted['Pillar'].apply(lambda x: x.split('_')[-2] + " (" + x.split('_')[-1] + ")")

    fig = px.line(melted, x='year', y='Score', color='CountryName', line_dash='Pillar',
                 markers=True, title=f"Evolución de Pilares (Método: {variant})",
                 labels={'year':'Año', 'Score':'Valor', 'CountryName':'País'})
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('bar-ranking', 'figure'),
    [Input('year-selector', 'value')]
)
def update_ranking(year):
    filtered = df[df['year'] == year].sort_values('GHEI', ascending=False).head(20)
    fig = px.bar(filtered, x='CountryName', y='GHEI', color='GHEI',
                title=f"Top 20 Países - Año {year}",
                labels={'GHEI':'Índice GHEI', 'CountryName':'País'},
                color_continuous_scale='Viridis')
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
                   title=f"Distribución {year}", color='Pillar')
    fig.update_layout(template='plotly_white', showlegend=False)
    return fig

@app.callback(
    Output('bar-topk', 'figure'),
    [Input('country-selector', 'value')]
)
def update_topk(countries):
    if df_topk.empty or not countries: return go.Figure().update_layout(title="Sin datos de sensibilidad")
    filtered = df_topk[df_topk['ISO'].isin(countries)].copy()
    filtered['CountryName'] = filtered['ISO'].map(data['iso_map']).fillna(filtered['ISO'])

    fig = px.bar(filtered, x='CountryName', y='prob_top_k',
                title="Robustez: Probabilidad de pertenecer al Top-K",
                labels={'prob_top_k':'Probabilidad', 'CountryName':'País'})
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('scatter-wpi', 'figure'),
    [Input('year-selector', 'value'), Input('show-adj-toggle', 'value')]
)
def update_wpi_scatter(year, show_adj):
    filtered = df[df['year'] == year]

    # Ensure wpi_val is present
    if 'wpi_val' not in filtered.columns and not df_cas.empty:
        wpi_data = df_cas[df_cas['year'] == year][['ISO', 'wpi_val']]
        filtered = filtered.merge(wpi_data, on='ISO', how='left')

    if 'wpi_val' not in filtered.columns:
        return go.Figure().update_layout(title="Datos WPI no disponibles")

    y_col = 'GHEI_adj' if show_adj else 'GHEI'
    fig = px.scatter(filtered, x='wpi_val', y=y_col, hover_name='CountryName',
                    trendline="ols", title=f"GHEI vs Poder Estructural (WPI) - {year}",
                    labels={'wpi_val':'Poder Estructural (WPI)', 'GHEI':'GHEI Bruto', 'GHEI_adj':'GHEI Ajustado (Esfuerzo)'})

    # Add identity line or similar if useful, but trendline is better
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('stacked-pillar-contrib', 'figure'),
    [Input('country-selector', 'value'), Input('year-selector', 'value'), Input('variant-selector', 'value')]
)
def update_pillar_contrib(countries, year, variant):
    if not countries: return go.Figure()
    cols = get_pillar_cols(variant)
    filtered = df[(df['ISO'].isin(countries)) & (df['year'] == year)]

    melted = filtered.melt(id_vars=['CountryName'], value_vars=cols, var_name='Pillar', value_name='Score')

    fig = px.bar(melted, x='CountryName', y='Score', color='Pillar', barmode='stack',
                title=f"Contribución por Pilar ({year})",
                labels={'Score':'Contribución', 'CountryName':'País'})
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('bar-pillar-d-components', 'figure'),
    [Input('country-selector', 'value'), Input('year-selector', 'value')]
)
def update_pillar_d(countries, year):
    if not countries or df_cas.empty: return go.Figure().update_layout(title="Seleccione países")

    comp_cols = ['participation_event_it_mm_global', 'decision_event_it_mm_global',
                 'leadership_event_it_mm_global', 'admin_event_it_mm_global', 'role_type_it_mm_global']

    # Filter columns that actually exist
    existing = [c for c in comp_cols if c in df_cas.columns]

    filtered = df_cas[(df_cas['ISO'].isin(countries)) & (df_cas['year'] == year)]
    if filtered.empty: return go.Figure().update_layout(title="No hay datos para esta selección")

    melted = filtered.melt(id_vars=['ISO'], value_vars=existing, var_name='Componente', value_name='Puntaje')
    melted['País'] = melted['ISO'].map(data['iso_map']).fillna(melted['ISO'])

    fig = px.bar(melted, x='Componente', y='Puntaje', color='País', barmode='group',
                title=f"Métricas de Participación OMS - {year}")
    fig.update_layout(template='plotly_white', xaxis_tickangle=-45)
    return fig

@app.callback(
    Output('scatter-noexclusion', 'figure'),
    [Input('year-selector', 'value')]
)
def update_exclusion_scatter(year):
    filtered = df[df['year'] == year]
    fig = px.scatter(filtered, x='NoExclusion', y='pillar_D_eq', hover_name='CountryName',
                    title=f"Pillar D vs Penalización NoExclusión ({year})",
                    labels={'NoExclusion':'Índice NoExclusión', 'pillar_D_eq':'Pilar D (Liderazgo)'})
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('bar-shap-importance', 'figure'),
    [Input('variant-selector', 'value')]
)
def update_shap(variant):
    shap_cols = [f'SHAP_pillar_A_{variant}', f'SHAP_pillar_B_{variant}', f'SHAP_pillar_C_{variant}']
    if df_cas.empty or not any(c in df_cas.columns for c in shap_cols):
        return go.Figure().update_layout(title="Datos SHAP no disponibles")

    existing = [c for c in shap_cols if c in df_cas.columns]
    mean_shap = df_cas[existing].abs().mean().reset_index()
    mean_shap.columns = ['Pilar', 'Importancia_Media']

    fig = px.bar(mean_shap, x='Pilar', y='Importancia_Media',
                title="Importancia de Pilares (Valores SHAP)",
                color='Importancia_Media', color_continuous_scale='Reds')
    fig.update_layout(template='plotly_white', showlegend=False)
    return fig

@app.callback(
    Output('heatmap-lags', 'figure'),
    [Input('country-selector', 'value')]
)
def update_lags(countries):
    lag_cols = ['A_lag', 'B_lag', 'C_lag', 'D_lag']
    if df_cas.empty: return go.Figure().update_layout(title="Datos no disponibles")

    existing = [c for c in lag_cols if c in df_cas.columns]
    if not existing: return go.Figure().update_layout(title="Sin rezagos temporales")

    filtered = df_cas[df_cas['ISO'].isin(countries)] if countries else df_cas
    if filtered.empty: filtered = df_cas

    corr = filtered[existing].corr()
    fig = px.imshow(corr, text_auto=True, title="Correlación Temporal (Lags)",
                   color_continuous_scale='RdBu_r', range_color=[-1,1])
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('scatter-dependency', 'figure'),
    [Input('variant-selector', 'value')]
)
def update_dep(variant):
    if df_cas.empty: return go.Figure().update_layout(title="Datos no disponibles")

    y_col = f'pillar_D_{variant}_resid' if f'pillar_D_{variant}_resid' in df_cas.columns else 'pillarD_resid'
    x_col = 'wpi_val'

    if y_col not in df_cas.columns or x_col not in df_cas.columns:
         return go.Figure().update_layout(title="Residuales no encontrados")

    fig = px.scatter(df_cas, x=x_col, y=y_col, color='year',
                    trendline="lowess",
                    title=f"Dependencia No Lineal: Esfuerzo vs Poder Estructural",
                    labels={x_col:'Poder Estructural (WPI)', y_col:'Residuo (Esfuerzo)'})
    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('trace-table-container', 'children'),
    [Input('trace-country', 'value'), Input('year-selector', 'value')]
)
def update_traceability(iso, year):
    if not iso: return "Seleccione un país"
    row = df[(df['ISO'] == iso) & (df['year'] == year)]
    if row.empty: return f"No hay datos para {iso} en {year}"

    # Key indicators audit
    indicators = [
        ('e_spar', 'Seguridad Sanitaria (SPAR)'),
        ('ghs_index', 'Índice GHS'),
        ('hexp_gdp', 'Gasto Salud (% PIB)'),
        ('uhc_index', 'Índice UHC')
    ]

    trace_data = []
    for raw_key, name in indicators:
        norm_key = f"{raw_key}_mm_global"
        flag_key = f"{raw_key}_flag"

        raw_val = "N/A"
        if not df_cas.empty:
            raw_row = df_cas[(df_cas['ISO'] == iso) & (df_cas['year'] == year)]
            if raw_key in raw_row.columns: raw_val = round(raw_row[raw_key].iloc[0], 3)

        norm_val = round(row[norm_key].iloc[0], 3) if norm_key in row.columns else "N/A"
        status = row[flag_key].iloc[0] if flag_key in row.columns else "N/A"

        trace_data.append({
            "Indicador": name,
            "Valor Crudo": raw_val,
            "Normalizado (0-1)": norm_val,
            "Estado del Dato": status
        })

    table = dash_table.DataTable(
        data=trace_data,
        columns=[{"name": i, "id": i} for i in trace_data[0].keys()],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'filter_query': '{Estado del Dato} == "imputed"'}, 'backgroundColor': '#fff3cd'},
            {'if': {'filter_query': '{Estado del Dato} == "missing"'}, 'backgroundColor': '#f8d7da'}
        ]
    )

    return html.Div([
        table,
        html.Div([
            html.P([html.B("Nota: "), "Los datos en amarillo están imputados. Los rojos están faltantes."])
        ], className="mt-2 small text-muted")
    ])

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-csv", "n_clicks"),
    prevent_initial_call=True,
)
def download_csv(n_clicks):
    return dcc.send_data_frame(df.to_csv, "ghei_datos_completos.csv")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
