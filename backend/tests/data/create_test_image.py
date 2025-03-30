"""Script to create a test image for face recognition tests."""
import cv2
import numpy as np
import os

def create_test_image():
    """Create a simple test image with a face-like shape."""
    # Create a 640x480 image with a white background
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # Draw a simple face-like shape
    # Face outline
    cv2.ellipse(img, (320, 240), (150, 200), 0, 0, 360, (200, 200, 200), -1)
    
    # Eyes
    cv2.circle(img, (250, 200), 20, (0, 0, 0), -1)
    cv2.circle(img, (390, 200), 20, (0, 0, 0), -1)
    
    # Nose
    cv2.line(img, (320, 220), (320, 280), (0, 0, 0), 2)
    
    # Mouth
    cv2.ellipse(img, (320, 300), (50, 30), 0, 0, 180, (0, 0, 0), 2)
    
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, 'test_face.jpg')
    
    # Save the image
    cv2.imwrite(output_path, img)
    print(f"Test image saved to: {output_path}")

if __name__ == '__main__':
    create_test_image() 