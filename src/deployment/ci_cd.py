from typing import Dict, List, Optional
import yaml
from pathlib import Path
import logging
from dataclasses import dataclass
import subprocess
import docker
import time

@dataclass
class PipelineStage:
    """CI/CD pipeline stage configuration"""
    name: str
    steps: List[Dict]
    environment: Dict
    dependencies: List[str]
    timeout: int = 3600

class CICDPipeline:
    """CI/CD pipeline management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('CICDPipeline')
        self.docker_client = docker.from_env()
        self._stages: Dict[str, PipelineStage] = {}
        self._results: Dict[str, Dict] = {}
        self._setup_stages()

    def _setup_stages(self) -> None:
        """Setup pipeline stages"""
        self._stages = {
            "test": PipelineStage(
                name="test",
                steps=[
                    {
                        "name": "lint",
                        "command": "pylint src/ tests/",
                        "artifacts": ["lint-report.txt"]
                    },
                    {
                        "name": "unit-tests",
                        "command": "pytest tests/unit/",
                        "artifacts": ["test-results/", "coverage/"]
                    },
                    {
                        "name": "integration-tests",
                        "command": "pytest tests/integration/",
                        "artifacts": ["integration-results/"]
                    }
                ],
                environment={
                    "PYTHONPATH": "src/",
                    "TEST_ENV": "true"
                },
                dependencies=[]
            ),
            "build": PipelineStage(
                name="build",
                steps=[
                    {
                        "name": "docker-build",
                        "command": "docker build -t cernoid:${VERSION} .",
                        "artifacts": ["build.log"]
                    },
                    {
                        "name": "security-scan",
                        "command": "trivy image cernoid:${VERSION}",
                        "artifacts": ["security-report.json"]
                    }
                ],
                environment={
                    "VERSION": "${GITHUB_SHA}"
                },
                dependencies=["test"]
            ),
            "deploy": PipelineStage(
                name="deploy",
                steps=[
                    {
                        "name": "deploy-kubernetes",
                        "command": "kubectl apply -f k8s/",
                        "artifacts": ["deploy.log"]
                    },
                    {
                        "name": "health-check",
                        "command": "python scripts/health_check.py",
                        "artifacts": ["health-report.json"]
                    }
                ],
                environment={
                    "KUBECONFIG": "/path/to/kubeconfig",
                    "ENVIRONMENT": "${DEPLOY_ENV}"
                },
                dependencies=["build"]
            )
        }

    async def run_pipeline(self, 
                          start_stage: Optional[str] = None) -> Dict:
        """Run CI/CD pipeline"""
        try:
            stages_to_run = self._get_stages_to_run(start_stage)
            
            for stage_name in stages_to_run:
                stage = self._stages[stage_name]
                
                # Check dependencies
                self._check_dependencies(stage)
                
                # Run stage
                result = await self._run_stage(stage)
                self._results[stage_name] = result
                
                # Check if stage failed
                if result["status"] != "success":
                    raise Exception(f"Stage {stage_name} failed")
                    
            return self._generate_pipeline_report()
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            raise

    async def _run_stage(self, stage: PipelineStage) -> Dict:
        """Run pipeline stage"""
        result = {
            "name": stage.name,
            "status": "failed",
            "start_time": time.time(),
            "duration": 0,
            "steps": []
        }
        
        try:
            # Setup environment
            env = {**os.environ, **stage.environment}
            
            # Run steps
            for step in stage.steps:
                step_result = await self._run_step(step, env)
                result["steps"].append(step_result)
                
                if step_result["status"] != "success":
                    return result
                    
            result["status"] = "success"
            result["duration"] = time.time() - result["start_time"]
            
        except Exception as e:
            self.logger.error(f"Stage {stage.name} failed: {str(e)}")
            result["error"] = str(e)
            
        return result

    async def _run_step(self, step: Dict, env: Dict) -> Dict:
        """Run pipeline step"""
        result = {
            "name": step["name"],
            "status": "failed",
            "output": "",
            "artifacts": []
        }
        
        try:
            # Execute command
            process = subprocess.Popen(
                step["command"],
                shell=True,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                result["status"] = "success"
                result["output"] = stdout.decode()
                
                # Collect artifacts
                for artifact in step["artifacts"]:
                    if Path(artifact).exists():
                        result["artifacts"].append(artifact)
            else:
                result["output"] = stderr.decode()
                
        except Exception as e:
            self.logger.error(f"Step {step['name']} failed: {str(e)}")
            result["error"] = str(e)
            
        return result

    def _check_dependencies(self, stage: PipelineStage) -> None:
        """Check stage dependencies"""
        for dep in stage.dependencies:
            if dep not in self._results:
                raise ValueError(f"Dependency {dep} not run before {stage.name}")
            if self._results[dep]["status"] != "success":
                raise ValueError(f"Dependency {dep} failed for {stage.name}")

    def _get_stages_to_run(self, start_stage: Optional[str]) -> List[str]:
        """Get ordered list of stages to run"""
        if not start_stage:
            return list(self._stages.keys())
            
        if start_stage not in self._stages:
            raise ValueError(f"Invalid start stage: {start_stage}")
            
        # Get all dependent stages
        stages = []
        def add_dependencies(stage_name: str):
            stage = self._stages[stage_name]
            for dep in stage.dependencies:
                if dep not in stages:
                    add_dependencies(dep)
            if stage_name not in stages:
                stages.append(stage_name)
                
        add_dependencies(start_stage)
        return stages

    def _generate_pipeline_report(self) -> Dict:
        """Generate pipeline execution report"""
        total_duration = sum(r["duration"] for r in self._results.values())
        
        report = {
            "status": "success" if all(r["status"] == "success" 
                                     for r in self._results.values()) else "failed",
            "stages": self._results,
            "total_duration": total_duration,
            "timestamp": time.time()
        }
        
        return report 