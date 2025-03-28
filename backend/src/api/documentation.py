from typing import Dict, List, Optional, Any, Type
import inspect
from pathlib import Path
import json
import yaml
from fastapi import FastAPI, APIRouter
from fastapi.openapi.utils import get_openapi
from ..base import BaseComponent
from core.utils.decorators import handle_errors

class DocumentationManager(BaseComponent):
    """API documentation management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._docs_path = Path(self.config.get('docs.path', 'docs'))
        self._specs: Dict[str, Dict] = {}
        self._examples: Dict[str, Dict] = {}
        self._schemas: Dict[str, Dict] = {}
        
        # Documentation settings
        self._group_by_tag = self.config.get('docs.group_by_tag', True)
        self._include_examples = self.config.get('docs.include_examples', True)
        self._validate_examples = self.config.get(
            'docs.validate_examples',
            True
        )

    async def initialize(self) -> None:
        """Initialize documentation manager"""
        self._docs_path.mkdir(parents=True, exist_ok=True)
        
        # Load documentation files
        await self._load_examples()
        await self._load_schemas()

    async def cleanup(self) -> None:
        """Cleanup documentation resources"""
        self._specs.clear()
        self._examples.clear()
        self._schemas.clear()

    def generate_openapi(self,
                        app: FastAPI,
                        version: str) -> Dict:
        """Generate OpenAPI specification"""
        if version in self._specs:
            return self._specs[version]
            
        # Generate base specification
        spec = get_openapi(
            title=self.config.get('api.title', 'API Documentation'),
            version=version,
            routes=app.routes
        )
        
        # Enhance specification
        self._enhance_spec(spec, version)
        
        # Cache specification
        self._specs[version] = spec
        return spec

    def add_example(self,
                   path: str,
                   method: str,
                   example: Dict) -> None:
        """Add API endpoint example"""
        if path not in self._examples:
            self._examples[path] = {}
        self._examples[path][method.lower()] = example

    def add_schema(self,
                  name: str,
                  schema: Dict) -> None:
        """Add API schema"""
        self._schemas[name] = schema

    async def generate_markdown(self,
                              version: str,
                              spec: Dict) -> str:
        """Generate Markdown documentation"""
        docs = []
        
        # Add header
        docs.extend([
            f"# {spec['info']['title']} v{version}\n",
            f"{spec['info'].get('description', '')}\n\n"
        ])
        
        # Group endpoints by tag
        endpoints = self._group_endpoints(spec['paths'])
        
        for tag, paths in endpoints.items():
            docs.extend([
                f"## {tag}\n\n",
                self._generate_endpoints_markdown(paths)
            ])
            
        return '\n'.join(docs)

    async def save_documentation(self,
                               version: str,
                               format: str = 'json') -> None:
        """Save API documentation"""
        if version not in self._specs:
            return
            
        spec = self._specs[version]
        
        if format == 'json':
            output = json.dumps(spec, indent=2)
            ext = 'json'
        elif format == 'yaml':
            output = yaml.dump(spec)
            ext = 'yml'
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        # Save specification
        spec_file = self._docs_path / f"openapi_{version}.{ext}"
        with open(spec_file, 'w') as f:
            f.write(output)
            
        # Generate and save Markdown
        if self.config.get('docs.generate_markdown', True):
            markdown = await self.generate_markdown(version, spec)
            md_file = self._docs_path / f"api_{version}.md"
            with open(md_file, 'w') as f:
                f.write(markdown)

    async def _load_examples(self) -> None:
        """Load API examples"""
        examples_path = self._docs_path / 'examples'
        if not examples_path.exists():
            return
            
        for example_file in examples_path.glob('*.yml'):
            with open(example_file) as f:
                examples = yaml.safe_load(f)
                
            for path, methods in examples.items():
                self.add_example(path, methods)

    async def _load_schemas(self) -> None:
        """Load API schemas"""
        schemas_path = self._docs_path / 'schemas'
        if not schemas_path.exists():
            return
            
        for schema_file in schemas_path.glob('*.yml'):
            with open(schema_file) as f:
                schema = yaml.safe_load(f)
                
            self.add_schema(schema_file.stem, schema)

    def _enhance_spec(self,
                     spec: Dict,
                     version: str) -> None:
        """Enhance OpenAPI specification"""
        # Add examples
        if self._include_examples:
            for path, path_spec in spec['paths'].items():
                if path in self._examples:
                    for method, example in self._examples[path].items():
                        if method in path_spec:
                            path_spec[method]['examples'] = example

        # Add schemas
        if self._schemas:
            if 'components' not in spec:
                spec['components'] = {}
            spec['components']['schemas'] = self._schemas

        # Add security schemes
        auth_config = self.config.get('auth', {})
        if auth_config:
            if 'components' not in spec:
                spec['components'] = {}
            spec['components']['securitySchemes'] = self._get_security_schemes()

    def _group_endpoints(self,
                        paths: Dict) -> Dict[str, Dict]:
        """Group API endpoints by tag"""
        if not self._group_by_tag:
            return {'Endpoints': paths}
            
        groups = {}
        for path, methods in paths.items():
            for method_spec in methods.values():
                tags = method_spec.get('tags', ['Other'])
                for tag in tags:
                    if tag not in groups:
                        groups[tag] = {}
                    groups[tag][path] = methods
                    
        return groups

    def _generate_endpoints_markdown(self, paths: Dict) -> str:
        """Generate Markdown for endpoints"""
        docs = []
        
        for path, methods in paths.items():
            for method, spec in methods.items():
                docs.extend([
                    f"### {spec['summary']}\n",
                    f"`{method.upper()}` `{path}`\n\n",
                    f"{spec.get('description', '')}\n\n"
                ])
                
                # Add parameters
                if 'parameters' in spec:
                    docs.extend([
                        "#### Parameters\n\n",
                        "| Name | In | Type | Required | Description |\n",
                        "|------|----|----|----------|-------------|\n"
                    ])
                    
                    for param in spec['parameters']:
                        docs.append(
                            f"| {param['name']} | {param['in']} | "
                            f"{param['schema']['type']} | "
                            f"{param.get('required', False)} | "
                            f"{param.get('description', '')} |\n"
                        )
                    docs.append("\n")
                    
                # Add request body
                if 'requestBody' in spec:
                    docs.extend([
                        "#### Request Body\n\n",
                        "```json\n",
                        json.dumps(
                            spec['requestBody']['content']['application/json']['schema'],
                            indent=2
                        ),
                        "\n```\n\n"
                    ])
                    
                # Add responses
                docs.append("#### Responses\n\n")
                for status, response in spec['responses'].items():
                    docs.extend([
                        f"**{status}**\n\n",
                        f"{response.get('description', '')}\n\n"
                    ])
                    
                    if 'content' in response:
                        docs.extend([
                            "```json\n",
                            json.dumps(
                                response['content']['application/json']['schema'],
                                indent=2
                            ),
                            "\n```\n\n"
                        ])
                        
        return ''.join(docs)

    def _get_security_schemes(self) -> Dict:
        """Get API security schemes"""
        schemes = {}
        auth_config = self.config.get('auth', {})
        
        if auth_config.get('jwt', {}).get('enabled', False):
            schemes['bearerAuth'] = {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT'
            }
            
        if auth_config.get('api_key', {}).get('enabled', False):
            schemes['apiKeyAuth'] = {
                'type': 'apiKey',
                'in': 'header',
                'name': auth_config['api_key'].get('header', 'X-API-Key')
            }
            
        return schemes 