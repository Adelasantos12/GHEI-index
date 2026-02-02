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
                    # Mod 1: Perfil de Compromiso
                    dbc.Tab(label="👤 Perfil de Compromiso", tab_id="tab-profile", children=[
                        html.Div([
                            html.Div([
                                html.H4("Resumen Estructural del Compromiso", className="mt-4"),
                                html.P("Análisis configuracional del país seleccionado, identificando habilitadores y cuellos de botella."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dbc.Row([
                                dbc.Col(html.Div(id='profile-summary'), width=12),
                            ]),
                            html.Hr(),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Configuración de Pilares (0-1)"),
                                    dcc.Graph(id='pillar-config-map'),
                                    html.Small("El pilar con menor puntaje actúa como cuello de botella sistémico.", className="text-muted")
                                ], width=12)
                            ])
                        ], className="p-3")
                    ]),

                    # Mod 3 & 4: Trayectoria y Agencia
                    dbc.Tab(label="📈 Trayectoria y Agencia", tab_id="tab-agency", children=[
                        html.Div([
                            html.Div([
                                html.H4("Evolución Temporal y Capacidad de Agencia", className="mt-4"),
                                html.P("Sincronización de la contribución total con la cooperación y el liderazgo institucional."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dcc.Graph(id='line-trajectory-sync'),
                            html.Hr(),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Presencia vs. Agencia (Pilar D)"),
                                    html.P("La asistencia frecuente (presencia) no garantiza influencia (liderazgo/agencia).", className="small"),
                                    dcc.Graph(id='scatter-presence-agency')
                                ], width=12)
                            ])
                        ], className="p-3")
                    ]),

                    # Mod 5 & 6: Analítica de Sistemas
                    dbc.Tab(label="🧠 Analítica de Sistemas", tab_id="tab-systems", children=[
                        html.Div([
                            html.Div([
                                html.H4("Ajuste Estructural y Umbrales de Activación", className="mt-4"),
                                html.P("Interpretación del desempeño relativo al poder estructural (WPI) y dependencias no lineales."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("GHEI vs Poder Estructural"),
                                    dcc.Graph(id='scatter-capacity-adj')
                                ], width=6),
                                dbc.Col([
                                    html.H5("Umbrales de Activación (CAS)"),
                                    dcc.Graph(id='scatter-thresholds')
                                ], width=6)
                            ]),
                            html.Div([
                                html.P("Nota: Los umbrales muestran puntos empíricos donde el compromiso tiende a estabilizarse o activarse.", className="small text-muted")
                            ], className="mt-2")
                        ], className="p-3")
                    ]),

                    # Mod 7: Robustez y Límites
                    dbc.Tab(label="🛡️ Robustez y Límites", tab_id="tab-limits", children=[
                        html.Div([
                            html.Div([
                                html.H4("Sensibilidad y Límites Epistémicos", className="mt-4"),
                                html.P("Evaluación de la solidez de los resultados y declaración explícita de lo que el índice NO mide."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Probabilidad de Liderazgo (Top-K)"),
                                    dcc.Graph(id='bar-robustness')
                                ], width=7),
                                dbc.Col([
                                    html.H5("Límites de la Medición"),
                                    html.Div([
                                        html.Ul([
                                            html.Li("Sin afirmaciones causales: El índice describe configuraciones, no causas."),
                                            html.Li("Sin medición de influencia informal: Solo se capturan roles institucionales registrados."),
                                            html.Li("Margen de error de fuente: El índice hereda incertidumbres de las fuentes primarias (SPAR, GHS)."),
                                            html.Li("Interpretación, no prescripción: Los resultados no son recomendaciones automáticas."),
                                        ])
                                    ], className="small")
                                ], width=5)
                            ])
                        ], className="p-3")
                    ]),

                    # Tab: Trazabilidad (Keep original)
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
                ], id="tabs-main", active_tab="tab-profile")
            ], width=9)
        ])
    ], fluid=True, className="pb-5")
])

# --- Callbacks ---

@app.callback(
    Output('profile-summary', 'children'),
    [Input('country-selector', 'value'), Input('year-selector', 'value'), Input('variant-selector', 'value')]
)
def update_profile_summary(countries, year, variant):
    if not countries:
        return dbc.Alert("Seleccione un país en el panel lateral para generar el perfil.", color="info")

    iso = countries[0] # Use first selected country
    row = df[(df['ISO'] == iso) & (df['year'] == year)]
    if row.empty:
        return dbc.Alert(f"No hay datos para {iso} en {year}.", color="warning")

    country_name = row['CountryName'].iloc[0]
    p_scores = {k: row[f'pillar_{k}_{variant}'].iloc[0] for k in ['A', 'B', 'C', 'D']}

    # Logic for summary
    sorted_p = sorted(p_scores.items(), key=lambda x: x[1], reverse=True)
    dom_key = sorted_p[0][0]
    con_key = sorted_p[-1][0]

    ghei = row['GHEI'].iloc[0]
    ghei_adj = row['GHEI_adj'].iloc[0]
    perf_status = "sobre-desempeño" if ghei_adj > ghei else "sub-desempeño"

    return dbc.Card([
        dbc.CardBody([
            html.H5(f"Análisis de Compromiso: {country_name} ({year})", className="card-title text-primary"),
            dbc.Row([
                dbc.Col([
                    html.P([html.B("Configuración Dominante: "), meta['pillars'][dom_key]]),
                    html.P([html.B("Habilitador Principal: "), f"{meta['pillars'][dom_key]} (puntuación: {p_scores[dom_key]:.2f})"]),
                    html.P([html.B("Cuello de Botella (Restricción): "), f"{meta['pillars'][con_key]} (puntuación: {p_scores[con_key]:.2f})"]),
                ], width=6),
                dbc.Col([
                    html.P([html.B("GHEI Absoluto: "), f"{ghei:.3f}"]),
                    html.P([html.B("GHEI Ajustado (Esfuerzo): "), f"{ghei_adj:.3f}"]),
                    html.P([
                        html.B("Interpretación: "),
                        f"El país muestra un {perf_status} relativo a su poder estructural. ",
                        "Esto indica que su contribución a la salud global está " +
                        ("más" if ghei_adj > ghei else "menos") + " impulsada por voluntad política que por capacidad económica pura."
                    ])
                ], width=6)
            ])
        ])
    ], className="shadow-sm border-start border-primary border-5")

@app.callback(
    Output('pillar-config-map', 'figure'),
    [Input('country-selector', 'value'), Input('year-selector', 'value'), Input('variant-selector', 'value')]
)
def update_pillar_map(countries, year, variant):
    if not countries: return go.Figure().update_layout(title="Seleccione un país")

    iso = countries[0]
    row = df[(df['ISO'] == iso) & (df['year'] == year)]
    if row.empty: return go.Figure()

    categories = ['A', 'B', 'C', 'D']
    scores = [row[f'pillar_{k}_{variant}'].iloc[0] for k in categories]
    labels = [meta['pillars'][k] for k in categories]
    descs = [meta['pillar_desc'][k] for k in categories]

    # Find bottleneck
    min_idx = np.argmin(scores)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=labels + [labels[0]],
        fill='toself',
        name=row['CountryName'].iloc[0],
        hoverinfo="text",
        text=[f"{l}: {s:.2f}<br>{d}" for l, s, d in zip(labels, scores, descs)] + [f"{labels[0]}: {scores[0]:.2f}"]
    ))

    # Highlight bottleneck
    fig.add_trace(go.Scatterpolar(
        r=[scores[min_idx]],
        theta=[labels[min_idx]],
        mode='markers',
        marker=dict(color='red', size=12, symbol='x'),
        name='Cuello de Botella',
        hoverinfo="text",
        text=[f"RESTRICCIÓN: {labels[min_idx]} es el pilar limitante."]
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        template='plotly_white',
        title=f"Configuración del Compromiso: {row['CountryName'].iloc[0]} ({year})"
    )
    return fig

@app.callback(
    Output('scatter-presence-agency', 'figure'),
    [Input('country-selector', 'value'), Input('year-selector', 'value')]
)
def update_presence_agency(countries, year):
    filtered = df[df['year'] == year]

    fig = px.scatter(
        filtered,
        x='participation_event_it_mm_global',
        y='leadership_event_it_mm_global',
        hover_name='CountryName',
        color='ISO',
        title=f"Presencia vs. Agencia ({year})",
        labels={
            'participation_event_it_mm_global': 'Presencia (Frecuencia de Asistencia)',
            'leadership_event_it_mm_global': 'Agencia (Roles de Liderazgo)'
        }
    )

    # Highlight selected countries
    if countries:
        selected = filtered[filtered['ISO'].isin(countries)]
        fig.add_trace(go.Scatter(
            x=selected['participation_event_it_mm_global'],
            y=selected['leadership_event_it_mm_global'],
            mode='markers+text',
            text=selected['CountryName'],
            textposition='top center',
            marker=dict(color='red', size=12, symbol='star'),
            name='Seleccionados'
        ))

    fig.add_annotation(
        x=0.8, y=0.1,
        text="Alta Presencia ≠ Alta Influencia",
        showarrow=False,
        font=dict(size=14, color="red"),
        bgcolor="white",
        bordercolor="red"
    )

    fig.update_layout(template='plotly_white', showlegend=False)
    return fig

@app.callback(
    Output('line-trajectory-sync', 'figure'),
    [Input('country-selector', 'value'), Input('variant-selector', 'value')]
)
def update_trajectory(countries, variant):
    if not countries: return go.Figure().update_layout(title="Seleccione países para ver la trayectoria")

    filtered = df[df['ISO'].isin(countries)].copy()

    # We want GHEI, Pillar C and Pillar D
    cols = ['GHEI', f'pillar_C_{variant}', f'pillar_D_{variant}']
    labels = {'GHEI': 'GHEI (Total)', f'pillar_C_{variant}': 'Pilar C (Cooperación)', f'pillar_D_{variant}': 'Pilar D (Liderazgo)'}

    melted = filtered.melt(id_vars=['year', 'CountryName', 'ISO'], value_vars=cols,
                          var_name='Métrica', value_name='Valor')
    melted['Métrica'] = melted['Métrica'].map(labels)

    fig = px.line(melted, x='year', y='Valor', color='CountryName', line_dash='Métrica',
                 markers=True, title="Trayectoria: GHEI vs. Cooperación (C) vs. Liderazgo (D)",
                 labels={'year':'Año', 'Valor':'Puntaje', 'CountryName':'País'})

    # Add event markers for NoExclusion changes
    for iso in countries:
        country_df = filtered[filtered['ISO'] == iso].sort_values('year')
        for i in range(1, len(country_df)):
            if country_df['NoExclusion'].iloc[i] != country_df['NoExclusion'].iloc[i-1]:
                year = country_df['year'].iloc[i]
                status = "Política No Excluyente" if country_df['NoExclusion'].iloc[i] == 1 else "Política Excluyente"
                fig.add_vline(x=year, line_dash="dash", line_color="grey")
                fig.add_annotation(x=year, y=1.0, text=f"{iso}: {status}", showarrow=True, arrowhead=1)

    fig.update_layout(template='plotly_white', hovermode='x unified', yaxis_range=[0,1.1])
    return fig

@app.callback(
    Output('bar-robustness', 'figure'),
    [Input('country-selector', 'value')]
)
def update_robustness(countries):
    if df_topk.empty or not countries:
        return go.Figure().update_layout(title="Seleccione países para ver análisis de robustez")

    filtered = df_topk[df_topk['ISO'].isin(countries)].copy()
    filtered['CountryName'] = filtered['ISO'].map(data['iso_map']).fillna(filtered['ISO'])

    fig = px.bar(filtered, x='CountryName', y='prob_top_k',
                title="Robustez: Probabilidad de pertenecer al Top-20",
                labels={'prob_top_k':'Probabilidad de Liderazgo Robustos', 'CountryName':'País'},
                color='prob_top_k', color_continuous_scale='Blues')

    fig.add_annotation(
        x=0.5, y=-0.2, xref="paper", yref="paper",
        text="Muestra qué tan probable es que el país mantenga su posición ante cambios en los pesos del índice.",
        showarrow=False, font=dict(size=10, color="grey")
    )

    fig.update_layout(template='plotly_white', showlegend=False)
    return fig

@app.callback(
    Output('scatter-capacity-adj', 'figure'),
    [Input('year-selector', 'value'), Input('country-selector', 'value')]
)
def update_capacity_adj(year, countries):
    filtered = df[df['year'] == year].copy()

    # Ensure wpi_val is present
    if 'wpi_val' not in filtered.columns and not df_cas.empty:
        wpi_data = df_cas[df_cas['year'] == year][['ISO', 'wpi_val']]
        filtered = filtered.merge(wpi_data, on='ISO', how='left')

    if 'wpi_val' not in filtered.columns:
        return go.Figure().update_layout(title="Datos WPI no disponibles")

    fig = px.scatter(filtered, x='wpi_val', y='GHEI', hover_name='CountryName',
                    trendline="ols", title=f"GHEI vs Poder Estructural (WPI) - {year}",
                    labels={'wpi_val':'Poder Estructural (WPI)', 'GHEI':'GHEI Absoluto'})

    # Identify over/under performers
    if countries:
        selected = filtered[filtered['ISO'].isin(countries)]
        fig.add_trace(go.Scatter(
            x=selected['wpi_val'], y=selected['GHEI'],
            mode='markers+text',
            text=selected['ISO'],
            textposition='top center',
            marker=dict(color='red', size=10, symbol='diamond'),
            name='Seleccionados'
        ))

    fig.add_annotation(
        x=filtered['wpi_val'].min(), y=filtered['GHEI'].max(),
        text="Arriba de la línea: Sobre-desempeño (Esfuerzo superior al esperado)",
        showarrow=False, font=dict(color="green")
    )

    fig.update_layout(template='plotly_white', showlegend=False)
    return fig

@app.callback(
    Output('scatter-thresholds', 'figure'),
    [Input('variant-selector', 'value')]
)
def update_thresholds(variant):
    if df_cas.empty: return go.Figure().update_layout(title="Datos CAS no disponibles")

    # Use residual of Pillar D vs WPI to show 'effort' beyond structural capacity
    y_col = f'pillar_D_{variant}_resid' if f'pillar_D_{variant}_resid' in df_cas.columns else 'pillarD_resid'
    x_col = 'wpi_val'

    if y_col not in df_cas.columns or x_col not in df_cas.columns:
         return go.Figure().update_layout(title="Variables de activación no encontradas")

    fig = px.scatter(df_cas, x=x_col, y=y_col, color='year',
                    trendline="lowess",
                    title="Análisis de Activación: Esfuerzo vs Capacidad",
                    labels={x_col:'Poder Estructural (WPI)', y_col:'Activación (Residuo de Liderazgo)'})

    fig.add_annotation(
        x=df_cas[x_col].median(), y=df_cas[y_col].max(),
        text="Umbral de Activación: El punto donde el esfuerzo deja de ser lineal.",
        showarrow=True, arrowhead=2
    )

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
