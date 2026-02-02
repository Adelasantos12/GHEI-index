import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dashboard_data import load_dashboard_data, get_pillar_cols, get_metadata_en

# Initialize data
data = load_dashboard_data()
df = data['main']
df_cas = data['cas']
df_topk = data['topk']
meta = get_metadata_en()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
server = app.server

# --- Custom Components ---

def make_header():
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Quick Guide", href="#")),
        ],
        brand="GHEI Dashboard: Global Health Analytics",
        brand_href="#",
        color="primary",
        dark=True,
        className="mb-4"
    )

def make_sidebar():
    return dbc.Card([
        dbc.CardHeader(html.H5("Configuration and Filters", className="mb-0")),
        dbc.CardBody([
            html.Label("1. Select Countries:", className="fw-bold"),
            dcc.Dropdown(
                id='country-selector',
                options=[{'label': row['CountryName'], 'value': row['ISO']} for _, row in df[['ISO', 'CountryName']].drop_duplicates().sort_values('CountryName').iterrows()],
                value=['USA', 'MEX', 'BRA', 'ESP'],
                multi=True,
                placeholder="Search country..."
            ),
            html.Small("You may select multiple countries to compare.", className="text-muted"),

            html.Br(), html.Br(),
            html.Label("2. Analysis Year:", className="fw-bold"),
            dcc.Dropdown(
                id='year-selector',
                options=[{'label': str(y), 'value': y} for y in sorted(df['year'].unique(), reverse=True)],
                value=df['year'].max()
            ),

            html.Br(),
            html.Label("3. Weighting Method:", className="fw-bold"),
            dbc.RadioItems(
                id='variant-selector',
                options=[
                    {'label': 'Equal Weights (Base)', 'value': 'eq'},
                    {'label': 'PCA Analysis', 'value': 'pca'},
                    {'label': 'Entropy Weights', 'value': 'ent'}
                ],
                value='eq'
            ),
            html.Small("Different ways to calculate the importance of each pillar.", className="text-muted"),
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
                    html.H6("Key Concepts", className="fw-bold"),
                    make_info_card("Absolute GHEI", "Total score based on observed performance."),
                    make_info_card("Adjusted GHEI", "Score that removes the advantage of economic power (WPI), rewarding those who do more with less."),
                    make_info_card("Pillar D", "WHO Governance Engagement: leadership and agency."),
                ], className="mt-4")
            ], width=3),

            # Content
            dbc.Col([
                dbc.Tabs([
                    # Mod 1: Country Engagement Profile
                    dbc.Tab(label="Country Engagement Profile", tab_id="tab-profile", children=[
                        html.Div([
                            html.Div([
                                html.H4("Structural Summary of Engagement", className="mt-4"),
                                html.P("Configurational analysis of the selected country, identifying enablers and bottlenecks."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dbc.Row([
                                dbc.Col(html.Div(id='profile-summary'), width=12),
                            ]),
                            html.Hr(),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Pillar Configuration (0-1)"),
                                    dcc.Graph(id='pillar-config-map'),
                                    html.Small("The pillar with the lowest score acts as a systemic bottleneck.", className="text-muted")
                                ], width=12)
                            ])
                        ], className="p-3")
                    ]),

                    # Mod 3 & 4: Trajectory and Agency
                    dbc.Tab(label="Trajectory and Agency", tab_id="tab-agency", children=[
                        html.Div([
                            html.Div([
                                html.H4("Temporal Evolution and Agency Capacity", className="mt-4"),
                                html.P("Synchronisation of total contribution with political commitment and institutional engagement."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dcc.Graph(id='line-trajectory-sync'),
                            html.Hr(),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Presence vs. Agency (Pillar D)"),
                                    html.P("Frequent attendance (presence) does not guarantee influence (leadership/agency).", className="small"),
                                    dcc.Graph(id='scatter-presence-agency')
                                ], width=12)
                            ])
                        ], className="p-3")
                    ]),

                    # Mod 5 & 6: Systems Analytics
                    dbc.Tab(label="Systems Analytics", tab_id="tab-systems", children=[
                        html.Div([
                            html.Div([
                                html.H4("Structural Adjustment and Activation Thresholds", className="mt-4"),
                                html.P("Interpretation of performance relative to structural power (WPI) and non-linear dependencies."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("GHEI vs Structural Power"),
                                    dcc.Graph(id='scatter-capacity-adj')
                                ], width=6),
                                dbc.Col([
                                    html.H5("Activation Thresholds (CAS)"),
                                    dcc.Graph(id='scatter-thresholds')
                                ], width=6)
                            ]),
                            html.Div([
                                html.P("Note: Thresholds show empirical points where engagement tends to stabilise or activate.", className="small text-muted")
                            ], className="mt-2")
                        ], className="p-3")
                    ]),

                    # Mod 7: Robustness and Limits
                    dbc.Tab(label="Robustness and Limits", tab_id="tab-limits", children=[
                        html.Div([
                            html.Div([
                                html.H4("Sensitivity and Epistemic Limits", className="mt-4"),
                                html.P("Evaluation of results robustness and explicit statement of what the index does NOT measure."),
                            ], className="p-3 bg-light rounded mb-4"),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Leadership Probability (Top-K)"),
                                    dcc.Graph(id='bar-robustness')
                                ], width=7),
                                dbc.Col([
                                    html.H5("Measurement Limits"),
                                    html.Div([
                                        html.Ul([
                                            html.Li("No causal claims: The index describes configurations, not causes."),
                                            html.Li("No measurement of informal influence: Only registered institutional roles are captured."),
                                            html.Li("Source-level measurement error: The index inherits uncertainties from primary sources (SPAR, GHS)."),
                                            html.Li("Interpretation, not prescription: Results are not automatic recommendations."),
                                        ])
                                    ], className="small")
                                ], width=5)
                            ])
                        ], className="p-3")
                    ]),

                    # Tab: Data Audit
                    dbc.Tab(label="Data Audit", tab_id="tab-trace", children=[
                        html.Div([
                            html.Div([
                                html.H4("Traceability and Transparency", className="mt-4"),
                                html.P("Consult original (raw) and normalised values for a specific country."),
                            ], className="p-3 bg-light rounded mb-4"),
                            html.Label("Select a country to audit:", className="fw-bold"),
                            dcc.Dropdown(id='trace-country', options=[{'label': n, 'value': i} for i, n in data['iso_map'].items()], value='MEX'),
                            html.Br(),
                            html.Div(id='trace-table-container'),
                            html.Div([
                                dbc.Button("Download Full Data (CSV)", id="btn-csv", color="success", className="mt-3"),
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
        return dbc.Alert("Select a country in the sidebar to generate the profile.", color="info")

    iso = countries[0] # Use first selected country
    row = df[(df['ISO'] == iso) & (df['year'] == year)]
    if row.empty:
        return dbc.Alert(f"No data for {iso} in {year}.", color="warning")

    country_name = row['CountryName'].iloc[0]
    p_scores = {k: row[f'pillar_{k}_{variant}'].iloc[0] for k in ['A', 'B', 'C', 'D']}

    # Logic for summary
    sorted_p = sorted(p_scores.items(), key=lambda x: x[1], reverse=True)
    dom_key = sorted_p[0][0]
    con_key = sorted_p[-1][0]

    ghei = row['GHEI'].iloc[0]
    ghei_adj = row['GHEI_adj'].iloc[0]
    perf_status = "over-performance" if ghei_adj > ghei else "under-performance"

    return dbc.Card([
        dbc.CardBody([
            html.H5(f"Engagement Analysis: {country_name} ({year})", className="card-title text-primary"),
            dbc.Row([
                dbc.Col([
                    html.P([html.B("Dominant Configuration: "), meta['pillars'][dom_key]]),
                    html.P([html.B("Main Enabler: "), f"{meta['pillars'][dom_key]} (score: {p_scores[dom_key]:.2f})"]),
                    html.P([html.B("Bottleneck (Constraint): "), f"{meta['pillars'][con_key]} (score: {p_scores[con_key]:.2f})"]),
                ], width=6),
                dbc.Col([
                    html.P([html.B("Absolute GHEI: "), f"{ghei:.3f}"]),
                    html.P([html.B("Adjusted GHEI (Effort): "), f"{ghei_adj:.3f}"]),
                    html.P([
                        html.B("Interpretation: "),
                        f"The country shows an {perf_status} relative to its structural power. ",
                        "This indicates that its contribution to global health is " +
                        ("more" if ghei_adj > ghei else "less") + " driven by political will than by pure economic capacity."
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
    if not countries: return go.Figure().update_layout(title="Select a country")

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
        name='Bottleneck',
        hoverinfo="text",
        text=[f"CONSTRAINT: {labels[min_idx]} is the limiting pillar."]
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        template='plotly_white',
        title=f"Engagement Configuration: {row['CountryName'].iloc[0]} ({year})"
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
        title=f"Presence vs. Agency (Pillar D) - {year}",
        labels={
            'participation_event_it_mm_global': 'Presence (Attendance Frequency)',
            'leadership_event_it_mm_global': 'Agency (Leadership Roles)'
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
            name='Selected'
        ))

    fig.add_annotation(
        x=0.8, y=0.1,
        text="High Presence ≠ High Influence",
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
    if not countries: return go.Figure().update_layout(title="Select countries to see trajectory")

    filtered = df[df['ISO'].isin(countries)].copy()

    # We want GHEI, Pillar C and Pillar D
    cols = ['GHEI', f'pillar_C_{variant}', f'pillar_D_{variant}']
    labels = {
        'GHEI': 'GHEI (Total)',
        f'pillar_C_{variant}': 'Pillar C (Commitment)',
        f'pillar_D_{variant}': 'Pillar D (Engagement)'
    }

    melted = filtered.melt(id_vars=['year', 'CountryName', 'ISO'], value_vars=cols,
                          var_name='Metric', value_name='Value')
    melted['Metric'] = melted['Metric'].map(labels)

    fig = px.line(melted, x='year', y='Value', color='CountryName', line_dash='Metric',
                 markers=True, title="Trajectory: GHEI vs. Commitment (C) vs. Engagement (D)",
                 labels={'year':'Year', 'Value':'Score', 'CountryName':'Country'})

    # Add event markers for NoExclusion changes
    for iso in countries:
        country_df = filtered[filtered['ISO'] == iso].sort_values('year')
        for i in range(1, len(country_df)):
            if country_df['NoExclusion'].iloc[i] != country_df['NoExclusion'].iloc[i-1]:
                year = country_df['year'].iloc[i]
                status = "Non-Exclusionary Policy" if country_df['NoExclusion'].iloc[i] == 1 else "Exclusionary Policy"
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
        return go.Figure().update_layout(title="Select countries to see robustness analysis")

    filtered = df_topk[df_topk['ISO'].isin(countries)].copy()
    filtered['CountryName'] = filtered['ISO'].map(data['iso_map']).fillna(filtered['ISO'])

    fig = px.bar(filtered, x='CountryName', y='prob_top_k',
                title="Robustness: Probability of belonging to Top-20",
                labels={'prob_top_k':'Robust Leadership Probability', 'CountryName':'Country'},
                color='prob_top_k', color_continuous_scale='Blues')

    fig.add_annotation(
        x=0.5, y=-0.2, xref="paper", yref="paper",
        text="Shows how likely the country is to maintain its position given changes in index weights.",
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
        return go.Figure().update_layout(title="WPI data not available")

    fig = px.scatter(filtered, x='wpi_val', y='GHEI', hover_name='CountryName',
                    trendline="ols", title=f"GHEI vs Structural Power (WPI) - {year}",
                    labels={'wpi_val':'Structural Power (WPI)', 'GHEI':'Absolute GHEI'})

    # Identify over/under performers
    if countries:
        selected = filtered[filtered['ISO'].isin(countries)]
        fig.add_trace(go.Scatter(
            x=selected['wpi_val'], y=selected['GHEI'],
            mode='markers+text',
            text=selected['ISO'],
            textposition='top center',
            marker=dict(color='red', size=10, symbol='diamond'),
            name='Selected'
        ))

    fig.add_annotation(
        x=filtered['wpi_val'].min(), y=filtered['GHEI'].max(),
        text="Above the line: Over-performance (Effort superior to expected)",
        showarrow=False, font=dict(color="green")
    )

    fig.update_layout(template='plotly_white', showlegend=False)
    return fig

@app.callback(
    Output('scatter-thresholds', 'figure'),
    [Input('variant-selector', 'value')]
)
def update_thresholds(variant):
    if df_cas.empty: return go.Figure().update_layout(title="CAS data not available")

    # Use residual of Pillar D vs WPI to show 'effort' beyond structural capacity
    y_col = f'pillar_D_{variant}_resid' if f'pillar_D_{variant}_resid' in df_cas.columns else 'pillarD_resid'
    x_col = 'wpi_val'

    if y_col not in df_cas.columns or x_col not in df_cas.columns:
         return go.Figure().update_layout(title="Activation variables not found")

    fig = px.scatter(df_cas, x=x_col, y=y_col, color='year',
                    trendline="lowess",
                    title="Activation Analysis: Effort vs Capacity",
                    labels={x_col:'Structural Power (WPI)', y_col:'Activation (Leadership Residual)'})

    fig.add_annotation(
        x=df_cas[x_col].median(), y=df_cas[y_col].max(),
        text="Activation Threshold: The point where effort ceases to be linear.",
        showarrow=True, arrowhead=2
    )

    fig.update_layout(template='plotly_white')
    return fig

@app.callback(
    Output('trace-table-container', 'children'),
    [Input('trace-country', 'value'), Input('year-selector', 'value')]
)
def update_traceability(iso, year):
    if not iso: return "Select a country"
    row = df[(df['ISO'] == iso) & (df['year'] == year)]
    if row.empty: return f"No data for {iso} in {year}"

    # Key indicators audit
    indicators = [
        ('e_spar', 'Health Capacity (SPAR)'),
        ('ghs_index', 'GHS Index'),
        ('hexp_gdp', 'Health Expenditure (% of GDP)'),
        ('uhc_index', 'UHC Index')
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
            "Indicator": name,
            "Raw Value": raw_val,
            "Normalised (0-1)": norm_val,
            "Data Status": status
        })

    table = dash_table.DataTable(
        data=trace_data,
        columns=[{"name": i, "id": i} for i in trace_data[0].keys()],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'filter_query': '{Data Status} == "imputed"'}, 'backgroundColor': '#fff3cd'},
            {'if': {'filter_query': '{Data Status} == "missing"'}, 'backgroundColor': '#f8d7da'}
        ]
    )

    return html.Div([
        table,
        html.Div([
            html.P([html.B("Note: "), "Yellow data points are imputed. Red points are missing."])
        ], className="mt-2 small text-muted")
    ])

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-csv", "n_clicks"),
    prevent_initial_call=True,
)
def download_csv(n_clicks):
    return dcc.send_data_frame(df.to_csv, "ghei_full_data.csv")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
