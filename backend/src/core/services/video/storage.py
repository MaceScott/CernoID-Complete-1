"""
Advanced video storage system with cloud integration and optimization.
"""
from typing import Optional, Dict, List, Any, Tuple
import cv2
import numpy as np
from pathlib import Path
import time
import asyncio
from datetime import datetime, timedelta
import json
import h5py
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore.exceptions import ClientError
from ...utils.config import get_settings
from ...utils.logging import get_logger

class VideoStorage:
    """
    Advanced video storage with multiple storage backends and optimization
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize storage paths
        self.storage_path = Path(self.settings.video_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize cloud storage
        self.s3_client = self._init_s3_client()
        
        # Initialize thread pool
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.settings.storage_threads
        )
        
        # Initialize video writer pool
        self.writers = {}
        
        # Initialize metadata storage
        self.metadata_file = self.storage_path / "metadata.h5"
        self.metadata_db = h5py.File(str(self.metadata_file), "a")
        
        # Initialize cleanup task
        if self.settings.enable_auto_cleanup:
            asyncio.create_task(self._cleanup_loop())
            
    def _init_s3_client(self) -> Optional[boto3.client]:
        """Initialize S3 client for cloud storage"""
        try:
            if self.settings.use_cloud_storage:
                return boto3.client(
                    's3',
                    aws_access_key_id=self.settings.aws_access_key,
                    aws_secret_access_key=self.settings.aws_secret_key,
                    region_name=self.settings.aws_region
                )
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {str(e)}")
        return None
        
    async def store_frame(self,
                         frame: np.ndarray,
                         camera_id: str,
                         timestamp: float,
                         metadata: Optional[Dict] = None) -> bool:
        """
        Store video frame with metadata
        
        Args:
            frame: Video frame
            camera_id: Camera identifier
            timestamp: Frame timestamp
            metadata: Optional frame metadata
            
        Returns:
            Success status
        """
        try:
            # Get or create video writer
            writer = await self._get_writer(camera_id, timestamp)
            
            # Write frame
            writer.write(frame)
            
            # Store metadata
            if metadata:
                await self._store_metadata(camera_id, timestamp, metadata)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store frame: {str(e)}")
            return False
            
    async def _get_writer(self,
                         camera_id: str,
                         timestamp: float) -> cv2.VideoWriter:
        """Get or create video writer for timestamp"""
        # Generate file path
        date_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H")
        file_path = self.storage_path / camera_id / f"{date_str}.mp4"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if writer exists
        writer_key = f"{camera_id}_{date_str}"
        if writer_key not in self.writers:
            # Create new writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(
                str(file_path),
                fourcc,
                self.settings.video_fps,
                self.settings.video_resolution,
                True
            )
            self.writers[writer_key] = writer
            
            # Schedule writer cleanup
            asyncio.create_task(
                self._cleanup_writer(writer_key, timestamp)
            )
            
        return self.writers[writer_key]
        
    async def _cleanup_writer(self,
                            writer_key: str,
                            timestamp: float):
        """Cleanup video writer after timeout"""
        try:
            # Wait for timeout
            await asyncio.sleep(self.settings.writer_timeout)
            
            # Close writer
            if writer_key in self.writers:
                self.writers[writer_key].release()
                del self.writers[writer_key]
                
            # Upload to cloud if enabled
            if self.s3_client is not None:
                await self._upload_to_cloud(writer_key, timestamp)
                
        except Exception as e:
            self.logger.error(f"Writer cleanup failed: {str(e)}")
            
    async def _store_metadata(self,
                            camera_id: str,
                            timestamp: float,
                            metadata: Dict):
        """Store frame metadata"""
        try:
            # Create metadata group
            group_name = f"{camera_id}/{int(timestamp)}"
            if group_name not in self.metadata_db:
                group = self.metadata_db.create_group(group_name)
                
                # Store metadata as attributes
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        group.attrs[key] = value
                    else:
                        # Convert complex types to JSON
                        group.attrs[key] = json.dumps(value)
                        
        except Exception as e:
            self.logger.error(f"Metadata storage failed: {str(e)}")
            
    async def _upload_to_cloud(self,
                             writer_key: str,
                             timestamp: float):
        """Upload video file to cloud storage"""
        try:
            camera_id, date_str = writer_key.split('_')
            file_path = self.storage_path / camera_id / f"{date_str}.mp4"
            
            if not file_path.exists():
                return
                
            # Generate S3 key
            s3_key = f"{camera_id}/{date_str}.mp4"
            
            # Upload file
            await asyncio.to_thread(
                self.s3_client.upload_file,
                str(file_path),
                self.settings.s3_bucket,
                s3_key
            )
            
            # Delete local file if configured
            if self.settings.delete_after_upload:
                file_path.unlink()
                
            self.logger.info(f"Uploaded {file_path} to S3")
            
        except Exception as e:
            self.logger.error(f"Cloud upload failed: {str(e)}")
            
    async def get_video_segment(self,
                              camera_id: str,
                              start_time: float,
                              end_time: float) -> Optional[str]:
        """
        Get video segment for time range
        
        Args:
            camera_id: Camera identifier
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            Path to video segment
        """
        try:
            # Generate output path
            output_path = self.storage_path / "segments" / f"{int(time.time())}.mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Find relevant video files
            start_date = datetime.fromtimestamp(start_time)
            end_date = datetime.fromtimestamp(end_time)
            
            video_files = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d_%H")
                file_path = self.storage_path / camera_id / f"{date_str}.mp4"
                
                if file_path.exists():
                    video_files.append(str(file_path))
                elif self.s3_client is not None:
                    # Try to download from S3
                    s3_key = f"{camera_id}/{date_str}.mp4"
                    try:
                        download_path = self.storage_path / "temp" / f"{date_str}.mp4"
                        download_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        await asyncio.to_thread(
                            self.s3_client.download_file,
                            self.settings.s3_bucket,
                            s3_key,
                            str(download_path)
                        )
                        video_files.append(str(download_path))
                    except ClientError:
                        pass
                        
                current_date += timedelta(hours=1)
                
            if not video_files:
                return None
                
            # Combine video files
            await self._combine_videos(
                video_files,
                str(output_path),
                start_time,
                end_time
            )
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to get video segment: {str(e)}")
            return None
            
    async def _combine_videos(self,
                            input_files: List[str],
                            output_file: str,
                            start_time: float,
                            end_time: float):
        """Combine multiple video files into a single segment"""
        try:
            # Create video reader for first file
            cap = cv2.VideoCapture(input_files[0])
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(
                output_file,
                fourcc,
                fps,
                (width, height),
                True
            )
            
            # Process each input file
            for input_file in input_files:
                cap = cv2.VideoCapture(input_file)
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    # Get frame timestamp
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    
                    # Check if frame is within time range
                    if start_time <= timestamp <= end_time:
                        writer.write(frame)
                        
                cap.release()
                
            writer.release()
            
        except Exception as e:
            self.logger.error(f"Failed to combine videos: {str(e)}")
            
    async def _cleanup_loop(self):
        """Periodic cleanup of old files"""
        while True:
            try:
                # Calculate cutoff time
                cutoff_time = time.time() - self.settings.local_retention_days * 86400
                
                # Cleanup local files
                await self._cleanup_local_files(cutoff_time)
                
                # Cleanup cloud files if enabled
                if self.s3_client is not None:
                    await self._cleanup_cloud_files(cutoff_time)
                    
                # Wait for next cleanup
                await asyncio.sleep(self.settings.cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"Cleanup loop failed: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
                
    async def _cleanup_local_files(self, cutoff_time: float):
        """Cleanup old local files"""
        try:
            for camera_dir in self.storage_path.iterdir():
                if not camera_dir.is_dir():
                    continue
                    
                for file_path in camera_dir.glob("*.mp4"):
                    # Get file timestamp from name
                    try:
                        date_str = file_path.stem
                        timestamp = datetime.strptime(date_str, "%Y%m%d_%H").timestamp()
                        
                        if timestamp < cutoff_time:
                            file_path.unlink()
                            self.logger.info(f"Deleted old file: {file_path}")
                            
                    except ValueError:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Local cleanup failed: {str(e)}")
            
    async def _cleanup_cloud_files(self, cutoff_time: float):
        """Cleanup old cloud files"""
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.settings.s3_bucket):
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    # Get file timestamp from key
                    try:
                        date_str = obj['Key'].split('/')[-1].split('.')[0]
                        timestamp = datetime.strptime(date_str, "%Y%m%d_%H").timestamp()
                        
                        if timestamp < cutoff_time:
                            self.s3_client.delete_object(
                                Bucket=self.settings.s3_bucket,
                                Key=obj['Key']
                            )
                            self.logger.info(f"Deleted old cloud file: {obj['Key']}")
                            
                    except (ValueError, IndexError):
                        continue
                        
        except Exception as e:
            self.logger.error(f"Cloud cleanup failed: {str(e)}")
            
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Close all video writers
            for writer in self.writers.values():
                writer.release()
            self.writers.clear()
            
            # Close metadata database
            self.metadata_db.close()
            
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}") 