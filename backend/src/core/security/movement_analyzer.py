from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from core.error_handling import handle_exceptions

@dataclass
class MovementPattern:
    pattern_type: str
    confidence: float
    duration: timedelta
    location: Dict[str, float]  # x, y coordinates
    velocity: Dict[str, float]  # dx, dy
    person_count: int

class MovementAnalyzer:
    def __init__(self):
        self.movement_history: Dict[int, List[MovementPattern]] = {}  # person_id -> patterns
        self.loitering_threshold = timedelta(minutes=5)
        self.velocity_threshold = 10.0  # pixels per frame for fight detection
        
    @handle_exceptions(logger=movement_logger.error)
    async def analyze_sequence(self, frame_sequence: List[np.ndarray]) -> List[Dict]:
        try:
            movement_data = []
            
            # Track movement patterns for each detected person
            tracked_objects = await self._track_objects(frame_sequence)
            
            for person_id, tracks in tracked_objects.items():
                # Analyze velocity and acceleration
                velocity = self._calculate_velocity(tracks)
                acceleration = self._calculate_acceleration(tracks)
                
                # Check for specific patterns
                patterns = await self._detect_patterns(
                    tracks, velocity, acceleration
                )
                
                if patterns:
                    movement_data.extend(patterns)
                
            movement_logger.info("Frame sequence analyzed successfully")
            return movement_data

        except Exception as e:
            movement_logger.error(f"Frame sequence analysis failed: {str(e)}")
            raise

    async def _detect_patterns(
        self, 
        tracks: List[Dict], 
        velocity: Dict[str, float], 
        acceleration: Dict[str, float]
    ) -> List[Dict]:
        patterns = []
        
        # Detect loitering
        if await self._check_loitering(tracks):
            patterns.append({
                'type': 'loitering',
                'confidence': 0.85,
                'location': tracks[-1]['location']
            })
            
        # Detect potential fights
        if await self._check_fight_behavior(velocity, acceleration):
            patterns.append({
                'type': 'fight',
                'confidence': 0.90,
                'location': tracks[-1]['location']
            })
            
        # Detect tailgating
        if await self._check_tailgating(tracks):
            patterns.append({
                'type': 'tailgating',
                'confidence': 0.95,
                'location': tracks[-1]['location']
            })
            
        return patterns

    async def _check_loitering(self, tracks: List[Dict]) -> bool:
        try:
            if len(tracks) < 2:
                return False

            start_time = tracks[0]['timestamp']
            end_time = tracks[-1]['timestamp']
            duration = end_time - start_time

            if duration >= self.loitering_threshold:
                positions = [t['location'] for t in tracks]
                max_distance = self._calculate_max_distance(positions)
                return max_distance < 100

            return False
        except Exception as e:
            movement_logger.error(f"Loitering check failed: {str(e)}")
            return False

    async def _check_fight_behavior(
        self, 
        velocity: Dict[str, float], 
        acceleration: Dict[str, float]
    ) -> bool:
        # Check for sudden movements and high acceleration
        return (abs(velocity['dx']) > self.velocity_threshold or 
                abs(velocity['dy']) > self.velocity_threshold) and \
               (abs(acceleration['dx']) > 5 or 
                abs(acceleration['dy']) > 5) 
