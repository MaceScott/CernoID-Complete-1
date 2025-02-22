from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from core.config.manager import ConfigManager
from core.events.manager import EventManager
from core.error_handling import handle_exceptions

class CernoIDServer:
    def __init__(self):
        self.config = ConfigManager()
        self.event_manager = EventManager()
        self.app = self._create_app()
        self._setup_middleware()
        self._setup_routes()

    def _create_app(self) -> FastAPI:
        return FastAPI(
            title="CernoID API",
            description="Advanced Facial Recognition Security System API",
            version="1.0.0"
        )

    def _setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get('api.cors_origins', ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @handle_exceptions(logger=server_logger.error)
    def _setup_routes(self):
        from .api_routes import router
        self.app.include_router(router, prefix="/api/v1")

    async def startup(self):
        await self.event_manager.start()
        # Additional startup tasks

    async def shutdown(self):
        # Cleanup tasks
        pass

    def run(self):
        import uvicorn
        uvicorn.run(
            self.app,
            host=self.config.get('api.host', "0.0.0.0"),
            port=self.config.get('api.port', 8000),
            reload=self.config.get('api.debug', False)
        ) 
