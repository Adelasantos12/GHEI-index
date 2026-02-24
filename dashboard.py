import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy import stats
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
            dbc.NavItem(dbc.NavLink("Documentation", href="#")),
        ],
        brand="GHEI Analytical Platform",
        brand_href="#",
        color="white",
        dark=False,
        className="mb-4 border-bottom shadow-sm",
        style={'fontWeight': 'bold', 'color': '#2c3e50'}
    )

def make_sidebar():
    n_countries = len(df['ISO'].unique())
    min_year = df['year'].min()
    max_year = df['year'].max()

    return html.Div([
        # Filters Section
        dbc.Card([
            dbc.CardHeader(html.H5("Configuration", className="mb-0 text-center", style={'fontSize': '1rem', 'fontWeight': '600'})),
            dbc.CardBody([
                html.Label("Select Countries", className="fw-bold small text-uppercase text-muted"),
                dcc.Dropdown(
                    id='country-selector',
                    options=[{'label': row['CountryName'], 'value': row['ISO']} for _, row in df[['ISO', 'CountryName']].drop_duplicates().sort_values('CountryName').iterrows()],
                    value=['USA', 'MEX', 'BRA', 'ESP'],
                    multi=True,
                    placeholder="Select...",
                    style={'fontSize': '0.9rem'}
                ),

                html.Br(),
                html.Label("Analysis Year", className="fw-bold small text-uppercase text-muted"),
                dcc.Dropdown(
                    id='year-selector',
                    options=[{'label': str(y), 'value': y} for y in sorted(df['year'].unique(), reverse=True)],
                    value=df['year'].max(),
                    clearable=True,
                    placeholder="Select year (or clear for all)",
                    style={'fontSize': '0.9rem'}
                ),

                html.Br(),
                html.Label("Weighting Method", className="fw-bold small text-uppercase text-muted"),
                dbc.RadioItems(
                    id='variant-selector',
                    options=[
                        {'label': 'Equal Weights (Base)', 'value': 'eq'},
                        {'label': 'PCA Analysis', 'value': 'pca'},
                        {'label': 'Entropy Weights', 'value': 'ent'}
                    ],
                    value='eq',
                    style={'fontSize': '0.9rem'}
                ),
            ], className="p-3")
        ], className="shadow-sm mb-4 border-0 bg-white"),

        # Metadata Panel (Academic Trust)
        dbc.Card([
            dbc.CardBody([
                html.H6("Study Metadata", className="fw-bold text-uppercase text-muted mb-3", style={'fontSize': '0.75rem', 'letterSpacing': '1px'}),
                html.Table([
                    html.Tr([html.Td("Period:", className="fw-bold text-secondary pe-2"), html.Td(f"{min_year}–{max_year}")]),
                    html.Tr([html.Td("Countries:", className="fw-bold text-secondary pe-2"), html.Td(f"N = {n_countries}")]),
                    html.Tr([html.Td("Method:", className="fw-bold text-secondary pe-2"), html.Td("Formative composite index")]),
                    html.Tr([html.Td("Aggregation:", className="fw-bold text-secondary pe-2"), html.Td("Equal weights + Robustness")]),
                    html.Tr([html.Td("Normalization:", className="fw-bold text-secondary pe-2"), html.Td("Min-max")]),
                    html.Tr([html.Td("Source:", className="fw-bold text-secondary pe-2"), html.Td("Author calc. (SPAR, WHO, etc.)")]),
                ], style={'fontSize': '0.8rem', 'lineHeight': '1.4', 'width': '100%'})
            ], className="p-3")
        ], className="shadow-sm border-0 bg-light")
    ])

# --- Layout ---

app.layout = html.Div([
    make_header(),
    dbc.Container([
        dbc.Row([
            # Sidebar
            dbc.Col([
                make_sidebar()
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
                                    dbc.Row([
                                        dbc.Col(dcc.Dropdown(id='y-axis-selector', options=[
                                            {'label': 'GHEI (Absolute)', 'value': 'GHEI'},
                                            {'label': 'GHEI (Raw)', 'value': 'GHEI_raw'},
                                            {'label': 'GHEI (Adjusted)', 'value': 'GHEI_adj'}
                                        ], value='GHEI', clearable=False), width=6),
                                        dbc.Col(dcc.Checklist(id='trendline-toggle', options=[
                                            {'label': ' Show Trendline (OLS)', 'value': 'ols'}
                                        ], value=[], inputStyle={"margin-right": "5px"}), width=6, className="d-flex align-items-center")
                                    ], className="mb-2"),
                                    dcc.Graph(id='scatter-capacity-adj')
                                ], width=6),
                                dbc.Col([
                                    html.H5("Activation Analysis (CAS)"),
                                    dcc.Graph(id='scatter-thresholds')
                                ], width=6)
                            ])
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
                            ]),

                            html.Hr(),
                            html.H5("Robustness Check: Aggregation Rule", className="mt-4"),
                            html.P("Comparison between geometric aggregation (GHEI_raw) and arithmetic mean (GHEI_arith)."),

                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='robustness-rho-summary', className="p-2 border rounded bg-light text-center fw-bold")
                                ], width=12)
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col([
                                    html.H6("Top 10 Comparison (Selected Year)"),
                                    html.Div(id='robustness-top10')
                                ], width=6),
                                dbc.Col([
                                    html.H6("Bottom 10 Comparison (Selected Year)"),
                                    html.Div(id='robustness-bottom10')
                                ], width=6)
                            ], className="mt-3"),

                            dbc.Row([
                                dbc.Col([
                                    html.H6("Zero Value Analysis (GHEI_raw=0 vs GHEI_arith=0)"),
                                    html.Div(id='robustness-zeros')
                                ], width=12)
                            ], className="mt-3")

                        ], className="p-3")
                    ]),

                    # Tab: Data Traceability
                    dbc.Tab(label="Data Traceability", tab_id="tab-trace", children=[
                        html.Div([
                            html.Div([
                                html.H4("Data Traceability", className="mt-4"),
                                html.P("Consult original (raw) and normalised values for specific indicators."),
                            ], className="p-3 bg-light rounded mb-4"),
                            html.Label("Select a country:", className="fw-bold"),
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
    perf_status = "above structural expectation" if ghei_adj > ghei else "below structural expectation"

    return dbc.Card([
        dbc.CardBody([
            html.H5(f"Country Profile: {country_name} ({year})", className="card-title fw-bold text-dark"),
            dbc.Row([
                dbc.Col([
                    html.P([html.Span("Dominant Configuration", className="fw-bold small text-muted"), html.Br(), meta['pillars'][dom_key]]),
                    html.P([html.Span("Main Enabler", className="fw-bold small text-muted"), html.Br(), f"{meta['pillars'][dom_key]} ({p_scores[dom_key]:.2f})"]),
                    html.P([html.Span("Systemic Constraint", className="fw-bold small text-muted"), html.Br(), f"{meta['pillars'][con_key]} ({p_scores[con_key]:.2f})"]),
                ], width=6),
                dbc.Col([
                    html.P([html.Span("Absolute GHEI", className="fw-bold small text-muted"), html.Br(), f"{ghei:.3f}"]),
                    html.P([html.Span("Structure-Adjusted GHEI", className="fw-bold small text-muted"), html.Br(), f"{ghei_adj:.3f}"]),
                    html.P([
                        html.Span("Structural Interpretation", className="fw-bold small text-muted"), html.Br(),
                        f"Engagement is {perf_status}."
                    ], className="mt-2")
                ], width=6)
            ])
        ])
    ], className="shadow-sm border-0 bg-white")

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
    [Input('year-selector', 'value'),
     Input('country-selector', 'value'),
     Input('y-axis-selector', 'value'),
     Input('trendline-toggle', 'value')]
)
def update_capacity_adj(year, countries, y_axis, trendline_opts):
    # Handle year selection
    if year is None:
        filtered = df.copy()
        title_year = "2010–2023 (Pooled)"
    else:
        filtered = df[df['year'] == year].copy()
        title_year = str(year)

    # Ensure year is int
    if 'year' in filtered.columns:
        filtered['year'] = filtered['year'].astype(int)

    # Ensure wpi_val is present
    if 'wpi_val' not in filtered.columns:
        if not df_cas.empty:
            cas_copy = df_cas.copy()
            if 'year' in cas_copy.columns:
                cas_copy['year'] = cas_copy['year'].astype(int)

            wpi_data = cas_copy[['ISO', 'year', 'wpi_val']].drop_duplicates()
            filtered = filtered.merge(wpi_data, on=['ISO', 'year'], how='left')

    if 'wpi_val' not in filtered.columns:
        return go.Figure().update_layout(title="WPI data not available")

    # Filter out NaNs for plot
    filtered = filtered.dropna(subset=['wpi_val', y_axis])

    # Determine trendline
    show_ols = 'ols' in (trendline_opts or [])
    trend = 'ols' if show_ols else None

    # Determine color
    color_col = 'year' if year is None else None

    # Hover data
    hover_cols = ["ISO", "year", "GHEI_raw", "GHEI", "GHEI_adj",
                  "pillar_A_eq", "pillar_B_eq", "pillar_C_eq", "pillar_D_eq_adj"]
    hover_cols = [c for c in hover_cols if c in filtered.columns]

    # Titles
    title_text = "Structural Power (WPI) vs Global Health Engagement"
    subtitle_text = f"Absolute and structure-adjusted engagement relative to systemic power | {title_year}"

    fig = px.scatter(
        filtered,
        x='wpi_val',
        y=y_axis,
        hover_name='CountryName',
        hover_data=hover_cols,
        color=color_col,
        trendline=trend,
        labels={'wpi_val':'Structural Power (WPI)', 'GHEI':'Absolute GHEI', 'GHEI_raw':'Raw GHEI', 'GHEI_adj':'Adjusted GHEI'}
    )

    # Identify Selected countries
    if countries:
        selected = filtered[filtered['ISO'].isin(countries)]
        fig.add_trace(go.Scatter(
            x=selected['wpi_val'],
            y=selected[y_axis],
            mode='markers+text',
            text=selected['ISO'],
            textposition='top center',
            marker=dict(color='#d62728', size=8, symbol='circle'), # Academic red
            name='Selected',
            showlegend=False
        ))

    # OLS Stats
    if show_ols and len(filtered) > 1:
        slope, intercept, r_value, p_value, std_err = stats.linregress(filtered['wpi_val'], filtered[y_axis])
        r_squared = r_value**2
        eq_text = f"y = {slope:.2f}x + {intercept:.2f} | R² = {r_squared:.2f}"

        # Add annotation for stats
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.05, y=0.95,
            text=eq_text,
            showarrow=False,
            font=dict(size=12, color="black"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1
        )

    fig.update_layout(
        template='plotly_white',
        title={
            'text': f"<b>{title_text}</b><br><span style='font-size: 12px; color: gray;'>{subtitle_text}</span>",
            'y':0.95,
            'x':0.0,
            'xanchor': 'left',
            'yanchor': 'top'
        },
        showlegend=(year is None),
        font=dict(family="Arial, sans-serif", size=12, color="black"),
        margin=dict(t=80, l=60, r=40, b=60),
        xaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='#f0f0f0'),
        yaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='#f0f0f0'),
    )
    return fig

@app.callback(
    Output('scatter-thresholds', 'figure'),
    [Input('variant-selector', 'value')]
)
def update_thresholds(variant):
    if df_cas.empty: return go.Figure().update_layout(title="CAS data not available")

    # Use GHEI_raw vs WPI residuals as requested
    # We calculate residuals on the fly to ensure accuracy with the requested method
    df_plot = df_cas.dropna(subset=['wpi_val', 'GHEI_raw']).copy()

    if df_plot.empty:
        return go.Figure().update_layout(title="Insufficient data for Activation Analysis")

    slope, intercept, r_value, p_value, std_err = stats.linregress(df_plot['wpi_val'], df_plot['GHEI_raw'])
    df_plot['residual'] = df_plot['GHEI_raw'] - (slope * df_plot['wpi_val'] + intercept)

    x_col = 'wpi_val'
    y_col = 'residual'

    fig = px.scatter(df_plot, x=x_col, y=y_col, color='year',
                    trendline="lowess",
                    title="Activation Analysis (Pooled 2010–2023)",
                    labels={x_col:'Structural Power (WPI)', y_col:'OLS residual from GHEI_raw ~ wpi_val'})

    # Academic Note
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=-0.25,
        text="Positive values indicate engagement above structural expectations.",
        showarrow=False,
        font=dict(size=10, color="gray", style="italic")
    )

    # Threshold Annotation (Median WPI)
    median_wpi = df_plot[x_col].median()
    max_resid = df_plot[y_col].max()

    fig.add_vline(x=median_wpi, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_annotation(
        x=median_wpi, y=max_resid,
        text="Activation Threshold",
        showarrow=True, arrowhead=1,
        ax=40, ay=-20
    )

    fig.update_layout(
        template='plotly_white',
        margin=dict(b=80), # Extra margin for the note
        title={
            'y':0.95,
            'x':0.0,
            'xanchor': 'left',
            'yanchor': 'top'
        }
    )
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

@app.callback(
    [Output('robustness-rho-summary', 'children'),
     Output('robustness-top10', 'children'),
     Output('robustness-bottom10', 'children'),
     Output('robustness-zeros', 'children')],
    [Input('year-selector', 'value')]
)
def update_robustness_aggregation(year):
    # Calculate global rho
    rho_global = df[['GHEI_raw', 'GHEI_arith']].corr(method='spearman').iloc[0, 1]

    # Calculate rho for selected year
    df_year = df[df['year'] == year].copy()
    if len(df_year) > 1:
        rho_year = df_year[['GHEI_raw', 'GHEI_arith']].corr(method='spearman').iloc[0, 1]
    else:
        rho_year = np.nan

    rho_text = f"Global Spearman Rho: {rho_global:.4f} | Rho for {year}: {rho_year:.4f}"

    # Top 5 for selected year (Academic/Minimalist)
    top5_raw = df_year.nlargest(5, 'GHEI_raw')[['CountryName', 'GHEI_raw']].reset_index(drop=True)
    top5_arith = df_year.nlargest(5, 'GHEI_arith')[['CountryName', 'GHEI_arith']].reset_index(drop=True)

    bottom5_raw = df_year.nsmallest(5, 'GHEI_raw')[['CountryName', 'GHEI_raw']].reset_index(drop=True)
    bottom5_arith = df_year.nsmallest(5, 'GHEI_arith')[['CountryName', 'GHEI_arith']].reset_index(drop=True)

    def make_table(d):
        return dbc.Table.from_dataframe(d.round(3), striped=False, bordered=False, hover=True, size='sm', style={'fontSize': '0.85rem'})

    top10_content = html.Div([
        dbc.Row([
            dbc.Col([html.Span("Multiplicative (Raw)", className="small text-muted fw-bold"), make_table(top5_raw)], width=6),
            dbc.Col([html.Span("Arithmetic (Check)", className="small text-muted fw-bold"), make_table(top5_arith)], width=6)
        ])
    ])

    bottom10_content = html.Div([
        dbc.Row([
            dbc.Col([html.Span("Multiplicative (Raw)", className="small text-muted fw-bold"), make_table(bottom5_raw)], width=6),
            dbc.Col([html.Span("Arithmetic (Check)", className="small text-muted fw-bold"), make_table(bottom5_arith)], width=6)
        ])
    ])

    # Zero analysis
    zeros_raw = df_year[df_year['GHEI_raw'] == 0]
    zeros_arith = df_year[df_year['GHEI_arith'] == 0]

    zeros_text = html.Div([
        dbc.Row([
            dbc.Col([
                html.P(f"Countries with GHEI_raw == 0 ({len(zeros_raw)}):"),
                html.Ul([html.Li(n) for n in zeros_raw['CountryName']])
            ], width=6),
            dbc.Col([
                html.P(f"Countries with GHEI_arith == 0 ({len(zeros_arith)}):"),
                html.Ul([html.Li(n) for n in zeros_arith['CountryName']])
            ], width=6)
        ])
    ])

    return rho_text, top10_content, bottom10_content, zeros_text

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
