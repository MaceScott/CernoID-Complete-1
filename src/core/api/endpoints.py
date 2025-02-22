from typing import Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import jwt
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
import numpy as np
import cv2
import logging
from uuid import uuid4

from ..base import BaseComponent
from ..utils.errors import APIError

# API Models
class RecognitionRequest(BaseModel):
    image: str  # base64 encoded image
    min_confidence: float = Field(0.7, ge=0, le=1)
    return_face_data: bool = False

class RecognitionResponse(BaseModel):
    face_id: str
    confidence: float
    bbox: List[float]
    landmarks: Optional[Dict[str, List[float]]]
    attributes: Optional[Dict[str, Union[str, float]]]
    embedding: Optional[List[float]]

class SearchRequest(BaseModel):
    face_id: str
    max_results: int = Field(10, ge=1, le=100)
    min_similarity: float = Field(0.7, ge=0, le=1)

class SearchResponse(BaseModel):
    matches: List[Dict[str, Union[str, float]]]
    total_searched: int
    search_time: float

class APIEndpoints(BaseComponent):
    """REST API endpoints for face recognition system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # API settings
        self._host = config.get('api.host', 'localhost')
        self._port = config.get('api.port', 8000)
        self._debug = config.get('api.debug', False)
        
        # Security settings
        self._secret_key = config.get('api.secret_key', 'your-secret-key')
        self._token_expire = config.get('api.token_expire', 24)  # hours
        
        # Rate limiting
        self._rate_limit = config.get('api.rate_limit', 100)  # requests per minute
        self._rate_window = 60  # seconds
        
        # Initialize FastAPI
        self._app = FastAPI(
            title="Face Recognition API",
            description="API for face recognition system",
            version="1.0.0"
        )
        
        # Setup security
        self._oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        
        # Setup CORS
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
        
        # Statistics
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'active_tokens': 0
        }

    def _setup_routes(self) -> None:
        """Setup API routes"""
        try:
            # Authentication
            @self._app.post("/token")
            async def login(form_data: OAuth2PasswordRequestForm = Depends()):
                return await self._authenticate_user(form_data)
            
            # Recognition endpoints
            @self._app.post("/recognize",
                          response_model=List[RecognitionResponse])
            async def recognize_faces(
                request: RecognitionRequest,
                token: str = Depends(self._oauth2_scheme)
            ):
                return await self._recognize_faces(request)
            
            @self._app.post("/recognize/file",
                          response_model=List[RecognitionResponse])
            async def recognize_file(
                file: UploadFile = File(...),
                min_confidence: float = 0.7,
                return_face_data: bool = False,
                token: str = Depends(self._oauth2_scheme)
            ):
                return await self._recognize_file(
                    file,
                    min_confidence,
                    return_face_data
                )
            
            # Search endpoints
            @self._app.post("/search",
                          response_model=SearchResponse)
            async def search_faces(
                request: SearchRequest,
                token: str = Depends(self._oauth2_scheme)
            ):
                return await self._search_faces(request)
            
            # Management endpoints
            @self._app.get("/stats")
            async def get_statistics(
                token: str = Depends(self._oauth2_scheme)
            ):
                return await self._get_statistics()
            
            @self._app.get("/health")
            async def health_check():
                return {"status": "healthy"}
            
        except Exception as e:
            raise APIError(f"Route setup failed: {str(e)}")

    async def _authenticate_user(self,
                               form_data: OAuth2PasswordRequestForm) -> Dict:
        """Authenticate user and return token"""
        try:
            # Validate credentials (implement your auth logic)
            if not self._validate_credentials(
                form_data.username,
                form_data.password
            ):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials"
                )
            
            # Generate token
            access_token = self._create_token(
                data={"sub": form_data.username}
            )
            
            self._stats['active_tokens'] += 1
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=str(e)
            )

    def _create_token(self, data: Dict) -> str:
        """Create JWT token"""
        try:
            expiration = datetime.utcnow() + timedelta(
                hours=self._token_expire
            )
            
            data.update({"exp": expiration})
            
            return jwt.encode(
                data,
                self._secret_key,
                algorithm="HS256"
            )
            
        except Exception as e:
            raise APIError(f"Token creation failed: {str(e)}")

    async def _recognize_faces(self,
                             request: RecognitionRequest) -> List[RecognitionResponse]:
        """Process face recognition request"""
        try:
            start_time = datetime.utcnow()
            
            # Decode image
            image = self._decode_image(request.image)
            
            # Process faces
            faces = await self._process_faces(
                image,
                request.min_confidence,
                request.return_face_data
            )
            
            # Update statistics
            self._update_stats(
                success=True,
                response_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
            return faces
            
        except Exception as e:
            self._update_stats(success=False)
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    async def _recognize_file(self,
                            file: UploadFile,
                            min_confidence: float,
                            return_face_data: bool) -> List[RecognitionResponse]:
        """Process face recognition from file"""
        try:
            start_time = datetime.utcnow()
            
            # Read image file
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Process faces
            faces = await self._process_faces(
                image,
                min_confidence,
                return_face_data
            )
            
            # Update statistics
            self._update_stats(
                success=True,
                response_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
            return faces
            
        except Exception as e:
            self._update_stats(success=False)
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    async def _search_faces(self,
                          request: SearchRequest) -> SearchResponse:
        """Process face search request"""
        try:
            start_time = datetime.utcnow()
            
            # Perform search
            results = await self._search_database(
                request.face_id,
                request.max_results,
                request.min_similarity
            )
            
            search_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update statistics
            self._update_stats(
                success=True,
                response_time=search_time
            )
            
            return SearchResponse(
                matches=results,
                total_searched=len(results),
                search_time=search_time
            )
            
        except Exception as e:
            self._update_stats(success=False)
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    def _update_stats(self,
                     success: bool,
                     response_time: Optional[float] = None) -> None:
        """Update API statistics"""
        try:
            self._stats['total_requests'] += 1
            
            if success:
                self._stats['successful_requests'] += 1
            else:
                self._stats['failed_requests'] += 1
            
            if response_time is not None:
                n = self._stats['successful_requests']
                current_avg = self._stats['average_response_time']
                self._stats['average_response_time'] = (
                    (current_avg * (n - 1) + response_time) / n
                )
                
        except Exception as e:
            self.logger.error(f"Stats update failed: {str(e)}")

    async def start(self) -> None:
        """Start API server"""
        try:
            import uvicorn
            uvicorn.run(
                self._app,
                host=self._host,
                port=self._port,
                debug=self._debug
            )
        except Exception as e:
            raise APIError(f"API start failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get API statistics"""
        return self._stats.copy() 