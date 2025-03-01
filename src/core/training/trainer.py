from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from sklearn.model_selection import train_test_split
import wandb
from datetime import datetime
import asyncio
from pathlib import Path
import json
import logging
from tqdm import tqdm

from ..base import BaseComponent
from ..utils.errors import TrainingError

class FaceDataset(Dataset):
    """Face recognition dataset"""
    
    def __init__(self,
                 face_paths: List[str],
                 labels: List[int],
                 transform: Optional[transforms.Compose] = None):
        self.face_paths = face_paths
        self.labels = labels
        self.transform = transform

    def __len__(self) -> int:
        return len(self.face_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        # Load image
        img_path = self.face_paths[idx]
        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Apply transforms
        if self.transform:
            image = self.transform(image)
        
        return image, self.labels[idx]

class ModelTrainer(BaseComponent):
    """Advanced model training system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Training settings
        self._batch_size = config.get('training.batch_size', 32)
        self._num_epochs = config.get('training.epochs', 100)
        self._learning_rate = config.get('training.learning_rate', 0.001)
        self._weight_decay = config.get('training.weight_decay', 0.0005)
        
        # Model architecture
        self._model_type = config.get('training.model_type', 'resnet50')
        self._embedding_size = config.get('training.embedding_size', 512)
        self._num_classes = config.get('training.num_classes', 1000)
        
        # Loss functions
        self._triplet_margin = config.get('training.triplet_margin', 0.3)
        self._center_loss_weight = config.get('training.center_loss', 0.01)
        
        # Optimization
        self._use_amp = config.get('training.use_amp', True)
        self._gradient_clip = config.get('training.gradient_clip', 1.0)
        
        # Validation
        self._val_interval = config.get('training.val_interval', 5)
        self._early_stopping = config.get('training.early_stopping', 10)
        
        # Logging
        self._log_interval = config.get('training.log_interval', 100)
        self._use_wandb = config.get('training.use_wandb', True)
        
        # Initialize training
        self._initialize_training()
        
        # Statistics
        self._stats = {
            'current_epoch': 0,
            'best_accuracy': 0.0,
            'train_loss': 0.0,
            'val_loss': 0.0,
            'learning_rate': self._learning_rate,
            'training_time': 0.0
        }

    def _initialize_training(self) -> None:
        """Initialize training system"""
        try:
            # Create model
            self._model = self._create_model()
            
            # Setup loss functions
            self._setup_losses()
            
            # Initialize optimizer
            self._optimizer = optim.Adam(
                self._model.parameters(),
                lr=self._learning_rate,
                weight_decay=self._weight_decay
            )
            
            # Initialize scheduler
            self._scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                self._optimizer,
                mode='min',
                patience=5,
                factor=0.1
            )
            
            # Initialize AMP
            if self._use_amp:
                self._scaler = torch.cuda.amp.GradScaler()
            
            # Initialize WandB
            if self._use_wandb:
                self._init_wandb()
            
        except Exception as e:
            raise TrainingError(f"Training initialization failed: {str(e)}")

    def _create_model(self) -> nn.Module:
        """Create model architecture"""
        try:
            if self._model_type == 'resnet50':
                model = models.resnet50(pretrained=True)
                model.fc = nn.Sequential(
                    nn.Linear(2048, self._embedding_size),
                    nn.BatchNorm1d(self._embedding_size),
                    nn.ReLU(),
                    nn.Linear(self._embedding_size, self._num_classes)
                )
            else:
                raise ValueError(f"Unknown model type: {self._model_type}")
            
            if torch.cuda.is_available():
                model = model.cuda()
            
            return model
            
        except Exception as e:
            raise TrainingError(f"Model creation failed: {str(e)}")

    def _setup_losses(self) -> None:
        """Setup training loss functions"""
        try:
            # Classification loss
            self._ce_loss = nn.CrossEntropyLoss()
            
            # Triplet loss
            self._triplet_loss = nn.TripletMarginLoss(
                margin=self._triplet_margin
            )
            
            # Center loss
            self._center_loss = CenterLoss(
                num_classes=self._num_classes,
                feat_dim=self._embedding_size
            )
            
            if torch.cuda.is_available():
                self._ce_loss = self._ce_loss.cuda()
                self._triplet_loss = self._triplet_loss.cuda()
                self._center_loss = self._center_loss.cuda()
            
        except Exception as e:
            raise TrainingError(f"Loss setup failed: {str(e)}")

    def _init_wandb(self) -> None:
        """Initialize Weights & Biases logging"""
        try:
            wandb.init(
                project="face-recognition",
                config={
                    "model_type": self._model_type,
                    "batch_size": self._batch_size,
                    "learning_rate": self._learning_rate,
                    "epochs": self._num_epochs,
                    "embedding_size": self._embedding_size,
                    "triplet_margin": self._triplet_margin,
                    "center_loss_weight": self._center_loss_weight
                }
            )
            
        except Exception as e:
            self.logger.error(f"WandB initialization failed: {str(e)}")
            self._use_wandb = False

    async def train(self, train_data: Tuple[List[str], List[int]], val_data: Optional[Tuple[List[str], List[int]]] = None) -> None:
        try:
            train_dataset = self._prepare_dataset(train_data)
            val_dataset = self._prepare_dataset(val_data) if val_data else None

            train_loader = DataLoader(train_dataset, batch_size=self._batch_size, shuffle=True, num_workers=4, pin_memory=True)
            val_loader = DataLoader(val_dataset, batch_size=self._batch_size, shuffle=False, num_workers=4, pin_memory=True) if val_dataset else None

            best_loss = float('inf')
            patience_counter = 0
            start_time = datetime.utcnow()

            for epoch in range(self._num_epochs):
                self._stats['current_epoch'] = epoch

                train_loss = await self._train_epoch(train_loader)
                self._stats['train_loss'] = train_loss
                self.logger.info(f"Epoch {epoch}: Training loss: {train_loss}")

                if val_loader and epoch % self._val_interval == 0:
                    val_loss = await self._validate(val_loader)
                    self._stats['val_loss'] = val_loss
                    self.logger.info(f"Epoch {epoch}: Validation loss: {val_loss}")

                    self._scheduler.step(val_loss)

                    if val_loss < best_loss:
                        best_loss = val_loss
                        patience_counter = 0
                        await self._save_checkpoint(epoch, val_loss)
                    else:
                        patience_counter += 1

                    if patience_counter >= self._early_stopping:
                        self.logger.info("Early stopping triggered.")
                        break

            self.logger.info("Training completed successfully.")

        except Exception as e:
            self.logger.error(f"Training failed: {str(e)}")
            raise TrainingError(f"Training failed: {str(e)}")

    async def _train_epoch(self, train_loader: DataLoader) -> float:
        """Train one epoch"""
        self._model.train()
        total_loss = 0.0

        with tqdm(train_loader, desc=f"Epoch {self._stats['current_epoch']}") as pbar:
            for batch_idx, (images, labels) in enumerate(pbar):
                try:
                    if torch.cuda.is_available():
                        images = images.cuda()
                        labels = labels.cuda()

                    with torch.cuda.amp.autocast(enabled=self._use_amp):
                        outputs = self._model(images)
                        loss = self._ce_loss(outputs, labels)

                    self._optimizer.zero_grad()
                    if self._use_amp:
                        self._scaler.scale(loss).backward()
                        self._scaler.step(self._optimizer)
                        self._scaler.update()
                    else:
                        loss.backward()
                        self._optimizer.step()

                    total_loss += loss.item()
                    pbar.set_postfix(loss=loss.item())

                except Exception as e:
                    self.logger.error(f"Training batch {batch_idx} failed: {str(e)}")
                    raise

        avg_loss = total_loss / len(train_loader)
        self.logger.info(f"Epoch {self._stats['current_epoch']} completed with average loss: {avg_loss}")
        return avg_loss

    async def _validate(self, val_loader: DataLoader) -> float:
        """Validate model"""
        self._model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for images, labels in val_loader:
                try:
                    if torch.cuda.is_available():
                        images = images.cuda()
                        labels = labels.cuda()
                    
                    # Forward pass
                    embeddings = self._model(images)
                    logits = self._model.fc(embeddings)
                    
                    # Calculate loss
                    loss = self._ce_loss(logits, labels)
                    total_loss += loss.item()
                    
                except Exception as e:
                    self.logger.error(f"Validation batch failed: {str(e)}")
                    continue
        
        return total_loss / len(val_loader)

    def _prepare_dataset(self,
                        data: Tuple[List[str], List[int]]) -> FaceDataset:
        """Prepare dataset with augmentations"""
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ColorJitter(
                brightness=0.2,
                contrast=0.2,
                saturation=0.2
            ),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        return FaceDataset(data[0], data[1], transform)

    async def _save_checkpoint(self,
                             epoch: int,
                             val_loss: float) -> None:
        """Save model checkpoint"""
        try:
            checkpoint = {
                'epoch': epoch,
                'model_state_dict': self._model.state_dict(),
                'optimizer_state_dict': self._optimizer.state_dict(),
                'scheduler_state_dict': self._scheduler.state_dict(),
                'val_loss': val_loss,
                'stats': self._stats
            }
            
            checkpoint_dir = Path('models/checkpoints')
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            torch.save(
                checkpoint,
                checkpoint_dir / f'checkpoint_epoch_{epoch}.pt'
            )
            
        except Exception as e:
            self.logger.error(f"Checkpoint save failed: {str(e)}")

    async def _save_model(self) -> None:
        """Save final model"""
        try:
            model_dir = Path('models')
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Save model
            torch.save(
                self._model.state_dict(),
                model_dir / 'face_recognition_model.pt'
            )
            
            # Save config
            config = {
                'model_type': self._model_type,
                'embedding_size': self._embedding_size,
                'num_classes': self._num_classes,
                'stats': self._stats
            }
            
            with open(model_dir / 'model_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Model save failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get training statistics"""
        return self._stats.copy() 