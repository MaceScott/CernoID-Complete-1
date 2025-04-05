import tkinter as tk
from tkinter import ttk
from datetime import datetime
import json
import logging
from typing import List, Optional
from dataclasses import dataclass, asdict

from .utils.file_loader import VideoIndex, VideoFile

logger = logging.getLogger(__name__)

@dataclass
class Incident:
    """Represents a recorded incident."""
    id: str
    timestamp: datetime
    video_filepath: str
    description: str
    severity: str
    notes: str = ""
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_notes: str = ""

class IncidentLogger:
    def __init__(self, video_index: VideoIndex, incident_file: str = "incidents.json"):
        self.video_index = video_index
        self.incident_file = incident_file
        self.incidents: List[Incident] = []
        self.load_incidents()
        
    def load_incidents(self):
        """Load incidents from file."""
        try:
            if os.path.exists(self.incident_file):
                with open(self.incident_file, 'r') as f:
                    data = json.load(f)
                    self.incidents = [
                        Incident(
                            id=inc['id'],
                            timestamp=datetime.fromisoformat(inc['timestamp']),
                            video_filepath=inc['video_filepath'],
                            description=inc['description'],
                            severity=inc['severity'],
                            notes=inc.get('notes', ''),
                            resolved=inc.get('resolved', False),
                            resolution_time=datetime.fromisoformat(inc['resolution_time'])
                            if inc.get('resolution_time') else None,
                            resolution_notes=inc.get('resolution_notes', '')
                        )
                        for inc in data
                    ]
        except Exception as e:
            logger.error(f"Error loading incidents: {e}")
            self.incidents = []
            
    def save_incidents(self):
        """Save incidents to file."""
        try:
            data = [
                {
                    **asdict(inc),
                    'timestamp': inc.timestamp.isoformat(),
                    'resolution_time': inc.resolution_time.isoformat()
                    if inc.resolution_time else None
                }
                for inc in self.incidents
            ]
            with open(self.incident_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving incidents: {e}")
            
    def add_incident(
        self,
        video_filepath: str,
        description: str,
        severity: str,
        notes: str = ""
    ) -> Incident:
        """Add a new incident."""
        incident = Incident(
            id=f"INC-{len(self.incidents) + 1:04d}",
            timestamp=datetime.now(),
            video_filepath=video_filepath,
            description=description,
            severity=severity,
            notes=notes
        )
        self.incidents.append(incident)
        self.save_incidents()
        
        # Update video incident flag
        for video in self.video_index.videos:
            if video.filepath == video_filepath:
                video.incident_flag = True
                self.video_index.update_video(video)
                break
                
        return incident
        
    def resolve_incident(
        self,
        incident_id: str,
        resolution_notes: str = ""
    ) -> Optional[Incident]:
        """Mark an incident as resolved."""
        for incident in self.incidents:
            if incident.id == incident_id:
                incident.resolved = True
                incident.resolution_time = datetime.now()
                incident.resolution_notes = resolution_notes
                self.save_incidents()
                return incident
        return None
        
    def get_incidents_by_date(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Incident]:
        """Get incidents within a date range."""
        if start_date is None:
            start_date = datetime.min
        if end_date is None:
            end_date = datetime.max
            
        return [
            inc for inc in self.incidents
            if start_date <= inc.timestamp <= end_date
        ]
        
    def get_incidents_by_video(self, video_filepath: str) -> List[Incident]:
        """Get all incidents for a specific video."""
        return [
            inc for inc in self.incidents
            if inc.video_filepath == video_filepath
        ]
        
    def get_unresolved_incidents(self) -> List[Incident]:
        """Get all unresolved incidents."""
        return [inc for inc in self.incidents if not inc.resolved]

class IncidentLoggerGUI:
    def __init__(self, root: tk.Tk, incident_logger: IncidentLogger):
        self.root = root
        self.root.title("Incident Logger")
        self.incident_logger = incident_logger
        
        # Create main layout
        self.create_layout()
        
        # Load initial data
        self.load_incidents()
        
    def create_layout(self):
        """Create the main GUI layout."""
        # Create main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for incident list
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)
        
        # Right panel for incident details
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=2)
        
        # Create incident list
        self.create_incident_list(left_panel)
        
        # Create incident details
        self.create_incident_details(right_panel)
        
    def create_incident_list(self, parent: ttk.Frame):
        """Create the incident list display."""
        # List frame
        list_frame = ttk.LabelFrame(parent, text="Incidents")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview
        columns = ("ID", "Date", "Time", "Severity", "Status")
        self.incident_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings"
        )
        
        # Configure columns
        for col in columns:
            self.incident_tree.heading(col, text=col)
            self.incident_tree.column(col, width=100)
            
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.incident_tree.yview
        )
        self.incident_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.incident_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.incident_tree.bind("<<TreeviewSelect>>", self.on_incident_select)
        
        # Add new incident button
        ttk.Button(
            parent,
            text="New Incident",
            command=self.show_new_incident_dialog
        ).pack(pady=5)
        
    def create_incident_details(self, parent: ttk.Frame):
        """Create the incident details panel."""
        # Details frame
        details_frame = ttk.LabelFrame(parent, text="Incident Details")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Incident info
        info_frame = ttk.Frame(details_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="ID:").grid(row=0, column=0, sticky="w")
        self.id_label = ttk.Label(info_frame, text="")
        self.id_label.grid(row=0, column=1, sticky="w")
        
        ttk.Label(info_frame, text="Date/Time:").grid(row=1, column=0, sticky="w")
        self.datetime_label = ttk.Label(info_frame, text="")
        self.datetime_label.grid(row=1, column=1, sticky="w")
        
        ttk.Label(info_frame, text="Severity:").grid(row=2, column=0, sticky="w")
        self.severity_label = ttk.Label(info_frame, text="")
        self.severity_label.grid(row=2, column=1, sticky="w")
        
        ttk.Label(info_frame, text="Status:").grid(row=3, column=0, sticky="w")
        self.status_label = ttk.Label(info_frame, text="")
        self.status_label.grid(row=3, column=1, sticky="w")
        
        # Description
        ttk.Label(details_frame, text="Description:").pack(anchor="w", padx=5)
        self.description_text = tk.Text(details_frame, height=3)
        self.description_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Notes
        ttk.Label(details_frame, text="Notes:").pack(anchor="w", padx=5)
        self.notes_text = tk.Text(details_frame, height=5)
        self.notes_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Resolution notes
        ttk.Label(details_frame, text="Resolution Notes:").pack(anchor="w", padx=5)
        self.resolution_text = tk.Text(details_frame, height=5)
        self.resolution_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Resolution button
        self.resolve_button = ttk.Button(
            details_frame,
            text="Mark as Resolved",
            command=self.resolve_incident
        )
        self.resolve_button.pack(pady=5)
        
    def load_incidents(self):
        """Load incidents into the treeview."""
        # Clear current list
        for item in self.incident_tree.get_children():
            self.incident_tree.delete(item)
            
        # Add incidents
        for incident in self.incident_logger.incidents:
            self.incident_tree.insert(
                "",
                tk.END,
                values=(
                    incident.id,
                    incident.timestamp.strftime("%Y-%m-%d"),
                    incident.timestamp.strftime("%H:%M:%S"),
                    incident.severity,
                    "Resolved" if incident.resolved else "Open"
                ),
                tags=(incident.id,)
            )
            
    def on_incident_select(self, event):
        """Handle incident selection in the treeview."""
        selection = self.incident_tree.selection()
        if not selection:
            return
            
        # Get the incident ID from the item tags
        incident_id = self.incident_tree.item(selection[0])['tags'][0]
        
        # Find the incident
        incident = next(
            (inc for inc in self.incident_logger.incidents if inc.id == incident_id),
            None
        )
        
        if incident:
            self.display_incident(incident)
            
    def display_incident(self, incident: Incident):
        """Display incident details in the details panel."""
        self.id_label.config(text=incident.id)
        self.datetime_label.config(
            text=incident.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        )
        self.severity_label.config(text=incident.severity)
        self.status_label.config(
            text="Resolved" if incident.resolved else "Open"
        )
        
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", incident.description)
        
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", incident.notes)
        
        self.resolution_text.delete("1.0", tk.END)
        self.resolution_text.insert("1.0", incident.resolution_notes)
        
        # Update resolve button state
        self.resolve_button.config(
            state="disabled" if incident.resolved else "normal"
        )
        
    def show_new_incident_dialog(self):
        """Show dialog for creating a new incident."""
        dialog = tk.Toplevel(self.root)
        dialog.title("New Incident")
        dialog.geometry("400x300")
        
        # Video selection
        ttk.Label(dialog, text="Video:").pack(pady=5)
        video_var = tk.StringVar()
        video_combo = ttk.Combobox(
            dialog,
            textvariable=video_var,
            values=[v.filepath for v in self.incident_logger.video_index.videos]
        )
        video_combo.pack(pady=5)
        
        # Severity selection
        ttk.Label(dialog, text="Severity:").pack(pady=5)
        severity_var = tk.StringVar()
        severity_combo = ttk.Combobox(
            dialog,
            textvariable=severity_var,
            values=["Low", "Medium", "High", "Critical"],
            state="readonly"
        )
        severity_combo.pack(pady=5)
        
        # Description
        ttk.Label(dialog, text="Description:").pack(pady=5)
        description_text = tk.Text(dialog, height=4)
        description_text.pack(pady=5)
        
        # Notes
        ttk.Label(dialog, text="Notes:").pack(pady=5)
        notes_text = tk.Text(dialog, height=4)
        notes_text.pack(pady=5)
        
        def create_incident():
            try:
                self.incident_logger.add_incident(
                    video_filepath=video_var.get(),
                    description=description_text.get("1.0", tk.END).strip(),
                    severity=severity_var.get(),
                    notes=notes_text.get("1.0", tk.END).strip()
                )
                self.load_incidents()
                dialog.destroy()
            except Exception as e:
                logger.error(f"Error creating incident: {e}")
                
        ttk.Button(dialog, text="Create", command=create_incident).pack(pady=10)
        
    def resolve_incident(self):
        """Mark the selected incident as resolved."""
        selection = self.incident_tree.selection()
        if not selection:
            return
            
        incident_id = self.incident_tree.item(selection[0])['tags'][0]
        resolution_notes = self.resolution_text.get("1.0", tk.END).strip()
        
        if self.incident_logger.resolve_incident(incident_id, resolution_notes):
            self.load_incidents()
            self.display_incident(
                next(
                    inc for inc in self.incident_logger.incidents
                    if inc.id == incident_id
                )
            ) 