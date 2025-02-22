from typing import Dict, Optional, List, Union, Callable
import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from ...base import BaseComponent
from ...utils.errors import UIError

class SettingsDialog(BaseComponent):
    """Base settings dialog"""
    
    def __init__(self, parent: tk.Widget, config: dict):
        super().__init__(config)
        self.parent = parent
        self._dialog = None
        self._widgets: Dict[str, Union[ttk.Entry, ttk.Checkbutton, ttk.Combobox]] = {}
        self._changes: Dict[str, any] = {}
        self._original: Dict[str, any] = {}

    def show(self) -> None:
        """Show settings dialog"""
        try:
            self._dialog = tk.Toplevel(self.parent)
            self._dialog.title(self._get_title())
            self._dialog.transient(self.parent)
            self._dialog.grab_set()
            
            # Create dialog content
            self._create_content()
            
            # Create action buttons
            self._create_buttons()
            
            # Center dialog
            self._center_dialog()
            
        except Exception as e:
            raise UIError(f"Dialog creation failed: {str(e)}")

    def _create_buttons(self) -> None:
        """Create dialog buttons"""
        button_frame = ttk.Frame(self._dialog)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self._save_changes
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _center_dialog(self) -> None:
        """Center dialog on parent window"""
        self._dialog.update_idletasks()
        
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self._dialog.winfo_width()
        dialog_height = self._dialog.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self._dialog.geometry(f"+{x}+{y}")

    def _create_content(self) -> None:
        """Create dialog content - override in subclasses"""
        raise NotImplementedError

    def _get_title(self) -> str:
        """Get dialog title - override in subclasses"""
        raise NotImplementedError

    async def _save_changes(self) -> None:
        """Save settings changes"""
        try:
            # Validate changes
            if not await self._validate_changes():
                return
            
            # Apply changes
            await self._apply_changes()
            
            # Close dialog
            self._dialog.destroy()
            
            # Show success message
            messagebox.showinfo(
                "Settings",
                "Settings updated successfully"
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to save settings: {str(e)}"
            )

    async def _validate_changes(self) -> bool:
        """Validate settings changes - override in subclasses"""
        return True

    async def _apply_changes(self) -> None:
        """Apply settings changes - override in subclasses"""
        raise NotImplementedError


class RecognitionSettings(SettingsDialog):
    """Recognition system settings"""
    
    def _get_title(self) -> str:
        return "Recognition Settings"

    def _create_content(self) -> None:
        """Create recognition settings content"""
        frame = ttk.LabelFrame(self._dialog, text="Face Recognition")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Confidence threshold
        row = 0
        ttk.Label(frame, text="Confidence Threshold:").grid(
            row=row, column=0, padx=5, pady=5
        )
        
        threshold = ttk.Entry(frame)
        threshold.insert(0, str(self.config.get('recognition.threshold', 0.6)))
        threshold.grid(row=row, column=1, padx=5, pady=5)
        self._widgets['threshold'] = threshold
        
        # Face size
        row += 1
        ttk.Label(frame, text="Minimum Face Size:").grid(
            row=row, column=0, padx=5, pady=5
        )
        
        face_size = ttk.Entry(frame)
        face_size.insert(0, str(self.config.get('recognition.min_face_size', 64)))
        face_size.grid(row=row, column=1, padx=5, pady=5)
        self._widgets['face_size'] = face_size
        
        # Anti-spoofing
        row += 1
        spoof_var = tk.BooleanVar(
            value=self.config.get('recognition.anti_spoofing', True)
        )
        spoof = ttk.Checkbutton(
            frame,
            text="Enable Anti-spoofing",
            variable=spoof_var
        )
        spoof.grid(row=row, column=0, columnspan=2, padx=5, pady=5)
        self._widgets['anti_spoofing'] = spoof_var
        
        # Model selection
        row += 1
        ttk.Label(frame, text="Recognition Model:").grid(
            row=row, column=0, padx=5, pady=5
        )
        
        model = ttk.Combobox(frame, values=[
            "dlib_resnet",
            "face_recognition",
            "custom_model"
        ])
        model.set(self.config.get('recognition.model', "dlib_resnet"))
        model.grid(row=row, column=1, padx=5, pady=5)
        self._widgets['model'] = model

    async def _validate_changes(self) -> bool:
        """Validate recognition settings"""
        try:
            # Validate threshold
            threshold = float(self._widgets['threshold'].get())
            if not 0 <= threshold <= 1:
                raise ValueError("Threshold must be between 0 and 1")
            
            # Validate face size
            face_size = int(self._widgets['face_size'].get())
            if face_size < 32:
                raise ValueError("Minimum face size must be at least 32 pixels")
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return False

    async def _apply_changes(self) -> None:
        """Apply recognition settings"""
        changes = {
            'recognition.threshold': float(self._widgets['threshold'].get()),
            'recognition.min_face_size': int(self._widgets['face_size'].get()),
            'recognition.anti_spoofing': self._widgets['anti_spoofing'].get(),
            'recognition.model': self._widgets['model'].get()
        }
        
        await self.app.admin.update_system_config(changes, 'admin')


class AlertSettings(SettingsDialog):
    """Alert system settings"""
    
    def _get_title(self) -> str:
        return "Alert Settings"

    def _create_content(self) -> None:
        """Create alert settings content"""
        frame = ttk.LabelFrame(self._dialog, text="Alert Configuration")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Email notifications
        row = 0
        email_var = tk.BooleanVar(
            value=self.config.get('alerts.email.enabled', True)
        )
        email = ttk.Checkbutton(
            frame,
            text="Enable Email Notifications",
            variable=email_var
        )
        email.grid(row=row, column=0, columnspan=2, padx=5, pady=5)
        self._widgets['email_enabled'] = email_var
        
        # SMS notifications
        row += 1
        sms_var = tk.BooleanVar(
            value=self.config.get('alerts.sms.enabled', True)
        )
        sms = ttk.Checkbutton(
            frame,
            text="Enable SMS Notifications",
            variable=sms_var
        )
        sms.grid(row=row, column=0, columnspan=2, padx=5, pady=5)
        self._widgets['sms_enabled'] = sms_var
        
        # Push notifications
        row += 1
        push_var = tk.BooleanVar(
            value=self.config.get('alerts.push.enabled', True)
        )
        push = ttk.Checkbutton(
            frame,
            text="Enable Push Notifications",
            variable=push_var
        )
        push.grid(row=row, column=0, columnspan=2, padx=5, pady=5)
        self._widgets['push_enabled'] = push_var
        
        # Alert levels
        row += 1
        ttk.Label(frame, text="Minimum Alert Level:").grid(
            row=row, column=0, padx=5, pady=5
        )
        
        level = ttk.Combobox(frame, values=[
            "critical",
            "high",
            "medium",
            "low"
        ])
        level.set(self.config.get('alerts.min_level', "medium"))
        level.grid(row=row, column=1, padx=5, pady=5)
        self._widgets['min_level'] = level

    async def _apply_changes(self) -> None:
        """Apply alert settings"""
        changes = {
            'alerts.email.enabled': self._widgets['email_enabled'].get(),
            'alerts.sms.enabled': self._widgets['sms_enabled'].get(),
            'alerts.push.enabled': self._widgets['push_enabled'].get(),
            'alerts.min_level': self._widgets['min_level'].get()
        }
        
        await self.app.admin.update_system_config(changes, 'admin')


class SecuritySettings(SettingsDialog):
    """Security system settings"""
    
    def _get_title(self) -> str:
        return "Security Settings"

    def _create_content(self) -> None:
        """Create security settings content"""
        frame = ttk.LabelFrame(self._dialog, text="Security Configuration")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Session timeout
        row = 0
        ttk.Label(frame, text="Session Timeout (minutes):").grid(
            row=row, column=0, padx=5, pady=5
        )
        
        timeout = ttk.Entry(frame)
        timeout.insert(0, str(self.config.get('security.session_timeout', 30)))
        timeout.grid(row=row, column=1, padx=5, pady=5)
        self._widgets['session_timeout'] = timeout
        
        # Password policy
        row += 1
        ttk.Label(frame, text="Minimum Password Length:").grid(
            row=row, column=0, padx=5, pady=5
        )
        
        pass_len = ttk.Entry(frame)
        pass_len.insert(0, str(self.config.get('security.min_password_length', 8)))
        pass_len.grid(row=row, column=1, padx=5, pady=5)
        self._widgets['min_password_length'] = pass_len
        
        # Two-factor authentication
        row += 1
        tfa_var = tk.BooleanVar(
            value=self.config.get('security.two_factor', False)
        )
        tfa = ttk.Checkbutton(
            frame,
            text="Require Two-Factor Authentication",
            variable=tfa_var
        )
        tfa.grid(row=row, column=0, columnspan=2, padx=5, pady=5)
        self._widgets['two_factor'] = tfa_var

    async def _validate_changes(self) -> bool:
        """Validate security settings"""
        try:
            # Validate timeout
            timeout = int(self._widgets['session_timeout'].get())
            if timeout < 5:
                raise ValueError("Session timeout must be at least 5 minutes")
            
            # Validate password length
            pass_len = int(self._widgets['min_password_length'].get())
            if pass_len < 8:
                raise ValueError("Minimum password length must be at least 8 characters")
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return False

    async def _apply_changes(self) -> None:
        """Apply security settings"""
        changes = {
            'security.session_timeout': int(self._widgets['session_timeout'].get()),
            'security.min_password_length': int(self._widgets['min_password_length'].get()),
            'security.two_factor': self._widgets['two_factor'].get()
        }
        
        await self.app.admin.update_system_config(changes, 'admin')


class NetworkSettings(SettingsDialog):
    """Network system settings"""
    
    def _get_title(self) -> str:
        return "Network Settings"

    def _create_content(self) -> None:
        """Create network settings content"""
        frame = ttk.LabelFrame(self._dialog, text="Network Configuration")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # API settings
        row = 0
        ttk.Label(frame, text="API Host:").grid(
            row=row, column=0, padx=5, pady=5
        )
        
        host = ttk.Entry(frame)
        host.insert(0, self.config.get('network.api_host', 'localhost'))
        host.grid(row=row, column=1, padx=5, pady=5)
        self._widgets['api_host'] = host
        
        # Port
        row += 1
        ttk.Label(frame, text="API Port:").grid(
            row=row, column=0, padx=5, pady=5
        )
        
        port = ttk.Entry(frame)
        port.insert(0, str(self.config.get('network.api_port', 8000)))
        port.grid(row=row, column=1, padx=5, pady=5)
        self._widgets['api_port'] = port
        
        # SSL/TLS
        row += 1
        ssl_var = tk.BooleanVar(
            value=self.config.get('network.use_ssl', True)
        )
        ssl = ttk.Checkbutton(
            frame,
            text="Enable SSL/TLS",
            variable=ssl_var
        )
        ssl.grid(row=row, column=0, columnspan=2, padx=5, pady=5)
        self._widgets['use_ssl'] = ssl_var

    async def _validate_changes(self) -> bool:
        """Validate network settings"""
        try:
            # Validate port
            port = int(self._widgets['api_port'].get())
            if not 1 <= port <= 65535:
                raise ValueError("Port must be between 1 and 65535")
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return False

    async def _apply_changes(self) -> None:
        """Apply network settings"""
        changes = {
            'network.api_host': self._widgets['api_host'].get(),
            'network.api_port': int(self._widgets['api_port'].get()),
            'network.use_ssl': self._widgets['use_ssl'].get()
        }
        
        await self.app.admin.update_system_config(changes, 'admin') 