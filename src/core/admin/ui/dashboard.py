from typing import Dict, Optional, List, Union, Callable
import tkinter as tk
from tkinter import ttk
import asyncio
from datetime import datetime, timedelta
from ...base import BaseComponent
from ...utils.errors import UIError

class AdminDashboard(BaseComponent):
    """Administrative dashboard interface"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # UI components
        self._window = None
        self._frames: Dict[str, ttk.Frame] = {}
        self._widgets: Dict[str, Dict] = {}
        
        # Display settings
        self._refresh_rate = config.get('admin.ui.refresh_rate', 1000)  # 1 second
        self._max_alerts = config.get('admin.ui.max_alerts', 100)
        self._chart_history = config.get('admin.ui.chart_history', 3600)  # 1 hour
        
        # Data storage
        self._alert_history: List[Dict] = []
        self._performance_history: List[Dict] = []
        
        # Callback handlers
        self._callbacks: Dict[str, List[Callable]] = {
            'face_register': [],
            'config_update': [],
            'alert_action': []
        }

    async def initialize(self) -> None:
        """Initialize dashboard interface"""
        try:
            # Create main window
            self._window = tk.Tk()
            self._window.title("CernoID-Complete Admin Dashboard")
            self._window.state('zoomed')  # Maximize window
            
            # Create UI layout
            await self._create_layout()
            
            # Start update loop
            self._window.after(self._refresh_rate, self._update_loop)
            
        except Exception as e:
            raise UIError(f"Dashboard initialization failed: {str(e)}")

    async def _create_layout(self) -> None:
        """Create dashboard layout"""
        try:
            # Create main container
            container = ttk.Frame(self._window)
            container.pack(fill=tk.BOTH, expand=True)
            
            # Create sections
            self._create_header(container)
            self._create_sidebar(container)
            self._create_main_content(container)
            self._create_status_bar(container)
            
            # Initialize tabs
            self._initialize_tabs()
            
        except Exception as e:
            raise UIError(f"Layout creation failed: {str(e)}")

    def _create_header(self, parent: ttk.Frame) -> None:
        """Create dashboard header"""
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, padx=5, pady=5)
        
        # Title
        title = ttk.Label(
            header,
            text="CernoID-Complete Security System",
            font=('Helvetica', 16, 'bold')
        )
        title.pack(side=tk.LEFT)
        
        # User info
        self._widgets['user_info'] = ttk.Label(header, text="")
        self._widgets['user_info'].pack(side=tk.RIGHT)

    def _create_sidebar(self, parent: ttk.Frame) -> None:
        """Create navigation sidebar"""
        sidebar = ttk.Frame(parent, relief=tk.GROOVE, borderwidth=1)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self._show_dashboard),
            ("Recognition", self._show_recognition),
            ("Alerts", self._show_alerts),
            ("Users", self._show_users),
            ("Settings", self._show_settings)
        ]
        
        for text, command in nav_buttons:
            btn = ttk.Button(sidebar, text=text, command=command)
            btn.pack(fill=tk.X, padx=5, pady=2)

    def _create_main_content(self, parent: ttk.Frame) -> None:
        """Create main content area"""
        content = ttk.Frame(parent)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for tabs
        self._widgets['notebook'] = ttk.Notebook(content)
        self._widgets['notebook'].pack(fill=tk.BOTH, expand=True)
        
        # Create frames for each tab
        tab_frames = [
            'dashboard',
            'recognition',
            'alerts',
            'users',
            'settings'
        ]
        
        for frame_name in tab_frames:
            self._frames[frame_name] = ttk.Frame(
                self._widgets['notebook']
            )

    def _initialize_tabs(self) -> None:
        """Initialize tab contents"""
        # Dashboard tab
        self._initialize_dashboard_tab()
        
        # Recognition tab
        self._initialize_recognition_tab()
        
        # Alerts tab
        self._initialize_alerts_tab()
        
        # Users tab
        self._initialize_users_tab()
        
        # Settings tab
        self._initialize_settings_tab()

    def _initialize_dashboard_tab(self) -> None:
        """Initialize main dashboard tab"""
        frame = self._frames['dashboard']
        
        # System status section
        status_frame = ttk.LabelFrame(frame, text="System Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status indicators
        indicators = ['Cameras', 'Recognition', 'Alerts', 'Network']
        for i, indicator in enumerate(indicators):
            label = ttk.Label(status_frame, text=f"{indicator}:")
            label.grid(row=0, column=i*2, padx=5, pady=5)
            
            status = ttk.Label(status_frame, text="●", foreground="green")
            status.grid(row=0, column=i*2+1, padx=5, pady=5)
            self._widgets[f'status_{indicator.lower()}'] = status
        
        # Performance metrics
        metrics_frame = ttk.LabelFrame(frame, text="Performance Metrics")
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create performance charts
        self._create_performance_charts(metrics_frame)

    def _initialize_recognition_tab(self) -> None:
        """Initialize face recognition tab"""
        frame = self._frames['recognition']
        
        # Face registration section
        reg_frame = ttk.LabelFrame(frame, text="Face Registration")
        reg_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Registration form
        fields = ['Name', 'ID', 'Access Level', 'Notes']
        self._widgets['registration'] = {}
        
        for i, field in enumerate(fields):
            label = ttk.Label(reg_frame, text=f"{field}:")
            label.grid(row=i, column=0, padx=5, pady=5)
            
            entry = ttk.Entry(reg_frame)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self._widgets['registration'][field.lower()] = entry
        
        # Image capture buttons
        btn_frame = ttk.Frame(reg_frame)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        
        ttk.Button(
            btn_frame,
            text="Capture Image",
            command=self._capture_face_image
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Upload Image",
            command=self._upload_face_image
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Register",
            command=self._register_face
        ).pack(side=tk.LEFT, padx=5)

    def _initialize_alerts_tab(self) -> None:
        """Initialize alerts tab"""
        frame = self._frames['alerts']
        
        # Alert filters
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Level filter
        ttk.Label(filter_frame, text="Level:").pack(side=tk.LEFT, padx=5)
        level_var = tk.StringVar(value="All")
        level_combo = ttk.Combobox(
            filter_frame,
            textvariable=level_var,
            values=["All", "Critical", "High", "Medium", "Low"]
        )
        level_combo.pack(side=tk.LEFT, padx=5)
        self._widgets['alert_level'] = level_var
        
        # Date range
        ttk.Label(filter_frame, text="Date:").pack(side=tk.LEFT, padx=5)
        date_var = tk.StringVar(value="Today")
        date_combo = ttk.Combobox(
            filter_frame,
            textvariable=date_var,
            values=["Today", "Yesterday", "Last 7 Days", "Last 30 Days"]
        )
        date_combo.pack(side=tk.LEFT, padx=5)
        self._widgets['alert_date'] = date_var
        
        # Alert list
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ['Time', 'Level', 'Type', 'Location', 'Details']
        tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        
        self._widgets['alert_tree'] = tree

    def _initialize_users_tab(self) -> None:
        """Initialize users tab"""
        frame = self._frames['users']
        
        # User management section
        user_frame = ttk.LabelFrame(frame, text="User Management")
        user_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # User list
        list_frame = ttk.Frame(user_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ['Username', 'Role', 'Last Login', 'Status']
        tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        
        self._widgets['user_tree'] = tree
        
        # User actions
        action_frame = ttk.Frame(user_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        actions = ['Add User', 'Edit User', 'Delete User']
        for action in actions:
            ttk.Button(
                action_frame,
                text=action,
                command=getattr(self, f'_{action.lower().replace(" ", "_")}')
            ).pack(side=tk.LEFT, padx=5)

    def _initialize_settings_tab(self) -> None:
        """Initialize settings tab"""
        frame = self._frames['settings']
        
        # System settings
        settings_frame = ttk.LabelFrame(frame, text="System Settings")
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Settings categories
        categories = [
            ('Recognition', self._recognition_settings),
            ('Alerts', self._alert_settings),
            ('Security', self._security_settings),
            ('Network', self._network_settings)
        ]
        
        for i, (category, command) in enumerate(categories):
            btn = ttk.Button(settings_frame, text=category, command=command)
            btn.grid(row=i//2, column=i%2, padx=10, pady=5, sticky='ew')

    async def _update_loop(self) -> None:
        """Update dashboard data"""
        try:
            # Update system status
            await self._update_status()
            
            # Update performance metrics
            await self._update_metrics()
            
            # Update alert list
            await self._update_alerts()
            
            # Schedule next update
            self._window.after(self._refresh_rate, self._update_loop)
            
        except Exception as e:
            self.logger.error(f"Dashboard update error: {str(e)}")
            self._window.after(self._refresh_rate, self._update_loop)

    async def run(self) -> None:
        """Run dashboard interface"""
        try:
            # Initialize UI
            await self.initialize()
            
            # Start main loop
            self._window.mainloop()
            
        except Exception as e:
            raise UIError(f"Dashboard execution failed: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup dashboard resources"""
        try:
            if self._window:
                self._window.destroy()
        except Exception as e:
            self.logger.error(f"Dashboard cleanup error: {str(e)}") 