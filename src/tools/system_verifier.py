from typing import Dict, List
import asyncio
from datetime import datetime
from core.system.initializer import SystemInitializer
from core.error_handling import handle_exceptions

class SystemVerifier:
    def __init__(self):
        self.system = SystemInitializer()
        self.verification_results: Dict = {}
        self.required_components = [
            'face_recognition',
            'camera_system',
            'security_alerts',
            'user_management',
            'api_endpoints',
            'database',
            'mobile_integration',
            'monitoring'
        ]

    @handle_exceptions(logger=verifier_logger.error)
    async def verify_system(self) -> Dict:
        await self.system.initialize_system()
        
        verification_tasks = [
            self._verify_component(component)
            for component in self.required_components
        ]
        
        results = await asyncio.gather(*verification_tasks)
        
        self.verification_results = {
            'timestamp': datetime.utcnow(),
            'overall_status': all(r['status'] == 'operational' for r in results),
            'components': dict(zip(self.required_components, results))
        }
        
        return self.verification_results

    async def _verify_component(self, component: str) -> Dict:
        verifier = getattr(self, f'_verify_{component}')
        try:
            result = await verifier()
            return {
                'status': 'operational' if result else 'failed',
                'timestamp': datetime.utcnow(),
                'details': result
            }
        except Exception as e:
            return {
                'status': 'error',
                'timestamp': datetime.utcnow(),
                'error': str(e)
            }

    async def generate_verification_report(self):
        if not self.verification_results:
            await self.verify_system()
            
        report = {
            'summary': {
                'total_components': len(self.required_components),
                'operational': sum(1 for c in self.verification_results['components'].values() 
                                 if c['status'] == 'operational'),
                'failed': sum(1 for c in self.verification_results['components'].values() 
                            if c['status'] == 'failed'),
                'errors': sum(1 for c in self.verification_results['components'].values() 
                            if c['status'] == 'error')
            },
            'details': self.verification_results
        }
        
        return report 
