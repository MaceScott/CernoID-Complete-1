from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
import json
import logging

from ..base import BaseComponent
from ..utils.errors import VisualizationError

class DashboardComponent(BaseComponent):
    """Real-time visualization dashboard"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Dashboard settings
        self._port = config.get('visualization.port', 8050)
        self._debug = config.get('visualization.debug', False)
        self._theme = config.get('visualization.theme', 'darkly')
        self._refresh_interval = config.get('visualization.refresh', 5000)
        
        # Data settings
        self._max_points = config.get('visualization.max_points', 1000)
        self._history_days = config.get('visualization.history', 7)
        
        # Initialize dashboard
        self._app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.DARKLY],
            suppress_callback_exceptions=True
        )
        
        # Create layout
        self._create_layout()
        
        # Setup callbacks
        self._setup_callbacks()
        
        # Statistics
        self._stats = {
            'dashboard_views': 0,
            'active_users': 0,
            'total_updates': 0,
            'last_update': None
        }

    def _create_layout(self) -> None:
        """Create dashboard layout"""
        try:
            self._app.layout = dbc.Container([
                # Header
                dbc.Row([
                    dbc.Col([
                        html.H1("Face Recognition System Dashboard",
                               className="text-center mb-4")
                    ])
                ]),
                
                # System Status
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("System Status"),
                            dbc.CardBody([
                                html.Div(id="system-status")
                            ])
                        ])
                    ], width=12)
                ], className="mb-4"),
                
                # Performance Metrics
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Recognition Performance"),
                            dbc.CardBody([
                                dcc.Graph(id="performance-graph")
                            ])
                        ])
                    ], width=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Error Rates"),
                            dbc.CardBody([
                                dcc.Graph(id="error-graph")
                            ])
                        ])
                    ], width=6)
                ], className="mb-4"),
                
                # Resource Usage
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Resource Usage"),
                            dbc.CardBody([
                                dcc.Graph(id="resource-graph")
                            ])
                        ])
                    ], width=12)
                ], className="mb-4"),
                
                # Face Recognition Stats
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Recognition Statistics"),
                            dbc.CardBody([
                                html.Div(id="recognition-stats")
                            ])
                        ])
                    ], width=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Quality Metrics"),
                            dbc.CardBody([
                                html.Div(id="quality-metrics")
                            ])
                        ])
                    ], width=6)
                ], className="mb-4"),
                
                # Update interval
                dcc.Interval(
                    id='interval-component',
                    interval=self._refresh_interval,
                    n_intervals=0
                )
            ], fluid=True)
            
        except Exception as e:
            raise VisualizationError(f"Layout creation failed: {str(e)}")

    def _setup_callbacks(self) -> None:
        """Setup dashboard callbacks"""
        try:
            # System status callback
            @self._app.callback(
                Output("system-status", "children"),
                Input("interval-component", "n_intervals")
            )
            async def update_status(n):
                status = await self._get_system_status()
                return self._create_status_indicators(status)
            
            # Performance graph callback
            @self._app.callback(
                Output("performance-graph", "figure"),
                Input("interval-component", "n_intervals")
            )
            async def update_performance(n):
                data = await self._get_performance_data()
                return self._create_performance_plot(data)
            
            # Error graph callback
            @self._app.callback(
                Output("error-graph", "figure"),
                Input("interval-component", "n_intervals")
            )
            async def update_errors(n):
                data = await self._get_error_data()
                return self._create_error_plot(data)
            
            # Resource graph callback
            @self._app.callback(
                Output("resource-graph", "figure"),
                Input("interval-component", "n_intervals")
            )
            async def update_resources(n):
                data = await self._get_resource_data()
                return self._create_resource_plot(data)
            
            # Recognition stats callback
            @self._app.callback(
                Output("recognition-stats", "children"),
                Input("interval-component", "n_intervals")
            )
            async def update_recognition_stats(n):
                stats = await self._get_recognition_stats()
                return self._create_stats_table(stats)
            
            # Quality metrics callback
            @self._app.callback(
                Output("quality-metrics", "children"),
                Input("interval-component", "n_intervals")
            )
            async def update_quality_metrics(n):
                metrics = await self._get_quality_metrics()
                return self._create_metrics_table(metrics)
            
        except Exception as e:
            raise VisualizationError(f"Callback setup failed: {str(e)}")

    def _create_status_indicators(self, status: Dict) -> html.Div:
        """Create system status indicators"""
        try:
            indicators = []
            
            for component, active in status.items():
                color = "success" if active else "danger"
                indicators.append(
                    dbc.Badge(
                        f"{component}: {'Active' if active else 'Inactive'}",
                        color=color,
                        className="me-2"
                    )
                )
            
            return html.Div(indicators)
            
        except Exception as e:
            self.logger.error(f"Status indicator creation failed: {str(e)}")
            return html.Div("Status unavailable")

    def _create_performance_plot(self, data: pd.DataFrame) -> go.Figure:
        """Create performance plot"""
        try:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Recognition Rate", "Processing Time")
            )
            
            # Recognition rate
            fig.add_trace(
                go.Scatter(
                    x=data['timestamp'],
                    y=data['recognition_rate'],
                    mode='lines',
                    name='Recognition Rate'
                ),
                row=1, col=1
            )
            
            # Processing time
            fig.add_trace(
                go.Scatter(
                    x=data['timestamp'],
                    y=data['processing_time'],
                    mode='lines',
                    name='Processing Time'
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                height=600,
                showlegend=True,
                template='plotly_dark'
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Performance plot creation failed: {str(e)}")
            return go.Figure()

    def _create_error_plot(self, data: pd.DataFrame) -> go.Figure:
        """Create error rate plot"""
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=data['timestamp'],
                y=data['error_rate'],
                mode='lines',
                name='Error Rate',
                fill='tozeroy'
            ))
            
            fig.update_layout(
                title='System Error Rate',
                xaxis_title='Time',
                yaxis_title='Error Rate',
                template='plotly_dark'
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error plot creation failed: {str(e)}")
            return go.Figure()

    def _create_resource_plot(self, data: pd.DataFrame) -> go.Figure:
        """Create resource usage plot"""
        try:
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=("CPU Usage", "Memory Usage")
            )
            
            # CPU usage
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=data['cpu_usage'].iloc[-1],
                    title={'text': "CPU"},
                    gauge={'axis': {'range': [0, 100]}},
                    domain={'row': 0, 'column': 0}
                )
            )
            
            # Memory usage
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=data['memory_usage'].iloc[-1],
                    title={'text': "Memory"},
                    gauge={'axis': {'range': [0, 100]}},
                    domain={'row': 0, 'column': 1}
                )
            )
            
            fig.update_layout(
                height=400,
                template='plotly_dark'
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Resource plot creation failed: {str(e)}")
            return go.Figure()

    def _create_stats_table(self, stats: Dict) -> html.Table:
        """Create statistics table"""
        try:
            rows = []
            for key, value in stats.items():
                rows.append(
                    html.Tr([
                        html.Td(key.replace('_', ' ').title()),
                        html.Td(f"{value:.2f}" if isinstance(value, float) else str(value))
                    ])
                )
            
            return dbc.Table([html.Tbody(rows)], bordered=True)
            
        except Exception as e:
            self.logger.error(f"Stats table creation failed: {str(e)}")
            return html.Div("Statistics unavailable")

    async def start(self) -> None:
        """Start dashboard server"""
        try:
            self._app.run_server(
                port=self._port,
                debug=self._debug
            )
        except Exception as e:
            raise VisualizationError(f"Dashboard start failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get dashboard statistics"""
        return self._stats.copy() 