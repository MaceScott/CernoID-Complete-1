"""
Deployment automation with infrastructure management.
"""
from typing import Dict, List, Any, Optional
import asyncio
import boto3
import kubernetes
from kubernetes import client, config
import docker
import yaml
from pathlib import Path
import jinja2
import time
from datetime import datetime

from ..utils.config import get_settings
from ..utils.logging import get_logger
from ..core.security.certificates import certificate_manager

class DeploymentManager:
    """
    Advanced deployment automation system
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize clients
        self.aws_client = boto3.client('ecs')
        self.docker_client = docker.from_url(self.settings.docker_url)
        
        # Load Kubernetes config
        config.load_kube_config()
        self.k8s_client = client.CoreV1Api()
        self.k8s_apps = client.AppsV1Api()
        
        # Initialize Jinja2 environment
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("deployment/templates")
        )
        
    async def deploy_application(self,
                               version: str,
                               environment: str) -> Dict[str, Any]:
        """Deploy application to specified environment."""
        try:
            # Build and push Docker image
            image_tag = await self._build_image(version)
            
            # Update Kubernetes deployments
            await self._update_k8s_deployments(image_tag, environment)
            
            # Update services and ingress
            await self._update_k8s_services(environment)
            
            # Wait for deployment completion
            status = await self._wait_for_deployment(environment)
            
            return {
                "status": "success",
                "version": version,
                "environment": environment,
                "image": image_tag,
                "deployment_status": status
            }
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {str(e)}")
            raise
            
    async def _build_image(self, version: str) -> str:
        """Build and push Docker image."""
        try:
            # Build image
            image_tag = f"{self.settings.docker_repo}:{version}"
            
            self.docker_client.images.build(
                path=".",
                tag=image_tag,
                dockerfile="Dockerfile"
            )
            
            # Push to registry
            self.docker_client.images.push(
                repository=self.settings.docker_repo,
                tag=version
            )
            
            return image_tag
            
        except Exception as e:
            self.logger.error(f"Image build failed: {str(e)}")
            raise
            
    async def _update_k8s_deployments(self,
                                    image_tag: str,
                                    environment: str):
        """Update Kubernetes deployments."""
        try:
            # Load deployment template
            template = self.template_env.get_template(
                f"deployment-{environment}.yml.j2"
            )
            
            # Render template
            deployment_yaml = template.render(
                image=image_tag,
                environment=environment,
                settings=self.settings
            )
            
            # Apply deployment
            deployment = yaml.safe_load(deployment_yaml)
            self.k8s_apps.patch_namespaced_deployment(
                name=deployment["metadata"]["name"],
                namespace=environment,
                body=deployment
            )
            
        except Exception as e:
            self.logger.error(f"Deployment update failed: {str(e)}")
            raise
            
    async def _update_k8s_services(self, environment: str):
        """Update Kubernetes services and ingress."""
        try:
            # Load service template
            template = self.template_env.get_template(
                f"service-{environment}.yml.j2"
            )
            
            # Render template
            service_yaml = template.render(
                environment=environment,
                settings=self.settings
            )
            
            # Apply service
            service = yaml.safe_load(service_yaml)
            self.k8s_client.patch_namespaced_service(
                name=service["metadata"]["name"],
                namespace=environment,
                body=service
            )
            
        except Exception as e:
            self.logger.error(f"Service update failed: {str(e)}")
            raise
            
    async def _wait_for_deployment(self,
                                 environment: str,
                                 timeout: int = 300) -> Dict[str, Any]:
        """Wait for deployment completion."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Get deployment status
                deployment = self.k8s_apps.read_namespaced_deployment_status(
                    name=f"cernoid-{environment}",
                    namespace=environment
                )
                
                if (deployment.status.available_replicas ==
                    deployment.status.replicas):
                    return {
                        "ready": True,
                        "replicas": deployment.status.replicas,
                        "available": deployment.status.available_replicas,
                        "conditions": deployment.status.conditions
                    }
                    
                await asyncio.sleep(5)
                
            raise TimeoutError("Deployment timeout exceeded")
            
        except Exception as e:
            self.logger.error(f"Deployment status check failed: {str(e)}")
            raise
            
    async def rollback_deployment(self,
                                environment: str,
                                version: str) -> Dict[str, Any]:
        """Rollback deployment to previous version."""
        try:
            # Get previous deployment
            deployment = self.k8s_apps.read_namespaced_deployment(
                name=f"cernoid-{environment}",
                namespace=environment
            )
            
            # Update image to previous version
            deployment.spec.template.spec.containers[0].image = (
                f"{self.settings.docker_repo}:{version}"
            )
            
            # Apply rollback
            self.k8s_apps.patch_namespaced_deployment(
                name=f"cernoid-{environment}",
                namespace=environment,
                body=deployment
            )
            
            # Wait for rollback completion
            status = await self._wait_for_deployment(environment)
            
            return {
                "status": "success",
                "version": version,
                "environment": environment,
                "rollback_status": status
            }
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            raise
            
    async def cleanup(self):
        """Cleanup resources."""
        pass  # No cleanup needed for deployment manager

# Global deployment manager instance
deployment_manager = DeploymentManager() 