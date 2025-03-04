"""
Data augmentation system for training pipeline.
"""
import albumentations as A
import cv2
import numpy as np
from typing import List, Tuple, Optional
import random
from pathlib import Path

class DataAugmentor:
    """
    Advanced data augmentation for face recognition
    """
    
    def __init__(self):
        # Initialize augmentation pipeline
        self.transform = A.Compose([
            A.RandomBrightnessContrast(
                brightness_limit=0.2,
                contrast_limit=0.2,
                p=0.5
            ),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            A.GaussianBlur(blur_limit=(3, 7), p=0.3),
            A.ImageCompression(
                quality_lower=85,
                quality_upper=100,
                p=0.3
            ),
            A.RandomShadow(p=0.2),
            A.RandomRotate90(p=0.2),
            A.Perspective(scale=(0.05, 0.1), p=0.3),
            A.OneOf([
                A.RandomRain(p=1.0),
                A.RandomFog(p=1.0),
                A.RandomSunFlare(p=1.0)
            ], p=0.2),
            A.ColorJitter(p=0.3)
        ])
        
        # Initialize face-specific augmentations
        self.face_transform = A.Compose([
            A.ShiftScaleRotate(
                shift_limit=0.1,
                scale_limit=0.1,
                rotate_limit=30,
                p=0.5
            ),
            A.OneOf([
                A.OpticalDistortion(p=1.0),
                A.GridDistortion(p=1.0),
                A.ElasticTransform(p=1.0)
            ], p=0.3)
        ])
        
    def augment_image(self,
                     image: np.ndarray,
                     bbox: Optional[Tuple[int, int, int, int]] = None
                     ) -> np.ndarray:
        """Apply augmentation to image."""
        try:
            augmented = self.transform(image=image)
            image = augmented["image"]
            
            if bbox is not None:
                x1, y1, x2, y2 = bbox
                face = image[y1:y2, x1:x2]
                
                augmented_face = self.face_transform(image=face)
                image[y1:y2, x1:x2] = augmented_face["image"]
                
            self.logger.debug("Image augmented successfully.")
            return image
            
        except Exception as e:
            self.logger.error(f"Augmentation error: {str(e)}")
            return image
            
    def generate_triplet(self,
                        anchor: np.ndarray,
                        positive: np.ndarray,
                        negative: np.ndarray
                        ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate augmented triplet."""
        return (
            self.augment_image(anchor),
            self.augment_image(positive),
            self.augment_image(negative)
        )
        
    def generate_batch(self,
                      images: List[np.ndarray],
                      batch_size: int
                      ) -> List[np.ndarray]:
        """Generate batch of augmented images."""
        augmented_batch = []
        
        for _ in range(batch_size):
            image = random.choice(images)
            augmented_batch.append(self.augment_image(image))
            
        return augmented_batch 