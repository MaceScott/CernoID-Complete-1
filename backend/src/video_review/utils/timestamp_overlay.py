import cv2
import numpy as np
from datetime import datetime
from typing import Union

def add_timestamp_overlay(
    frame: np.ndarray,
    timestamp: Union[datetime, float],
    position: tuple = (10, 30),
    font_scale: float = 0.7,
    thickness: int = 2
) -> np.ndarray:
    """
    Add a timestamp overlay to a video frame.
    
    Args:
        frame: The video frame to add the overlay to
        timestamp: Either a datetime object or seconds since epoch
        position: (x, y) position of the timestamp text
        font_scale: Scale of the font
        thickness: Thickness of the text
        
    Returns:
        The frame with the timestamp overlay
    """
    # Convert timestamp to datetime if it's a float
    if isinstance(timestamp, float):
        timestamp = datetime.fromtimestamp(timestamp)
        
    # Format timestamp string
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    # Get text size
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_width, text_height), _ = cv2.getTextSize(
        timestamp_str, font, font_scale, thickness
    )
    
    # Add black outline
    outline_color = (0, 0, 0)
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        cv2.putText(
            frame,
            timestamp_str,
            (position[0] + dx, position[1] + dy),
            font,
            font_scale,
            outline_color,
            thickness + 1
        )
        
    # Add white text
    cv2.putText(
        frame,
        timestamp_str,
        position,
        font,
        font_scale,
        (255, 255, 255),
        thickness
    )
    
    return frame 