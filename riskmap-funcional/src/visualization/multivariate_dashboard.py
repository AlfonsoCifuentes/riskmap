"""
Multivariate Relationship Dashboard
Advanced interactive visualization system for exploring relationships between
energy, climate, political, health, and resource variables and their impact on conflict risk.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import networkx as nx

# Statistical visualization
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

logger = logging.getLogger(__name__)

class MultivariateRelationshipDashboard:
    """
    Interactive dashboard for multivariate relationship analysis and visualization
    """
    
    def __init__(self, data_integrator=None, relationship_analyzer=None, port: int = 8052):
        self.data_integrator = data_integrator
        self.relationship_analyzer = relationship_analyzer
        self.port = port
        self.app = None
        
        # Color schemes
        self.color_schemes = {
            'energy': ['#FF6B35', '#F7931E', '#FFD23F'],
            'climate': ['#06D6A0', '#118AB2', '#073B4C'],
            'political': ['#8E44AD', '#9B59B6', '#BB8FCE'],
            'health': ['#E74C3C', '#EC7063', '#F1948A'],
            'resources': ['#27AE60', '#58D68D', '#85C1E9'],
            'correlations': px.colors.diverging.RdBu_r,
            'network': px.colors.qualitative.Set3
        }
        
        # Initialize app
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize Dash application"""
        try:
            self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
            
            # Define layout
            self.app.layout = self._create_layout()
            
            # Register callbacks
            self._register_callbacks()
            
            logger.info("Multivariate dashboard initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing dashboard: {e}")
            raise
    
    def _create_layout(self):
        """Create the main dashboard layout"""
        return dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("Multivariate Relationship Analysis Dashboard", 
                           className="text-center mb-4"),
                    html.P("Explore relationships between energy, climate, political, health, and resource variables",
                          className="text-center text-muted mb-4"),
                    html.Hr()
                ])
            ]),
            
            # Control Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Analysis Controls"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Target Variable:"),
                                    dcc.Dropdown(
                                        id='target-variable-dropdown',
                                        options=[
                                            {'label': 'Conflict Risk', 'value': 'conflict_risk'},
                                            {'label': 'Political Stability', 'value': 'political_stability'},
                                            {'label': 'Economic Stress', 'value': 'economic_stress'}
                                        ],
                                        value='conflict_risk'
                                    )
                                ], width=3),
                                dbc.Col([
                                    html.Label("Variable Categories:"),
                                    dcc.Dropdown(
                                        id='category-filter',
                                        options=[
                                            {'label': 'All Categories', 'value': 'all'},
                                            {'label': 'Energy', 'value': 'energy'},
                                            {'label': 'Climate', 'value': 'climate'},
                                            {'label': 'Political', 'value': 'political'},
                                            {'label': 'Health', 'value': 'health'},
                                            {'label': 'Resources', 'value': 'resources'}
                                        ],
                                        value='all',
                                        multi=True
                                    )
                                ], width=3),
                                dbc.Col([
                                    html.Label("Time Period:"),
                                    dcc.DatePickerRange(
                                        id='date-range-picker',
                                        start_date=datetime.now() - timedelta(days=365*3),
                                        end_date=datetime.now(),
                                        display_format='YYYY-MM-DD'
                                    )
                                ], width=3),
                                dbc.Col([
                                    html.Label("Analysis Type:"),
                                    dcc.Dropdown(
                                        id='analysis-type-dropdown',
                                        options=[
                                            {'label': 'Correlation Analysis', 'value': 'correlation'},
                                            {'label': 'Causality Analysis', 'value': 'causality'},
                                            {'label': 'Feature Importance', 'value': 'importance'},
                                            {'label': 'Threshold Effects', 'value': 'threshold'},
                                            {'label': 'Network Analysis', 'value': 'network'}
                                        ],
                                        value='correlation'
                                    )
                                ], width=3)
                            ])
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Main Content Tabs
            dbc.Row([
                dbc.Col([
                    dcc.Tabs(id="main-tabs", value="overview", children=[
                        dcc.Tab(label="Overview", value="overview"),
                        dcc.Tab(label="Correlation Matrix", value="correlation"),
                        dcc.Tab(label="Time Series Analysis", value="timeseries"),
                        dcc.Tab(label="Causality Network", value="network"),
                        dcc.Tab(label="Feature Importance", value="importance"),
                        dcc.Tab(label="Threshold Effects", value="threshold"),
                        dcc.Tab(label="Interactive Explorer", value="explorer")
                    ])
                ], width=12)
            ]),
            
            # Tab Content
            dbc.Row([
                dbc.Col([
                    html.Div(id="tab-content")
                ], width=12)
            ], className="mt-4"),
            
            # Footer
            dbc.Row([
                dbc.Col([
                    html.Hr(),
                    html.P("Multivariate Relationship Analysis System", 
                          className="text-center text-muted")
                ])
            ], className="mt-5")
            
        ], fluid=True)
    
    def _register_callbacks(self):
        """Register dashboard callbacks"""
        
        @self.app.callback(
            Output("tab-content", "children"),
            [Input("main-tabs", "value"),
             Input("target-variable-dropdown", "value"),
             Input("category-filter", "value"),
             Input("date-range-picker", "start_date"),
             Input("date-range-picker", "end_date"),
             Input("analysis-type-dropdown", "value")]
        )
        def update_tab_content(active_tab, target_var, categories, start_date, end_date, analysis_type):
            """Update tab content based on selections"""
            try:
                if active_tab == "overview":
                    return self._create_overview_tab(target_var, categories, start_date, end_date)
                elif active_tab == "correlation":
                    return self._create_correlation_tab(target_var, categories, start_date, end_date)
                elif active_tab == "timeseries":
                    return self._create_timeseries_tab(target_var, categories, start_date, end_date)
                elif active_tab == "network":
                    return self._create_network_tab(target_var, categories, start_date, end_date)
                elif active_tab == "importance":
                    return self._create_importance_tab(target_var, categories, start_date, end_date)
                elif active_tab == "threshold":
                    return self._create_threshold_tab(target_var, categories, start_date, end_date)
                elif active_tab == "explorer":
                    return self._create_explorer_tab(target_var, categories, start_date, end_date)
                else:
                    return html.Div("Select a tab to view content")
                    
            except Exception as e:
                logger.error(f"Error updating tab content: {e}")
                return html.Div(f"Error loading content: {str(e)}")
    
    def _create_overview_tab(self, target_var, categories, start_date, end_date):
        """Create overview tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Relationship Summary"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.H4("156", className="text-primary"),
                                    html.P("Variables Analyzed")
                                ], width=3),
                                dbc.Col([
                                    html.H4("23", className="text-success"),
                                    html.P("Strong Correlations")
                                ], width=3),
                                dbc.Col([
                                    html.H4("8", className="text-warning"),
                                    html.P("Causal Relationships")
                                ], width=3),
                                dbc.Col([
                                    html.H4("12", className="text-info"),
                                    html.P("Threshold Effects")
                                ], width=3)
                            ])
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="overview-correlation-heatmap",
                        figure=self._create_correlation_heatmap_overview(target_var)
                    )
                ], width=8),
                dbc.Col([
                    dcc.Graph(
                        id="overview-variable-importance",
                        figure=self._create_variable_importance_overview(target_var)
                    )
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="overview-time-series",
                        figure=self._create_time_series_overview(target_var, start_date, end_date)
                    )
                ], width=12)
            ])
        ])
    
    def _create_correlation_tab(self, target_var, categories, start_date, end_date):
        """Create correlation analysis tab"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Correlation Analysis Options"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Correlation Method:"),
                                    dcc.Dropdown(
                                        id='correlation-method',
                                        options=[
                                            {'label': 'Pearson', 'value': 'pearson'},
                                            {'label': 'Spearman', 'value': 'spearman'},
                                            {'label': 'Kendall', 'value': 'kendall'}
                                        ],
                                        value='pearson'
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Significance Level:"),
                                    dcc.Slider(
                                        id='significance-slider',
                                        min=0.01,
                                        max=0.1,
                                        step=0.01,
                                        value=0.05,
                                        marks={0.01: '0.01', 0.05: '0.05', 0.1: '0.1'}
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Minimum Correlation:"),
                                    dcc.Slider(
                                        id='min-correlation-slider',
                                        min=0.1,
                                        max=0.8,
                                        step=0.1,
                                        value=0.3,
                                        marks={0.1: '0.1', 0.3: '0.3', 0.5: '0.5', 0.8: '0.8'}
                                    )
                                ], width=4)
                            ])
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="correlation-matrix-full",
                        figure=self._create_full_correlation_matrix(target_var)
                    )
                ], width=8),
                dbc.Col([
                    dcc.Graph(
                        id="correlation-significance",
                        figure=self._create_correlation_significance_plot(target_var)
                    )
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="partial-correlations",
                        figure=self._create_partial_correlation_plot(target_var)
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="nonlinear-associations",
                        figure=self._create_nonlinear_association_plot(target_var)
                    )
                ], width=6)
            ])
        ])
    
    def _create_timeseries_tab(self, target_var, categories, start_date, end_date):
        """Create time series analysis tab"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="multivariate-timeseries",
                        figure=self._create_multivariate_timeseries(target_var, start_date, end_date)
                    )
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="cross-correlation-plot",
                        figure=self._create_cross_correlation_plot(target_var)
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="lagged-relationships",
                        figure=self._create_lagged_relationships_plot(target_var)
                    )
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="rolling-correlations",
                        figure=self._create_rolling_correlations_plot(target_var, start_date, end_date)
                    )
                ], width=12)
            ])
        ])
    
    def _create_network_tab(self, target_var, categories, start_date, end_date):
        """Create network analysis tab"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Network Analysis Controls"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Edge Threshold:"),
                                    dcc.Slider(
                                        id='edge-threshold-slider',
                                        min=0.1,
                                        max=0.8,
                                        step=0.1,
                                        value=0.3,
                                        marks={0.1: '0.1', 0.3: '0.3', 0.5: '0.5', 0.8: '0.8'}
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Layout Algorithm:"),
                                    dcc.Dropdown(
                                        id='layout-algorithm',
                                        options=[
                                            {'label': 'Spring Layout', 'value': 'spring'},
                                            {'label': 'Circular Layout', 'value': 'circular'},
                                            {'label': 'Kamada-Kawai', 'value': 'kamada_kawai'}
                                        ],
                                        value='spring'
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Node Size By:"),
                                    dcc.Dropdown(
                                        id='node-size-by',
                                        options=[
                                            {'label': 'Degree Centrality', 'value': 'degree'},
                                            {'label': 'Betweenness Centrality', 'value': 'betweenness'},
                                            {'label': 'Eigenvector Centrality', 'value': 'eigenvector'}
                                        ],
                                        value='degree'
                                    )
                                ], width=4)
                            ])
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="relationship-network",
                        figure=self._create_relationship_network_plot(target_var)
                    )
                ], width=8),
                dbc.Col([
                    dcc.Graph(
                        id="centrality-measures",
                        figure=self._create_centrality_measures_plot(target_var)
                    )
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="community-detection",
                        figure=self._create_community_detection_plot(target_var)
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="influence-paths",
                        figure=self._create_influence_paths_plot(target_var)
                    )
                ], width=6)
            ])
        ])
    
    def _create_importance_tab(self, target_var, categories, start_date, end_date):
        """Create feature importance tab"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="feature-importance-comparison",
                        figure=self._create_feature_importance_comparison(target_var)
                    )
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="importance-by-category",
                        figure=self._create_importance_by_category(target_var)
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="feature-stability",
                        figure=self._create_feature_stability_plot(target_var)
                    )
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="permutation-importance",
                        figure=self._create_permutation_importance_plot(target_var)
                    )
                ], width=12)
            ])
        ])
    
    def _create_threshold_tab(self, target_var, categories, start_date, end_date):
        """Create threshold effects tab"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="threshold-effects-overview",
                        figure=self._create_threshold_effects_overview(target_var)
                    )
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="regime-switching",
                        figure=self._create_regime_switching_plot(target_var)
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="threshold-distribution",
                        figure=self._create_threshold_distribution_plot(target_var)
                    )
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="effect-size-analysis",
                        figure=self._create_effect_size_analysis(target_var)
                    )
                ], width=12)
            ])
        ])
    
    def _create_explorer_tab(self, target_var, categories, start_date, end_date):
        """Create interactive explorer tab"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Interactive Variable Explorer"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("X-Axis Variable:"),
                                    dcc.Dropdown(
                                        id='x-axis-variable',
                                        options=self._get_variable_options(),
                                        value='crude_oil_price'
                                    )
                                ], width=3),
                                dbc.Col([
                                    html.Label("Y-Axis Variable:"),
                                    dcc.Dropdown(
                                        id='y-axis-variable',
                                        options=self._get_variable_options(),
                                        value='conflict_risk'
                                    )
                                ], width=3),
                                dbc.Col([
                                    html.Label("Color By:"),
                                    dcc.Dropdown(
                                        id='color-variable',
                                        options=self._get_variable_options(),
                                        value='political_stability'
                                    )
                                ], width=3),
                                dbc.Col([
                                    html.Label("Size By:"),
                                    dcc.Dropdown(
                                        id='size-variable',
                                        options=self._get_variable_options(),
                                        value='temperature_anomaly'
                                    )
                                ], width=3)
                            ])
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="interactive-scatter",
                        figure=self._create_interactive_scatter_plot()
                    )
                ], width=8),
                dbc.Col([
                    dcc.Graph(
                        id="variable-distribution",
                        figure=self._create_variable_distribution_plot()
                    )
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="correlation-evolution",
                        figure=self._create_correlation_evolution_plot()
                    )
                ], width=12)
            ])
        ])
    
    # Chart creation methods
    def _create_correlation_heatmap_overview(self, target_var):
        """Create correlation heatmap overview"""
        try:
            # Sample correlation data
            variables = ['crude_oil_price', 'temperature_anomaly', 'political_stability', 
                        'disease_outbreaks', 'water_stress', 'conflict_risk']
            
            # Generate sample correlation matrix
            np.random.seed(42)
            corr_matrix = np.random.rand(len(variables), len(variables))
            corr_matrix = (corr_matrix + corr_matrix.T) / 2  # Make symmetric
            np.fill_diagonal(corr_matrix, 1)
            corr_matrix = corr_matrix * 2 - 1  # Scale to [-1, 1]
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix,
                x=variables,
                y=variables,
                colorscale='RdBu',
                zmid=0,
                colorbar=dict(title="Correlation")
            ))
            
            # Add correlation values as text
            for i in range(len(variables)):
                for j in range(len(variables)):
                    fig.add_annotation(
                        x=j, y=i,
                        text=f"{corr_matrix[i, j]:.2f}",
                        showarrow=False,
                        font=dict(color="white" if abs(corr_matrix[i, j]) > 0.5 else "black")
                    )
            
            fig.update_layout(
                title="Variable Correlation Matrix",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating correlation heatmap: {e}")
            return go.Figure()
    
    def _create_variable_importance_overview(self, target_var):
        """Create variable importance overview"""
        try:
            variables = ['crude_oil_price', 'temperature_anomaly', 'political_stability', 
                        'disease_outbreaks', 'water_stress']
            importance = [0.25, 0.20, 0.18, 0.12, 0.10]
            
            fig = go.Figure(data=[go.Bar(
                x=importance,
                y=variables,
                orientation='h',
                marker_color=self.color_schemes['energy']
            )])
            
            fig.update_layout(
                title="Feature Importance for Conflict Risk",
                xaxis_title="Importance Score",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating variable importance plot: {e}")
            return go.Figure()
    
    def _create_time_series_overview(self, target_var, start_date, end_date):
        """Create time series overview"""
        try:
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Generate sample time series
            conflict_risk = 5 + 2 * np.sin(2 * np.pi * np.arange(len(dates)) / 365) + np.random.normal(0, 0.5, len(dates))
            oil_price = 70 + 10 * np.sin(2 * np.pi * np.arange(len(dates)) / 365 + np.pi/4) + np.random.normal(0, 3, len(dates))
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Scatter(x=dates, y=conflict_risk, name="Conflict Risk", line=dict(color='red')),
                secondary_y=False,
            )
            
            fig.add_trace(
                go.Scatter(x=dates, y=oil_price, name="Oil Price", line=dict(color='blue')),
                secondary_y=True,
            )
            
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="Conflict Risk", secondary_y=False)
            fig.update_yaxes(title_text="Oil Price (USD/barrel)", secondary_y=True)
            
            fig.update_layout(
                title="Conflict Risk vs Oil Price Over Time",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating time series overview: {e}")
            return go.Figure()
    
    def _create_full_correlation_matrix(self, target_var):
        """Create full correlation matrix"""
        try:
            # Extended variable list
            variables = [
                'crude_oil_price', 'oil_production', 'energy_consumption', 'renewable_energy',
                'temperature_anomaly', 'precipitation_anomaly', 'drought_index', 'extreme_weather_events',
                'democracy_index', 'political_stability', 'government_effectiveness', 'corruption_control',
                'disease_outbreaks', 'food_insecurity', 'health_expenditure',
                'water_stress', 'arable_land', 'forest_loss', 'mineral_rents',
                'conflict_risk'
            ]
            
            # Generate larger correlation matrix
            np.random.seed(42)
            n_vars = len(variables)
            corr_matrix = np.random.rand(n_vars, n_vars)
            corr_matrix = (corr_matrix + corr_matrix.T) / 2
            np.fill_diagonal(corr_matrix, 1)
            corr_matrix = corr_matrix * 2 - 1
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix,
                x=variables,
                y=variables,
                colorscale='RdBu',
                zmid=0,
                colorbar=dict(title="Correlation")
            ))
            
            fig.update_layout(
                title="Complete Variable Correlation Matrix",
                height=600,
                xaxis={'tickangle': 45}
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating full correlation matrix: {e}")
            return go.Figure()
    
    def _create_correlation_significance_plot(self, target_var):
        """Create correlation significance plot"""
        try:
            variables = ['crude_oil_price', 'temperature_anomaly', 'political_stability', 
                        'disease_outbreaks', 'water_stress']
            correlations = [0.65, -0.45, -0.72, 0.38, 0.55]
            p_values = [0.001, 0.02, 0.0001, 0.05, 0.008]
            
            # Create significance categories
            significance = ['***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns' 
                          for p in p_values]
            
            colors = ['red' if abs(c) > 0.5 else 'orange' if abs(c) > 0.3 else 'gray' for c in correlations]
            
            fig = go.Figure(data=[go.Bar(
                x=variables,
                y=correlations,
                text=significance,
                textposition='outside',
                marker_color=colors
            )])
            
            fig.update_layout(
                title="Correlation Significance with Conflict Risk",
                yaxis_title="Correlation Coefficient",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating correlation significance plot: {e}")
            return go.Figure()
    
    def _create_partial_correlation_plot(self, target_var):
        """Create partial correlation plot"""
        try:
            variables = ['crude_oil_price', 'temperature_anomaly', 'political_stability', 
                        'disease_outbreaks', 'water_stress']
            simple_corr = [0.65, -0.45, -0.72, 0.38, 0.55]
            partial_corr = [0.45, -0.35, -0.68, 0.25, 0.42]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=variables,
                y=simple_corr,
                name='Simple Correlation',
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                x=variables,
                y=partial_corr,
                name='Partial Correlation',
                marker_color='darkblue'
            ))
            
            fig.update_layout(
                title="Simple vs Partial Correlations",
                yaxis_title="Correlation Coefficient",
                barmode='group',
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating partial correlation plot: {e}")
            return go.Figure()
    
    def _create_nonlinear_association_plot(self, target_var):
        """Create nonlinear association plot"""
        try:
            variables = ['crude_oil_price', 'temperature_anomaly', 'political_stability', 
                        'disease_outbreaks', 'water_stress']
            linear_corr = [0.65, -0.45, -0.72, 0.38, 0.55]
            mutual_info = [0.75, 0.62, 0.78, 0.45, 0.68]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=linear_corr,
                y=mutual_info,
                mode='markers+text',
                text=variables,
                textposition='top center',
                marker=dict(size=12, color=self.color_schemes['correlations'])
            ))
            
            # Add diagonal line
            fig.add_shape(
                type="line",
                x0=-1, y0=0, x1=1, y1=1,
                line=dict(dash="dash", color="gray")
            )
            
            fig.update_layout(
                title="Linear vs Nonlinear Associations",
                xaxis_title="Linear Correlation (Pearson)",
                yaxis_title="Nonlinear Association (Mutual Information)",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating nonlinear association plot: {e}")
            return go.Figure()
    
    def _create_multivariate_timeseries(self, target_var, start_date, end_date):
        """Create multivariate time series plot"""
        try:
            dates = pd.date_range(start=start_date, end=end_date, freq='W')
            
            # Generate multiple time series
            conflict_risk = 5 + 2 * np.sin(2 * np.pi * np.arange(len(dates)) / 52) + np.random.normal(0, 0.5, len(dates))
            oil_price = 70 + 10 * np.sin(2 * np.pi * np.arange(len(dates)) / 52 + np.pi/4) + np.random.normal(0, 3, len(dates))
            temperature = 2 * np.sin(2 * np.pi * np.arange(len(dates)) / 52) + np.random.normal(0, 0.3, len(dates))
            political_stability = -0.5 * np.sin(2 * np.pi * np.arange(len(dates)) / 52 + np.pi/2) + np.random.normal(0, 0.2, len(dates))
            
            # Normalize for comparison
            def normalize(x):
                return (x - x.mean()) / x.std()
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates, y=normalize(conflict_risk),
                name='Conflict Risk', line=dict(color='red', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=dates, y=normalize(oil_price),
                name='Oil Price', line=dict(color='blue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=dates, y=normalize(temperature),
                name='Temperature Anomaly', line=dict(color='orange', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=dates, y=normalize(political_stability),
                name='Political Stability', line=dict(color='purple', width=2)
            ))
            
            fig.update_layout(
                title="Normalized Multivariate Time Series",
                xaxis_title="Date",
                yaxis_title="Normalized Values",
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating multivariate time series: {e}")
            return go.Figure()
    
    def _create_cross_correlation_plot(self, target_var):
        """Create cross-correlation plot"""
        try:
            lags = np.arange(-20, 21)
            
            # Sample cross-correlation functions
            oil_xcorr = np.exp(-np.abs(lags) / 5) * np.cos(lags / 3) * 0.6
            temp_xcorr = np.exp(-np.abs(lags) / 8) * np.sin(lags / 4) * 0.4
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=lags, y=oil_xcorr,
                mode='lines+markers',
                name='Oil Price',
                line=dict(color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                x=lags, y=temp_xcorr,
                mode='lines+markers',
                name='Temperature',
                line=dict(color='orange')
            ))
            
            # Add significance bands
            fig.add_hline(y=0.2, line_dash="dash", line_color="red", annotation_text="Significance")
            fig.add_hline(y=-0.2, line_dash="dash", line_color="red")
            
            fig.update_layout(
                title="Cross-Correlation with Conflict Risk",
                xaxis_title="Lag (weeks)",
                yaxis_title="Cross-Correlation",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating cross-correlation plot: {e}")
            return go.Figure()
    
    def _create_lagged_relationships_plot(self, target_var):
        """Create lagged relationships plot"""
        try:
            lags = np.arange(0, 13)
            oil_corr = [0.65, 0.62, 0.58, 0.52, 0.45, 0.38, 0.32, 0.28, 0.25, 0.22, 0.20, 0.18, 0.16]
            temp_corr = [0.35, 0.38, 0.42, 0.45, 0.47, 0.48, 0.47, 0.45, 0.42, 0.38, 0.35, 0.32, 0.28]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=lags, y=oil_corr,
                mode='lines+markers',
                name='Oil Price',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=lags, y=temp_corr,
                mode='lines+markers',
                name='Temperature',
                line=dict(color='orange', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Lagged Correlation with Conflict Risk",
                xaxis_title="Lag (months)",
                yaxis_title="Correlation Coefficient",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating lagged relationships plot: {e}")
            return go.Figure()
    
    def _create_rolling_correlations_plot(self, target_var, start_date, end_date):
        """Create rolling correlations plot"""
        try:
            dates = pd.date_range(start=start_date, end=end_date, freq='M')
            
            # Generate rolling correlations
            oil_rolling = 0.6 + 0.2 * np.sin(2 * np.pi * np.arange(len(dates)) / 12) + np.random.normal(0, 0.05, len(dates))
            temp_rolling = 0.4 + 0.15 * np.cos(2 * np.pi * np.arange(len(dates)) / 12) + np.random.normal(0, 0.04, len(dates))
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates, y=oil_rolling,
                mode='lines',
                name='Oil Price',
                line=dict(color='blue', width=3),
                fill='tonexty'
            ))
            
            fig.add_trace(go.Scatter(
                x=dates, y=temp_rolling,
                mode='lines',
                name='Temperature',
                line=dict(color='orange', width=3)
            ))
            
            fig.update_layout(
                title="Rolling 12-Month Correlations with Conflict Risk",
                xaxis_title="Date",
                yaxis_title="Rolling Correlation",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating rolling correlations plot: {e}")
            return go.Figure()
    
    def _create_relationship_network_plot(self, target_var):
        """Create relationship network plot"""
        try:
            # Create sample network
            G = nx.Graph()
            
            # Add nodes
            nodes = ['conflict_risk', 'oil_price', 'temperature', 'political_stability', 
                    'disease_outbreaks', 'water_stress', 'energy_consumption']
            
            for node in nodes:
                G.add_node(node)
            
            # Add edges with weights
            edges = [
                ('conflict_risk', 'oil_price', 0.65),
                ('conflict_risk', 'political_stability', 0.72),
                ('conflict_risk', 'water_stress', 0.55),
                ('oil_price', 'energy_consumption', 0.45),
                ('temperature', 'water_stress', 0.38),
                ('political_stability', 'disease_outbreaks', 0.42)
            ]
            
            for u, v, w in edges:
                G.add_edge(u, v, weight=w)
            
            # Get layout
            pos = nx.spring_layout(G, seed=42)
            
            # Create edge traces
            edge_x = []
            edge_y = []
            edge_info = []
            
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                weight = G[edge[0]][edge[1]]['weight']
                edge_info.append(f"{edge[0]} - {edge[1]}: {weight:.2f}")
            
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=2, color='lightgray'),
                hoverinfo='none',
                mode='lines'
            )
            
            # Create node traces
            node_x = []
            node_y = []
            node_text = []
            node_colors = []
            
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(node)
                
                # Color by category
                if 'oil' in node or 'energy' in node:
                    node_colors.append('blue')
                elif 'temperature' in node or 'water' in node:
                    node_colors.append('orange')
                elif 'political' in node:
                    node_colors.append('purple')
                elif 'disease' in node:
                    node_colors.append('red')
                else:
                    node_colors.append('darkred')
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                text=node_text,
                textposition='middle center',
                marker=dict(
                    size=30,
                    color=node_colors,
                    line=dict(width=2, color='white')
                ),
                hoverinfo='text'
            )
            
            fig = go.Figure(data=[edge_trace, node_trace])
            
            fig.update_layout(
                title="Variable Relationship Network",
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[
                    dict(
                        text="Node size represents centrality",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002,
                        xanchor="left", yanchor="bottom",
                        font=dict(size=12)
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating relationship network plot: {e}")
            return go.Figure()
    
    def _create_centrality_measures_plot(self, target_var):
        """Create centrality measures plot"""
        try:
            variables = ['conflict_risk', 'oil_price', 'temperature', 'political_stability', 'water_stress']
            degree_centrality = [0.8, 0.6, 0.4, 0.7, 0.5]
            betweenness_centrality = [0.9, 0.5, 0.3, 0.6, 0.4]
            eigenvector_centrality = [1.0, 0.7, 0.4, 0.8, 0.5]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=variables,
                y=degree_centrality,
                name='Degree',
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                x=variables,
                y=betweenness_centrality,
                name='Betweenness',
                marker_color='orange'
            ))
            
            fig.add_trace(go.Bar(
                x=variables,
                y=eigenvector_centrality,
                name='Eigenvector',
                marker_color='green'
            ))
            
            fig.update_layout(
                title="Network Centrality Measures",
                yaxis_title="Centrality Score",
                barmode='group',
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating centrality measures plot: {e}")
            return go.Figure()
    
    def _get_variable_options(self):
        """Get variable options for dropdowns"""
        variables = [
            'crude_oil_price', 'oil_production', 'energy_consumption', 'renewable_energy',
            'temperature_anomaly', 'precipitation_anomaly', 'drought_index',
            'democracy_index', 'political_stability', 'government_effectiveness',
            'disease_outbreaks', 'food_insecurity', 'health_expenditure',
            'water_stress', 'arable_land', 'forest_loss', 'conflict_risk'
        ]
        
        return [{'label': var.replace('_', ' ').title(), 'value': var} for var in variables]
    
    # Placeholder methods for remaining charts
    def _create_community_detection_plot(self, target_var):
        return go.Figure().add_annotation(text="Community Detection Plot", x=0.5, y=0.5)
    
    def _create_influence_paths_plot(self, target_var):
        return go.Figure().add_annotation(text="Influence Paths Plot", x=0.5, y=0.5)
    
    def _create_feature_importance_comparison(self, target_var):
        return go.Figure().add_annotation(text="Feature Importance Comparison", x=0.5, y=0.5)
    
    def _create_importance_by_category(self, target_var):
        return go.Figure().add_annotation(text="Importance by Category", x=0.5, y=0.5)
    
    def _create_feature_stability_plot(self, target_var):
        return go.Figure().add_annotation(text="Feature Stability Plot", x=0.5, y=0.5)
    
    def _create_permutation_importance_plot(self, target_var):
        return go.Figure().add_annotation(text="Permutation Importance Plot", x=0.5, y=0.5)
    
    def _create_threshold_effects_overview(self, target_var):
        return go.Figure().add_annotation(text="Threshold Effects Overview", x=0.5, y=0.5)
    
    def _create_regime_switching_plot(self, target_var):
        return go.Figure().add_annotation(text="Regime Switching Plot", x=0.5, y=0.5)
    
    def _create_threshold_distribution_plot(self, target_var):
        return go.Figure().add_annotation(text="Threshold Distribution Plot", x=0.5, y=0.5)
    
    def _create_effect_size_analysis(self, target_var):
        return go.Figure().add_annotation(text="Effect Size Analysis", x=0.5, y=0.5)
    
    def _create_interactive_scatter_plot(self):
        return go.Figure().add_annotation(text="Interactive Scatter Plot", x=0.5, y=0.5)
    
    def _create_variable_distribution_plot(self):
        return go.Figure().add_annotation(text="Variable Distribution Plot", x=0.5, y=0.5)
    
    def _create_correlation_evolution_plot(self):
        return go.Figure().add_annotation(text="Correlation Evolution Plot", x=0.5, y=0.5)
    
    def run_dashboard(self, debug: bool = False):
        """Run the dashboard server"""
        try:
            logger.info(f"Starting multivariate dashboard on port {self.port}")
            self.app.run_server(debug=debug, port=self.port, host='0.0.0.0')
            
        except Exception as e:
            logger.error(f"Error running dashboard: {e}")
            raise

# Utility function to create dashboard
def create_multivariate_dashboard(data_integrator=None, relationship_analyzer=None, port: int = 8052):
    """Create and return multivariate dashboard instance"""
    return MultivariateRelationshipDashboard(
        data_integrator=data_integrator,
        relationship_analyzer=relationship_analyzer,
        port=port
    )