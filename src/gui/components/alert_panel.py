from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from core.alerts.alert_manager import AlertManager, AlertPriority

class AlertPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.alert_manager = AlertManager()
        self.setup_ui()
        self.initialize_alert_handlers()

    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.alert_widgets = {}
        self.setup_priority_sections()

    def setup_priority_sections(self):
        for priority in AlertPriority:
            section = QWidget()
            section_layout = QVBoxLayout()
            section.setLayout(section_layout)
            
            header = QLabel(f"{priority.value.upper()} PRIORITY ALERTS")
            header.setStyleSheet(self._get_priority_style(priority))
            section_layout.addWidget(header)
            
            self.layout.addWidget(section)

    async def initialize_alert_handlers(self):
        await self.alert_manager.event_manager.subscribe(
            'new_alert',
            self._handle_new_alert
        )

    async def _handle_new_alert(self, event):
        alert = event.data['alert']
        await self.add_alert_widget(alert)

    def _get_priority_style(self, priority: AlertPriority) -> str:
        colors = {
            AlertPriority.LOW: "green",
            AlertPriority.MEDIUM: "orange",
            AlertPriority.HIGH: "red",
            AlertPriority.CRITICAL: "darkred"
        }
        return f"""
            color: {colors[priority]};
            font-weight: bold;
            padding: 5px;
            border: 1px solid {colors[priority]};
        """ 
