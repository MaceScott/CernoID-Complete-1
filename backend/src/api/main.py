from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from core.config.manager import ConfigManager
from core.system import CernoIDSystem
from .routes import auth, recognition, admin
from core.security.middleware import SecurityMiddleware

class CernoIDAPI:
    """Main API application"""
    
    def __init__(self):
        self.config = ConfigManager().load_all()
        self.system = CernoIDSystem(self.config)
        self.security = SecurityMiddleware(self.config)
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        app = FastAPI(
            title="CernoID API",
            description="Professional Face Recognition System API",
            version="1.0.0"
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config['security']['cors']['allowed_origins'],
            allow_credentials=True,
            allow_methods=self.config['security']['cors']['allowed_methods'],
            allow_headers=["*"],
        )

        # Register routes
        app.include_router(auth.router)
        app.include_router(recognition.router)
        app.include_router(admin.router)

        # Add middleware
        @app.middleware("http")
        async def security_middleware(request: Request, call_next):
            try:
                await self.security.process_request(request)
                response: Response = await call_next(request)
                
                # Add security headers
                for key, value in request.state.security_headers.items():
                    response.headers[key] = value
                    
                return response
            except Exception as e:
                self.logger.error(f"Request processing failed: {str(e)}")
                raise

        return app

    async def startup(self):
        """Application startup handler"""
        await self.system.initialize()

    async def shutdown(self):
        """Application shutdown handler"""
        await self.system.cleanup()

# Create API instance
api = CernoIDAPI()
app = api.app

# Register startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await api.startup()

@app.on_event("shutdown")
async def shutdown_event():
    await api.shutdown() 