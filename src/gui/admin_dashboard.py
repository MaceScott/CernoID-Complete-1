"""
Administrative dashboard for system management and monitoring.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
import psutil
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ..core.recognition import FaceRecognitionSystem
from ..core.storage import VideoStorage
from ..utils.config import get_settings
from ..utils.logging import get_logger
from ..services.notification import NotificationService

class AdminDashboard(tk.Toplevel):
    """
    Advanced administrative dashboard for system management
    """
    
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize services
        self.recognition_system = FaceRecognitionSystem()
        self.video_storage = VideoStorage()
        self.notification_service = NotificationService()
        
        # Configure window
        self.title("Admin Dashboard")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Initialize UI
        self._create_layout()
        
        # Start update loop
        self.running = True
        self.update_task = asyncio.create_task(self._update_loop())
        
        # Bind cleanup
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _create_layout(self):
        """Create dashboard layout"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create system tab
        self.system_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.system_tab, text="System Status")
        self._create_system_tab()
        
        # Create users tab
        self.users_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.users_tab, text="User Management")
        self._create_users_tab()
        
        # Create cameras tab
        self.cameras_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.cameras_tab, text="Camera Management")
        self._create_cameras_tab()
        
        # Create logs tab
        self.logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_tab, text="System Logs")
        self._create_logs_tab()
        
        # Create settings tab
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        self._create_settings_tab()
        
    def _create_system_tab(self):
        """Create system status tab"""
        # Create left panel for stats
        stats_frame = ttk.LabelFrame(
            self.system_tab,
            text="System Statistics"
        )
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add system stats
        self.cpu_label = ttk.Label(stats_frame, text="CPU: 0%")
        self.cpu_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.memory_label = ttk.Label(stats_frame, text="Memory: 0%")
        self.memory_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.storage_label = ttk.Label(stats_frame, text="Storage: 0%")
        self.storage_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.uptime_label = ttk.Label(stats_frame, text="Uptime: 0:00:00")
        self.uptime_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # Create right panel for graphs
        graph_frame = ttk.LabelFrame(
            self.system_tab,
            text="Performance Graphs"
        )
        graph_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add performance graphs
        self.fig, (self.cpu_ax, self.mem_ax) = plt.subplots(2, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize graph data
        self.cpu_data = []
        self.mem_data = []
        self.max_data_points = 60
        
    def _create_users_tab(self):
        """Create user management tab"""
        # Create user list
        list_frame = ttk.LabelFrame(
            self.users_tab,
            text="Registered Users"
        )
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add user list
        self.user_tree = ttk.Treeview(
            list_frame,
            columns=("ID", "Name", "Access Level", "Last Seen"),
            show="headings"
        )
        
        self.user_tree.heading("ID", text="ID")
        self.user_tree.heading("Name", text="Name")
        self.user_tree.heading("Access Level", text="Access Level")
        self.user_tree.heading("Last Seen", text="Last Seen")
        
        self.user_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.user_tree.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        
        # Create control panel
        control_frame = ttk.Frame(self.users_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="Add User",
            command=self._add_user_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Edit User",
            command=self._edit_user_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Delete User",
            command=self._delete_user_dialog
        ).pack(side=tk.LEFT, padx=5)
        
    def _create_cameras_tab(self):
        """Create camera management tab"""
        # Create camera list
        list_frame = ttk.LabelFrame(
            self.cameras_tab,
            text="Connected Cameras"
        )
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add camera list
        self.camera_tree = ttk.Treeview(
            list_frame,
            columns=("ID", "Name", "Type", "Status", "FPS"),
            show="headings"
        )
        
        self.camera_tree.heading("ID", text="ID")
        self.camera_tree.heading("Name", text="Name")
        self.camera_tree.heading("Type", text="Type")
        self.camera_tree.heading("Status", text="Status")
        self.camera_tree.heading("FPS", text="FPS")
        
        self.camera_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.camera_tree.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.camera_tree.configure(yscrollcommand=scrollbar.set)
        
        # Create control panel
        control_frame = ttk.Frame(self.cameras_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="Add Camera",
            command=self._add_camera_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Edit Camera",
            command=self._edit_camera_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Delete Camera",
            command=self._delete_camera_dialog
        ).pack(side=tk.LEFT, padx=5)
        
    def _create_logs_tab(self):
        """Create system logs tab"""
        # Create log viewer
        self.log_text = tk.Text(
            self.logs_tab,
            wrap=tk.WORD,
            width=80,
            height=20
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            self.logs_tab,
            orient=tk.VERTICAL,
            command=self.log_text.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Add control panel
        control_frame = ttk.Frame(self.logs_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="Refresh",
            command=self._refresh_logs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Clear",
            command=self._clear_logs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Export",
            command=self._export_logs
        ).pack(side=tk.LEFT, padx=5)
        
    def _create_settings_tab(self):
        """Create settings tab"""
        # Create settings form
        form_frame = ttk.LabelFrame(
            self.settings_tab,
            text="System Settings"
        )
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add settings fields
        self._add_setting_field(
            form_frame,
            "Recognition Threshold:",
            "recognition_threshold",
            0.0,
            1.0
        )
        
        self._add_setting_field(
            form_frame,
            "Anti-Spoofing Threshold:",
            "liveness_threshold",
            0.0,
            1.0
        )
        
        self._add_setting_field(
            form_frame,
            "Threat Detection Sensitivity:",
            "threat_sensitivity",
            0.0,
            1.0
        )
        
        self._add_setting_field(
            form_frame,
            "Video Retention (days):",
            "video_retention_days",
            1,
            90
        )
        
        # Add control panel
        control_frame = ttk.Frame(self.settings_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="Save",
            command=self._save_settings
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Reset",
            command=self._reset_settings
        ).pack(side=tk.LEFT, padx=5)
        
    async def _update_loop(self):
        """Update dashboard data periodically"""
        while self.running:
            try:
                # Update system stats
                self._update_system_stats()
                
                # Update performance graphs
                self._update_graphs()
                
                # Update user list
                await self._update_users()
                
                # Update camera list
                await self._update_cameras()
                
                # Update logs
                await self._update_logs()
                
                # Wait for next update
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Update loop error: {str(e)}")
                
    def _update_system_stats(self):
        """Update system statistics"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent()
            self.cpu_label.config(text=f"CPU: {cpu_percent}%")
            
            # Get memory usage
            memory = psutil.virtual_memory()
            self.memory_label.config(
                text=f"Memory: {memory.percent}%"
            )
            
            # Get storage usage
            storage = psutil.disk_usage('/')
            self.storage_label.config(
                text=f"Storage: {storage.percent}%"
            )
            
            # Get uptime
            uptime = datetime.now() - self.settings.start_time
            self.uptime_label.config(
                text=f"Uptime: {str(uptime).split('.')[0]}"
            )
            
        except Exception as e:
            self.logger.error(f"Stats update error: {str(e)}")
            
    def _update_graphs(self):
        """Update performance graphs"""
        try:
            # Update data
            self.cpu_data.append(psutil.cpu_percent())
            self.mem_data.append(psutil.virtual_memory().percent)
            
            # Limit data points
            if len(self.cpu_data) > self.max_data_points:
                self.cpu_data.pop(0)
            if len(self.mem_data) > self.max_data_points:
                self.mem_data.pop(0)
                
            # Clear axes
            self.cpu_ax.clear()
            self.mem_ax.clear()
            
            # Plot data
            self.cpu_ax.plot(self.cpu_data, 'b-')
            self.cpu_ax.set_ylabel('CPU %')
            self.cpu_ax.set_ylim(0, 100)
            
            self.mem_ax.plot(self.mem_data, 'r-')
            self.mem_ax.set_ylabel('Memory %')
            self.mem_ax.set_ylim(0, 100)
            
            # Update canvas
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Graph update error: {str(e)}")
            
    async def _update_users(self):
        """Update user list"""
        try:
            # Clear current items
            for item in self.user_tree.get_children():
                self.user_tree.delete(item)
                
            # Get user data
            users = await self.recognition_system.get_registered_users()
            
            # Add users to tree
            for user in users:
                self.user_tree.insert(
                    "",
                    tk.END,
                    values=(
                        user["id"],
                        user["name"],
                        user["access_level"],
                        user["last_seen"]
                    )
                )
                
        except Exception as e:
            self.logger.error(f"User update error: {str(e)}")
            
    async def _update_cameras(self):
        """Update camera list"""
        try:
            # Clear current items
            for item in self.camera_tree.get_children():
                self.camera_tree.delete(item)
                
            # Get camera data
            cameras = self._get_camera_config()
            
            # Add cameras to tree
            for camera in cameras:
                self.camera_tree.insert(
                    "",
                    tk.END,
                    values=(
                        camera["id"],
                        camera["name"],
                        camera["type"],
                        camera["status"],
                        camera["fps"]
                    )
                )
                
        except Exception as e:
            self.logger.error(f"Camera update error: {str(e)}")
            
    async def _update_logs(self):
        """Update system logs"""
        try:
            # Get latest logs
            logs = self._get_latest_logs()
            
            # Update text widget
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, logs)
            
        except Exception as e:
            self.logger.error(f"Log update error: {str(e)}")
            
    def _on_closing(self):
        """Clean up resources on window close"""
        self.running = False
        self.destroy()
        
    def _add_setting_field(self,
                          parent: ttk.Frame,
                          label: str,
                          setting_key: str,
                          min_val: float,
                          max_val: float):
        """Add setting field to form"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(frame, text=label).pack(side=tk.LEFT)
        
        var = tk.DoubleVar(value=getattr(self.settings, setting_key))
        scale = ttk.Scale(
            frame,
            from_=min_val,
            to=max_val,
            variable=var,
            orient=tk.HORIZONTAL
        )
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        value_label = ttk.Label(frame, text=str(var.get()))
        value_label.pack(side=tk.LEFT, padx=5)
        
        # Update value label when scale changes
        def on_change(event):
            value_label.config(text=f"{var.get():.2f}")
        scale.bind("<Motion>", on_change)
        
        # Store references
        setattr(self, f"{setting_key}_var", var)
        setattr(self, f"{setting_key}_label", value_label) 