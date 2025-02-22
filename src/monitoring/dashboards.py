from typing import Dict, List, Optional
import json
from pathlib import Path
import logging
from dataclasses import dataclass
import grafanalib.core as G
from grafanalib._gen import DashboardEncoder

@dataclass
class Dashboard:
    """Grafana dashboard configuration"""
    title: str
    panels: List[Dict]
    variables: Optional[List[Dict]] = None
    refresh: str = "1m"
    tags: List[str] = None

class DashboardManager:
    """Monitoring dashboard management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('DashboardManager')
        self.output_dir = Path(config['dashboard_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._dashboards: Dict[str, Dashboard] = {}
        self._setup_dashboards()

    def _setup_dashboards(self) -> None:
        """Setup monitoring dashboards"""
        # System Overview Dashboard
        self._dashboards['system_overview'] = Dashboard(
            title="System Overview",
            panels=self._create_system_panels(),
            variables=[
                {
                    "name": "environment",
                    "type": "custom",
                    "options": ["production", "staging", "development"]
                }
            ],
            tags=["overview", "system"]
        )
        
        # Recognition Performance Dashboard
        self._dashboards['recognition_performance'] = Dashboard(
            title="Recognition Performance",
            panels=self._create_recognition_panels(),
            variables=[
                {
                    "name": "model_version",
                    "type": "query",
                    "query": "SELECT version FROM model_versions"
                }
            ],
            tags=["recognition", "performance"]
        )
        
        # API Metrics Dashboard
        self._dashboards['api_metrics'] = Dashboard(
            title="API Metrics",
            panels=self._create_api_panels(),
            refresh="30s",
            tags=["api", "metrics"]
        )
        
        # Security Monitoring Dashboard
        self._dashboards['security_monitoring'] = Dashboard(
            title="Security Monitoring",
            panels=self._create_security_panels(),
            refresh="1m",
            tags=["security"]
        )

    def _create_system_panels(self) -> List[Dict]:
        """Create system overview panels"""
        return [
            G.Row(
                title="System Resources",
                panels=[
                    G.Graph(
                        title="CPU Usage",
                        dataSource="prometheus",
                        targets=[
                            G.Target(
                                expr='sum(rate(container_cpu_usage_seconds_total{namespace="cernoid"}[5m])) by (pod)',
                                legendFormat="{{pod}}"
                            )
                        ],
                        yAxes=G.YAxes(
                            left=G.YAxis(format="percent", min=0, max=100)
                        )
                    ),
                    G.Graph(
                        title="Memory Usage",
                        dataSource="prometheus",
                        targets=[
                            G.Target(
                                expr='sum(container_memory_usage_bytes{namespace="cernoid"}) by (pod)',
                                legendFormat="{{pod}}"
                            )
                        ],
                        yAxes=G.YAxes(
                            left=G.YAxis(format="bytes", min=0)
                        )
                    )
                ]
            ),
            G.Row(
                title="Application Metrics",
                panels=[
                    G.Graph(
                        title="Request Rate",
                        dataSource="prometheus",
                        targets=[
                            G.Target(
                                expr='sum(rate(http_requests_total{namespace="cernoid"}[5m])) by (service)',
                                legendFormat="{{service}}"
                            )
                        ]
                    ),
                    G.Graph(
                        title="Error Rate",
                        dataSource="prometheus",
                        targets=[
                            G.Target(
                                expr='sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)',
                                legendFormat="{{service}}"
                            )
                        ]
                    )
                ]
            )
        ]

    def _create_recognition_panels(self) -> List[Dict]:
        """Create recognition performance panels"""
        return [
            G.Row(
                title="Recognition Metrics",
                panels=[
                    G.Graph(
                        title="Recognition Accuracy",
                        dataSource="prometheus",
                        targets=[
                            G.Target(
                                expr='recognition_accuracy_percent',
                                legendFormat="Accuracy"
                            )
                        ],
                        yAxes=G.YAxes(
                            left=G.YAxis(format="percent", min=0, max=100)
                        )
                    ),
                    G.Graph(
                        title="Processing Time",
                        dataSource="prometheus",
                        targets=[
                            G.Target(
                                expr='recognition_processing_seconds',
                                legendFormat="Processing Time"
                            )
                        ]
                    )
                ]
            )
        ]

    def generate_dashboards(self) -> None:
        """Generate Grafana dashboard JSON files"""
        try:
            for name, dashboard in self._dashboards.items():
                dashboard_json = self._create_dashboard_json(dashboard)
                
                output_file = self.output_dir / f"{name}.json"
                with open(output_file, 'w') as f:
                    json.dump(dashboard_json, f, cls=DashboardEncoder)
                    
                self.logger.info(f"Generated dashboard: {name}")
                
        except Exception as e:
            self.logger.error(f"Dashboard generation failed: {str(e)}")
            raise

    def _create_dashboard_json(self, dashboard: Dashboard) -> Dict:
        """Create Grafana dashboard JSON"""
        return {
            "dashboard": {
                "id": None,
                "title": dashboard.title,
                "tags": dashboard.tags or [],
                "timezone": "browser",
                "refresh": dashboard.refresh,
                "schemaVersion": 21,
                "version": 0,
                "panels": dashboard.panels,
                "templating": {
                    "list": dashboard.variables or []
                }
            },
            "folderId": 0,
            "overwrite": True
        } 