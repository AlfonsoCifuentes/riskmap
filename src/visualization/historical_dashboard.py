"""
Interactive Historical Dashboard Module
Provides comprehensive visualization capabilities for historical data analysis,
temporal and geospatial comparisons, and real-time vs historical event analysis.
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

# Geospatial visualization
import folium
from folium import plugins
import geopandas as gpd

# Statistical visualization
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

logger = logging.getLogger(__name__)

class HistoricalDashboard:
    """
    Interactive dashboard for historical data visualization and analysis
    """
    
    def __init__(self, data_source=None, port: int = 8051):
        self.data_source = data_source
        self.port = port
        self.app = None
        self.figures_cache = {}
        
        # Color schemes for different visualizations
        self.color_schemes = {
            'risk_levels': ['#2E8B57', '#FFD700', '#FF6347', '#DC143C', '#8B0000'],
            'conflict_types': px.colors.qualitative.Set3,
            'temporal': px.colors.sequential.Viridis,
            'geospatial': px.colors.sequential.Plasma
        }
        
        # Initialize Dash app
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize Dash application with layout and callbacks"""
        try:
            self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
            
            # Define app layout
            self.app.layout = self._create_layout()
            
            # Register callbacks
            self._register_callbacks()
            
            logger.info("Historical dashboard initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing dashboard: {e}")
            raise
    
    def _create_layout(self):
        """Create the main dashboard layout"""
        return dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("Historical Geopolitical Risk Analysis Dashboard", 
                           className="text-center mb-4"),
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
                                    html.Label("Time Period:"),
                                    dcc.DatePickerRange(
                                        id='date-picker-range',
                                        start_date=datetime.now() - timedelta(days=365),
                                        end_date=datetime.now(),
                                        display_format='YYYY-MM-DD'
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Region:"),
                                    dcc.Dropdown(
                                        id='region-dropdown',
                                        options=[
                                            {'label': 'Global', 'value': 'global'},
                                            {'label': 'Europe', 'value': 'europe'},
                                            {'label': 'Asia', 'value': 'asia'},
                                            {'label': 'Africa', 'value': 'africa'},
                                            {'label': 'Americas', 'value': 'americas'},
                                            {'label': 'Middle East', 'value': 'middle_east'}
                                        ],
                                        value='global'
                                    )
                                ], width=3),
                                dbc.Col([
                                    html.Label("Event Type:"),
                                    dcc.Dropdown(
                                        id='event-type-dropdown',
                                        options=[
                                            {'label': 'All Events', 'value': 'all'},
                                            {'label': 'Conflicts', 'value': 'conflict'},
                                            {'label': 'Natural Disasters', 'value': 'disaster'},
                                            {'label': 'Economic Crises', 'value': 'economic'},
                                            {'label': 'Health Emergencies', 'value': 'health'}
                                        ],
                                        value='all'
                                    )
                                ], width=3),
                                dbc.Col([
                                    html.Label("Analysis Type:"),
                                    dcc.Dropdown(
                                        id='analysis-type-dropdown',
                                        options=[
                                            {'label': 'Temporal Trends', 'value': 'temporal'},
                                            {'label': 'Geospatial Analysis', 'value': 'geospatial'},
                                            {'label': 'Comparative Analysis', 'value': 'comparative'},
                                            {'label': 'Pattern Detection', 'value': 'patterns'}
                                        ],
                                        value='temporal'
                                    )
                                ], width=2)
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
                        dcc.Tab(label="Temporal Analysis", value="temporal"),
                        dcc.Tab(label="Geospatial Analysis", value="geospatial"),
                        dcc.Tab(label="Comparative Analysis", value="comparative"),
                        dcc.Tab(label="Pattern Detection", value="patterns"),
                        dcc.Tab(label="Predictive Models", value="predictions")
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
                    html.P("Historical Geopolitical Risk Analysis System", 
                          className="text-center text-muted")
                ])
            ], className="mt-5")
            
        ], fluid=True)
    
    def _register_callbacks(self):
        """Register all dashboard callbacks"""
        
        @self.app.callback(
            Output("tab-content", "children"),
            [Input("main-tabs", "value"),
             Input("date-picker-range", "start_date"),
             Input("date-picker-range", "end_date"),
             Input("region-dropdown", "value"),
             Input("event-type-dropdown", "value"),
             Input("analysis-type-dropdown", "value")]
        )
        def update_tab_content(active_tab, start_date, end_date, region, event_type, analysis_type):
            """Update tab content based on selections"""
            try:
                if active_tab == "overview":
                    return self._create_overview_tab(start_date, end_date, region, event_type)
                elif active_tab == "temporal":
                    return self._create_temporal_tab(start_date, end_date, region, event_type)
                elif active_tab == "geospatial":
                    return self._create_geospatial_tab(start_date, end_date, region, event_type)
                elif active_tab == "comparative":
                    return self._create_comparative_tab(start_date, end_date, region, event_type)
                elif active_tab == "patterns":
                    return self._create_patterns_tab(start_date, end_date, region, event_type)
                elif active_tab == "predictions":
                    return self._create_predictions_tab(start_date, end_date, region, event_type)
                else:
                    return html.Div("Select a tab to view content")
                    
            except Exception as e:
                logger.error(f"Error updating tab content: {e}")
                return html.Div(f"Error loading content: {str(e)}")
    
    def _create_overview_tab(self, start_date, end_date, region, event_type):
        """Create overview tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Key Metrics"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.H4("1,247", className="text-primary"),
                                    html.P("Total Events")
                                ], width=3),
                                dbc.Col([
                                    html.H4("89", className="text-warning"),
                                    html.P("Active Conflicts")
                                ], width=3),
                                dbc.Col([
                                    html.H4("156", className="text-danger"),
                                    html.P("Natural Disasters")
                                ], width=3),
                                dbc.Col([
                                    html.H4("7.2", className="text-info"),
                                    html.P("Avg Risk Score")
                                ], width=3)
                            ])
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="overview-timeline",
                        figure=self._create_overview_timeline(start_date, end_date, region, event_type)
                    )
                ], width=8),
                dbc.Col([
                    dcc.Graph(
                        id="overview-distribution",
                        figure=self._create_event_distribution_chart(start_date, end_date, region, event_type)
                    )
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="overview-heatmap",
                        figure=self._create_risk_heatmap(start_date, end_date, region, event_type)
                    )
                ], width=12)
            ])
        ])
    
    def _create_temporal_tab(self, start_date, end_date, region, event_type):
        """Create temporal analysis tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Temporal Pattern Analysis"),
                        dbc.CardBody([
                            dcc.Graph(
                                id="temporal-trends",
                                figure=self._create_temporal_trends_chart(start_date, end_date, region, event_type)
                            )
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="seasonal-analysis",
                        figure=self._create_seasonal_analysis_chart(start_date, end_date, region, event_type)
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="cyclical-patterns",
                        figure=self._create_cyclical_patterns_chart(start_date, end_date, region, event_type)
                    )
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="autocorrelation",
                        figure=self._create_autocorrelation_chart(start_date, end_date, region, event_type)
                    )
                ], width=12)
            ])
        ])
    
    def _create_geospatial_tab(self, start_date, end_date, region, event_type):
        """Create geospatial analysis tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Interactive Geospatial Analysis"),
                        dbc.CardBody([
                            html.Div(
                                id="geospatial-map",
                                children=self._create_interactive_map(start_date, end_date, region, event_type)
                            )
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="geographic-distribution",
                        figure=self._create_geographic_distribution_chart(start_date, end_date, region, event_type)
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="spatial-clustering",
                        figure=self._create_spatial_clustering_chart(start_date, end_date, region, event_type)
                    )
                ], width=6)
            ])
        ])
    
    def _create_comparative_tab(self, start_date, end_date, region, event_type):
        """Create comparative analysis tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Historical vs Current Comparison"),
                        dbc.CardBody([
                            dcc.Graph(
                                id="historical-comparison",
                                figure=self._create_historical_comparison_chart(start_date, end_date, region, event_type)
                            )
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="period-comparison",
                        figure=self._create_period_comparison_chart(start_date, end_date, region, event_type)
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="regional-comparison",
                        figure=self._create_regional_comparison_chart(start_date, end_date, region, event_type)
                    )
                ], width=6)
            ])
        ])
    
    def _create_patterns_tab(self, start_date, end_date, region, event_type):
        """Create pattern detection tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Pattern Detection Results"),
                        dbc.CardBody([
                            dcc.Graph(
                                id="pattern-clusters",
                                figure=self._create_pattern_clusters_chart(start_date, end_date, region, event_type)
                            )
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="anomaly-detection",
                        figure=self._create_anomaly_detection_chart(start_date, end_date, region, event_type)
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="correlation-matrix",
                        figure=self._create_correlation_matrix_chart(start_date, end_date, region, event_type)
                    )
                ], width=6)
            ])
        ])
    
    def _create_predictions_tab(self, start_date, end_date, region, event_type):
        """Create predictions tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Predictive Model Results"),
                        dbc.CardBody([
                            dcc.Graph(
                                id="prediction-forecast",
                                figure=self._create_prediction_forecast_chart(start_date, end_date, region, event_type)
                            )
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="model-performance",
                        figure=self._create_model_performance_chart(start_date, end_date, region, event_type)
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        id="risk-scenarios",
                        figure=self._create_risk_scenarios_chart(start_date, end_date, region, event_type)
                    )
                ], width=6)
            ])
        ])
    
    def _create_overview_timeline(self, start_date, end_date, region, event_type):
        """Create overview timeline chart"""
        try:
            # Generate sample data for demonstration
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Simulate different event types
            conflicts = np.random.poisson(2, len(dates))
            disasters = np.random.poisson(1, len(dates))
            economic = np.random.poisson(0.5, len(dates))
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=conflicts,
                mode='lines+markers',
                name='Conflicts',
                line=dict(color='red', width=2),
                marker=dict(size=4)
            ))
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=disasters,
                mode='lines+markers',
                name='Natural Disasters',
                line=dict(color='orange', width=2),
                marker=dict(size=4)
            ))
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=economic,
                mode='lines+markers',
                name='Economic Events',
                line=dict(color='blue', width=2),
                marker=dict(size=4)
            ))
            
            fig.update_layout(
                title="Historical Events Timeline",
                xaxis_title="Date",
                yaxis_title="Number of Events",
                hovermode='x unified',
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating overview timeline: {e}")
            return go.Figure()
    
    def _create_event_distribution_chart(self, start_date, end_date, region, event_type):
        """Create event distribution pie chart"""
        try:
            # Sample data
            labels = ['Conflicts', 'Natural Disasters', 'Economic Crises', 'Health Emergencies', 'Other']
            values = [45, 25, 15, 10, 5]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker_colors=self.color_schemes['risk_levels']
            )])
            
            fig.update_layout(
                title="Event Type Distribution",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating event distribution chart: {e}")
            return go.Figure()
    
    def _create_risk_heatmap(self, start_date, end_date, region, event_type):
        """Create risk level heatmap"""
        try:
            # Generate sample heatmap data
            countries = ['USA', 'China', 'Russia', 'India', 'Brazil', 'Germany', 'UK', 'France', 'Japan', 'Canada']
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            # Random risk scores
            risk_data = np.random.uniform(1, 10, (len(countries), len(months)))
            
            fig = go.Figure(data=go.Heatmap(
                z=risk_data,
                x=months,
                y=countries,
                colorscale='RdYlGn_r',
                colorbar=dict(title="Risk Score")
            ))
            
            fig.update_layout(
                title="Risk Level Heatmap by Country and Month",
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating risk heatmap: {e}")
            return go.Figure()
    
    def _create_temporal_trends_chart(self, start_date, end_date, region, event_type):
        """Create temporal trends analysis chart"""
        try:
            dates = pd.date_range(start=start_date, end=end_date, freq='W')
            
            # Simulate trend data with seasonality
            trend = np.linspace(5, 7, len(dates))
            seasonal = 2 * np.sin(2 * np.pi * np.arange(len(dates)) / 52)  # Annual cycle
            noise = np.random.normal(0, 0.5, len(dates))
            risk_scores = trend + seasonal + noise
            
            # Moving averages
            ma_30 = pd.Series(risk_scores).rolling(window=4).mean()  # 4 weeks ≈ 1 month
            ma_90 = pd.Series(risk_scores).rolling(window=12).mean()  # 12 weeks ≈ 3 months
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=risk_scores,
                mode='lines',
                name='Risk Score',
                line=dict(color='lightblue', width=1),
                opacity=0.7
            ))
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=ma_30,
                mode='lines',
                name='30-day MA',
                line=dict(color='blue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=ma_90,
                mode='lines',
                name='90-day MA',
                line=dict(color='red', width=2)
            ))
            
            fig.update_layout(
                title="Temporal Risk Trends with Moving Averages",
                xaxis_title="Date",
                yaxis_title="Risk Score",
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating temporal trends chart: {e}")
            return go.Figure()
    
    def _create_seasonal_analysis_chart(self, start_date, end_date, region, event_type):
        """Create seasonal analysis chart"""
        try:
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            # Simulate seasonal patterns for different event types
            conflicts = [6.2, 5.8, 6.5, 7.1, 7.8, 8.2, 8.5, 8.1, 7.4, 6.9, 6.3, 5.9]
            disasters = [4.1, 4.5, 5.2, 6.8, 7.5, 8.9, 9.2, 8.7, 7.3, 5.8, 4.9, 4.2]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=months,
                y=conflicts,
                mode='lines+markers',
                name='Conflicts',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=months,
                y=disasters,
                mode='lines+markers',
                name='Natural Disasters',
                line=dict(color='orange', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Seasonal Risk Patterns",
                xaxis_title="Month",
                yaxis_title="Average Risk Score",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating seasonal analysis chart: {e}")
            return go.Figure()
    
    def _create_cyclical_patterns_chart(self, start_date, end_date, region, event_type):
        """Create cyclical patterns chart"""
        try:
            # Generate sample cyclical data
            days = np.arange(0, 365)
            
            # Multiple cycles
            annual_cycle = 3 * np.sin(2 * np.pi * days / 365)
            quarterly_cycle = 1.5 * np.sin(2 * np.pi * days / 90)
            monthly_cycle = 0.8 * np.sin(2 * np.pi * days / 30)
            
            combined_cycle = annual_cycle + quarterly_cycle + monthly_cycle + 5
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=days,
                y=combined_cycle,
                mode='lines',
                name='Combined Cycles',
                line=dict(color='purple', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=days,
                y=annual_cycle + 5,
                mode='lines',
                name='Annual Cycle',
                line=dict(color='blue', width=1, dash='dash'),
                opacity=0.7
            ))
            
            fig.update_layout(
                title="Cyclical Risk Patterns",
                xaxis_title="Day of Year",
                yaxis_title="Risk Score",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating cyclical patterns chart: {e}")
            return go.Figure()
    
    def _create_autocorrelation_chart(self, start_date, end_date, region, event_type):
        """Create autocorrelation analysis chart"""
        try:
            # Generate sample autocorrelation data
            lags = np.arange(0, 50)
            autocorr = np.exp(-lags / 10) * np.cos(2 * np.pi * lags / 7)  # Weekly pattern with decay
            
            # Confidence intervals
            n = 100  # Sample size
            confidence_interval = 1.96 / np.sqrt(n)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=lags,
                y=autocorr,
                name='Autocorrelation',
                marker_color=['red' if abs(ac) > confidence_interval else 'lightblue' for ac in autocorr]
            ))
            
            # Add confidence interval lines
            fig.add_hline(y=confidence_interval, line_dash="dash", line_color="red", 
                         annotation_text="95% Confidence")
            fig.add_hline(y=-confidence_interval, line_dash="dash", line_color="red")
            
            fig.update_layout(
                title="Autocorrelation Function",
                xaxis_title="Lag (days)",
                yaxis_title="Autocorrelation",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating autocorrelation chart: {e}")
            return go.Figure()
    
    def _create_interactive_map(self, start_date, end_date, region, event_type):
        """Create interactive geospatial map"""
        try:
            # Sample geographical data
            locations = [
                {'lat': 40.7128, 'lon': -74.0060, 'city': 'New York', 'risk': 6.5, 'events': 15},
                {'lat': 51.5074, 'lon': -0.1278, 'city': 'London', 'risk': 5.2, 'events': 8},
                {'lat': 35.6762, 'lon': 139.6503, 'city': 'Tokyo', 'risk': 4.8, 'events': 12},
                {'lat': 55.7558, 'lon': 37.6176, 'city': 'Moscow', 'risk': 7.8, 'events': 22},
                {'lat': 39.9042, 'lon': 116.4074, 'city': 'Beijing', 'risk': 6.1, 'events': 18},
                {'lat': 28.6139, 'lon': 77.2090, 'city': 'New Delhi', 'risk': 8.2, 'events': 28},
                {'lat': -23.5505, 'lon': -46.6333, 'city': 'São Paulo', 'risk': 7.1, 'events': 19},
                {'lat': 30.0444, 'lon': 31.2357, 'city': 'Cairo', 'risk': 8.9, 'events': 35}
            ]
            
            fig = go.Figure()
            
            # Add scatter points for events
            fig.add_trace(go.Scattergeo(
                lon=[loc['lon'] for loc in locations],
                lat=[loc['lat'] for loc in locations],
                text=[f"{loc['city']}<br>Risk: {loc['risk']}<br>Events: {loc['events']}" for loc in locations],
                mode='markers',
                marker=dict(
                    size=[loc['risk'] * 3 for loc in locations],
                    color=[loc['risk'] for loc in locations],
                    colorscale='RdYlGn_r',
                    colorbar=dict(title="Risk Score"),
                    sizemode='diameter',
                    opacity=0.8,
                    line=dict(width=1, color='white')
                ),
                name='Risk Locations'
            ))
            
            fig.update_layout(
                title="Global Risk Distribution",
                geo=dict(
                    projection_type='natural earth',
                    showland=True,
                    landcolor='lightgray',
                    showocean=True,
                    oceancolor='lightblue',
                    showlakes=True,
                    lakecolor='lightblue'
                ),
                height=500
            )
            
            return dcc.Graph(figure=fig)
            
        except Exception as e:
            logger.error(f"Error creating interactive map: {e}")
            return html.Div("Error loading map")
    
    def _create_geographic_distribution_chart(self, start_date, end_date, region, event_type):
        """Create geographic distribution chart"""
        try:
            regions = ['North America', 'Europe', 'Asia', 'Africa', 'South America', 'Oceania']
            event_counts = [45, 38, 67, 89, 23, 8]
            
            fig = go.Figure(data=[go.Bar(
                x=regions,
                y=event_counts,
                marker_color=self.color_schemes['conflict_types'][:len(regions)]
            )])
            
            fig.update_layout(
                title="Events by Geographic Region",
                xaxis_title="Region",
                yaxis_title="Number of Events",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating geographic distribution chart: {e}")
            return go.Figure()
    
    def _create_spatial_clustering_chart(self, start_date, end_date, region, event_type):
        """Create spatial clustering visualization"""
        try:
            # Generate sample clustering data
            np.random.seed(42)
            n_points = 100
            
            # Create 3 clusters
            cluster1 = np.random.multivariate_normal([40, -100], [[10, 0], [0, 10]], 30)
            cluster2 = np.random.multivariate_normal([50, 10], [[8, 0], [0, 8]], 35)
            cluster3 = np.random.multivariate_normal([30, 30], [[12, 0], [0, 12]], 35)
            
            all_points = np.vstack([cluster1, cluster2, cluster3])
            labels = [0] * 30 + [1] * 35 + [2] * 35
            
            colors = ['red', 'blue', 'green']
            
            fig = go.Figure()
            
            for i, color in enumerate(colors):
                cluster_points = all_points[np.array(labels) == i]
                fig.add_trace(go.Scatter(
                    x=cluster_points[:, 1],
                    y=cluster_points[:, 0],
                    mode='markers',
                    name=f'Cluster {i+1}',
                    marker=dict(color=color, size=8, opacity=0.7)
                ))
            
            fig.update_layout(
                title="Spatial Event Clustering",
                xaxis_title="Longitude",
                yaxis_title="Latitude",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating spatial clustering chart: {e}")
            return go.Figure()
    
    def _create_historical_comparison_chart(self, start_date, end_date, region, event_type):
        """Create historical vs current comparison chart"""
        try:
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            # Historical average (last 10 years)
            historical_avg = [5.2, 5.1, 5.8, 6.2, 6.8, 7.1, 7.5, 7.2, 6.9, 6.3, 5.7, 5.4]
            
            # Current year
            current_year = [6.1, 5.9, 6.8, 7.5, 8.2, 8.8, 9.1, 8.7, 8.2, 7.6, 6.9, 6.2]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=months,
                y=historical_avg,
                mode='lines+markers',
                name='Historical Average (10 years)',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            ))
            
            fig.add_trace(go.Scatter(
                x=months,
                y=current_year,
                mode='lines+markers',
                name='Current Year',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Historical vs Current Risk Comparison",
                xaxis_title="Month",
                yaxis_title="Risk Score",
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating historical comparison chart: {e}")
            return go.Figure()
    
    def _create_period_comparison_chart(self, start_date, end_date, region, event_type):
        """Create period comparison chart"""
        try:
            periods = ['2020-2021', '2021-2022', '2022-2023', '2023-2024']
            conflicts = [45, 52, 48, 61]
            disasters = [23, 28, 35, 31]
            economic = [12, 18, 22, 19]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=periods,
                y=conflicts,
                name='Conflicts',
                marker_color='red'
            ))
            
            fig.add_trace(go.Bar(
                x=periods,
                y=disasters,
                name='Natural Disasters',
                marker_color='orange'
            ))
            
            fig.add_trace(go.Bar(
                x=periods,
                y=economic,
                name='Economic Crises',
                marker_color='blue'
            ))
            
            fig.update_layout(
                title="Event Comparison by Period",
                xaxis_title="Period",
                yaxis_title="Number of Events",
                barmode='group',
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating period comparison chart: {e}")
            return go.Figure()
    
    def _create_regional_comparison_chart(self, start_date, end_date, region, event_type):
        """Create regional comparison chart"""
        try:
            regions = ['Europe', 'Asia', 'Africa', 'Americas', 'Middle East']
            risk_scores = [5.2, 6.8, 8.1, 6.3, 8.9]
            event_counts = [45, 78, 92, 56, 67]
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(x=regions, y=risk_scores, name="Risk Score", marker_color='lightblue'),
                secondary_y=False,
            )
            
            fig.add_trace(
                go.Scatter(x=regions, y=event_counts, mode='lines+markers', 
                          name="Event Count", line=dict(color='red', width=3)),
                secondary_y=True,
            )
            
            fig.update_xaxes(title_text="Region")
            fig.update_yaxes(title_text="Risk Score", secondary_y=False)
            fig.update_yaxes(title_text="Event Count", secondary_y=True)
            
            fig.update_layout(
                title="Regional Risk and Event Comparison",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating regional comparison chart: {e}")
            return go.Figure()
    
    def _create_pattern_clusters_chart(self, start_date, end_date, region, event_type):
        """Create pattern clusters visualization"""
        try:
            # Generate sample clustering data
            np.random.seed(42)
            
            # Create sample data with different patterns
            n_samples = 200
            features = np.random.randn(n_samples, 2)
            
            # Add some structure
            features[:50] += [2, 2]  # Cluster 1
            features[50:100] += [-2, 2]  # Cluster 2
            features[100:150] += [0, -2]  # Cluster 3
            
            # Simulate cluster labels
            labels = [0] * 50 + [1] * 50 + [2] * 50 + [3] * 50
            
            colors = ['red', 'blue', 'green', 'orange']
            
            fig = go.Figure()
            
            for i, color in enumerate(colors):
                cluster_points = features[np.array(labels) == i]
                fig.add_trace(go.Scatter(
                    x=cluster_points[:, 0],
                    y=cluster_points[:, 1],
                    mode='markers',
                    name=f'Pattern {i+1}',
                    marker=dict(color=color, size=8, opacity=0.7)
                ))
            
            fig.update_layout(
                title="Detected Event Patterns",
                xaxis_title="Feature 1",
                yaxis_title="Feature 2",
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating pattern clusters chart: {e}")
            return go.Figure()
    
    def _create_anomaly_detection_chart(self, start_date, end_date, region, event_type):
        """Create anomaly detection visualization"""
        try:
            # Generate sample time series with anomalies
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Normal pattern with some anomalies
            normal_data = 5 + 2 * np.sin(2 * np.pi * np.arange(len(dates)) / 30) + np.random.normal(0, 0.5, len(dates))
            
            # Inject anomalies
            anomaly_indices = np.random.choice(len(dates), size=int(len(dates) * 0.05), replace=False)
            anomaly_data = normal_data.copy()
            anomaly_data[anomaly_indices] += np.random.choice([-3, 3], size=len(anomaly_indices))
            
            fig = go.Figure()
            
            # Normal points
            normal_mask = np.ones(len(dates), dtype=bool)
            normal_mask[anomaly_indices] = False
            
            fig.add_trace(go.Scatter(
                x=dates[normal_mask],
                y=anomaly_data[normal_mask],
                mode='markers',
                name='Normal Events',
                marker=dict(color='blue', size=4)
            ))
            
            # Anomalous points
            fig.add_trace(go.Scatter(
                x=dates[anomaly_indices],
                y=anomaly_data[anomaly_indices],
                mode='markers',
                name='Anomalies',
                marker=dict(color='red', size=8, symbol='x')
            ))
            
            fig.update_layout(
                title="Anomaly Detection Results",
                xaxis_title="Date",
                yaxis_title="Risk Score",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating anomaly detection chart: {e}")
            return go.Figure()
    
    def _create_correlation_matrix_chart(self, start_date, end_date, region, event_type):
        """Create correlation matrix heatmap"""
        try:
            # Sample correlation matrix
            variables = ['Conflicts', 'Disasters', 'Economic', 'Political', 'Social', 'Environmental']
            
            # Generate sample correlation matrix
            np.random.seed(42)
            corr_matrix = np.random.rand(len(variables), len(variables))
            corr_matrix = (corr_matrix + corr_matrix.T) / 2  # Make symmetric
            np.fill_diagonal(corr_matrix, 1)  # Diagonal = 1
            
            # Make it more realistic
            corr_matrix = corr_matrix * 0.8 - 0.4  # Scale to [-0.4, 0.4] then add diagonal
            
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
            logger.error(f"Error creating correlation matrix chart: {e}")
            return go.Figure()
    
    def _create_prediction_forecast_chart(self, start_date, end_date, region, event_type):
        """Create prediction forecast visualization"""
        try:
            # Historical data
            hist_dates = pd.date_range(start=start_date, end=end_date, freq='D')
            hist_data = 5 + 2 * np.sin(2 * np.pi * np.arange(len(hist_dates)) / 365) + np.random.normal(0, 0.5, len(hist_dates))
            
            # Future predictions
            future_dates = pd.date_range(start=end_date + timedelta(days=1), periods=30, freq='D')
            future_trend = 5.5 + 2 * np.sin(2 * np.pi * np.arange(len(hist_dates), len(hist_dates) + 30) / 365)
            future_data = future_trend + np.random.normal(0, 0.3, len(future_dates))
            
            # Confidence intervals
            upper_bound = future_data + 1.96 * 0.5
            lower_bound = future_data - 1.96 * 0.5
            
            fig = go.Figure()
            
            # Historical data
            fig.add_trace(go.Scatter(
                x=hist_dates,
                y=hist_data,
                mode='lines',
                name='Historical Data',
                line=dict(color='blue', width=2)
            ))
            
            # Predictions
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=future_data,
                mode='lines',
                name='Predictions',
                line=dict(color='red', width=2)
            ))
            
            # Confidence interval
            fig.add_trace(go.Scatter(
                x=np.concatenate([future_dates, future_dates[::-1]]),
                y=np.concatenate([upper_bound, lower_bound[::-1]]),
                fill='toself',
                fillcolor='rgba(255,0,0,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='95% Confidence Interval'
            ))
            
            fig.update_layout(
                title="Risk Forecast with Confidence Intervals",
                xaxis_title="Date",
                yaxis_title="Risk Score",
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating prediction forecast chart: {e}")
            return go.Figure()
    
    def _create_model_performance_chart(self, start_date, end_date, region, event_type):
        """Create model performance comparison chart"""
        try:
            models = ['Prophet', 'LSTM', 'ARIMA', 'Random Forest', 'Ensemble']
            metrics = ['MAE', 'RMSE', 'R²']
            
            # Sample performance data
            performance_data = {
                'Prophet': [0.85, 1.12, 0.78],
                'LSTM': [0.72, 0.95, 0.85],
                'ARIMA': [0.91, 1.25, 0.71],
                'Random Forest': [0.68, 0.88, 0.87],
                'Ensemble': [0.65, 0.82, 0.89]
            }
            
            fig = go.Figure()
            
            for i, metric in enumerate(metrics):
                values = [performance_data[model][i] for model in models]
                fig.add_trace(go.Bar(
                    x=models,
                    y=values,
                    name=metric,
                    yaxis=f'y{i+1}' if i > 0 else 'y'
                ))
            
            fig.update_layout(
                title="Model Performance Comparison",
                xaxis_title="Model",
                height=400,
                barmode='group'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating model performance chart: {e}")
            return go.Figure()
    
    def _create_risk_scenarios_chart(self, start_date, end_date, region, event_type):
        """Create risk scenarios visualization"""
        try:
            dates = pd.date_range(start=datetime.now(), periods=30, freq='D')
            
            # Different scenarios
            optimistic = 4 + 0.5 * np.sin(2 * np.pi * np.arange(30) / 30) + np.random.normal(0, 0.2, 30)
            realistic = 6 + 1 * np.sin(2 * np.pi * np.arange(30) / 30) + np.random.normal(0, 0.3, 30)
            pessimistic = 8 + 1.5 * np.sin(2 * np.pi * np.arange(30) / 30) + np.random.normal(0, 0.4, 30)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=optimistic,
                mode='lines',
                name='Optimistic (20%)',
                line=dict(color='green', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=realistic,
                mode='lines',
                name='Realistic (60%)',
                line=dict(color='blue', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=pessimistic,
                mode='lines',
                name='Pessimistic (20%)',
                line=dict(color='red', width=2)
            ))
            
            fig.update_layout(
                title="Risk Scenarios (30-day forecast)",
                xaxis_title="Date",
                yaxis_title="Risk Score",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating risk scenarios chart: {e}")
            return go.Figure()
    
    def run_dashboard(self, debug: bool = False):
        """Run the dashboard server"""
        try:
            logger.info(f"Starting historical dashboard on port {self.port}")
            self.app.run_server(debug=debug, port=self.port, host='0.0.0.0')
            
        except Exception as e:
            logger.error(f"Error running dashboard: {e}")
            raise

# Utility function to create and run dashboard
def create_historical_dashboard(data_source=None, port: int = 8051):
    """
    Create and return a historical dashboard instance
    
    Args:
        data_source: Data source for the dashboard
        port: Port to run the dashboard on
        
    Returns:
        HistoricalDashboard instance
    """
    return HistoricalDashboard(data_source=data_source, port=port)