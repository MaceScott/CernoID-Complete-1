from typing import Dict, Optional
import yaml
from pathlib import Path
import logging
from dataclasses import dataclass

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    environment: str
    version: str
    services: Dict
    resources: Dict
    scaling: Dict
    monitoring: Dict
    security: Dict

class DeploymentManager:
    """Deployment configuration management"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.logger = logging.getLogger('DeploymentManager')
        self._configs: Dict[str, DeploymentConfig] = {}
        self._load_configurations()

    def get_config(self, environment: str) -> DeploymentConfig:
        """Get deployment configuration for environment"""
        if environment not in self._configs:
            raise ValueError(f"Configuration not found for environment: {environment}")
        return self._configs[environment]

    def validate_config(self, config: DeploymentConfig) -> bool:
        """Validate deployment configuration"""
        try:
            # Validate required services
            required_services = {"api", "database", "recognition", "redis"}
            if not all(service in config.services for service in required_services):
                raise ValueError("Missing required services")
                
            # Validate resource limits
            for service, resources in config.resources.items():
                if "cpu" not in resources or "memory" not in resources:
                    raise ValueError(f"Missing resource limits for {service}")
                    
            # Validate scaling configuration
            for service, scaling in config.scaling.items():
                if "min_replicas" not in scaling or "max_replicas" not in scaling:
                    raise ValueError(f"Invalid scaling config for {service}")
                    
            # Validate monitoring configuration
            if not all(key in config.monitoring for key in ["metrics", "logging", "alerts"]):
                raise ValueError("Invalid monitoring configuration")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {str(e)}")
            return False

    def _load_configurations(self) -> None:
        """Load deployment configurations"""
        try:
            for config_file in self.config_dir.glob("*.yaml"):
                environment = config_file.stem
                
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                config = DeploymentConfig(
                    environment=environment,
                    version=config_data['version'],
                    services=config_data['services'],
                    resources=config_data['resources'],
                    scaling=config_data['scaling'],
                    monitoring=config_data['monitoring'],
                    security=config_data['security']
                )
                
                if self.validate_config(config):
                    self._configs[environment] = config
                    self.logger.info(f"Loaded configuration for {environment}")
                    
        except Exception as e:
            self.logger.error(f"Configuration loading failed: {str(e)}")
            raise

# Example deployment configurations
DEVELOPMENT = {
    "version": "1.0.0",
    "services": {
        "api": {
            "image": "cernoid/api:latest",
            "port": 8000,
            "env": {"DEBUG": "true"}
        },
        "database": {
            "image": "postgres:13",
            "port": 5432
        },
        "recognition": {
            "image": "cernoid/recognition:latest",
            "gpu": True
        },
        "redis": {
            "image": "redis:6",
            "port": 6379
        }
    },
    "resources": {
        "api": {
            "cpu": "1",
            "memory": "1Gi"
        },
        "recognition": {
            "cpu": "2",
            "memory": "4Gi",
            "gpu": "1"
        }
    },
    "scaling": {
        "api": {
            "min_replicas": 1,
            "max_replicas": 3,
            "target_cpu_utilization": 80
        },
        "recognition": {
            "min_replicas": 1,
            "max_replicas": 2,
            "target_gpu_utilization": 80
        }
    },
    "monitoring": {
        "metrics": {
            "prometheus": True,
            "grafana": True
        },
        "logging": {
            "elasticsearch": True,
            "retention_days": 7
        },
        "alerts": {
            "email": True,
            "slack": False
        }
    },
    "security": {
        "network_policy": {
            "enabled": True,
            "whitelist_ips": []
        },
        "ssl": {
            "enabled": True,
            "cert_manager": True
        }
    }
}

PRODUCTION = {
    # Similar structure but with production-specific values
    # Add production configuration here
} 