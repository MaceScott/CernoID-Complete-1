from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from core.auth.permissions import PermissionManager, Permission
from core.error_handling import handle_exceptions

class PermissionControl(QWidget):
    def __init__(self):
        super().__init__()
        self.permission_manager = PermissionManager()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.permission_tree = QTreeWidget()
        self.permission_tree.setHeaderLabels(["Role", "Permissions"])
        layout.addWidget(self.permission_tree)
        
        self.load_permissions()

    @handle_exceptions(logger=admin_logger.error)
    async def load_permissions(self):
        self.permission_tree.clear()
        
        for role_name, role in self.permission_manager.roles.items():
            role_item = QTreeWidgetItem([role_name])
            self.permission_tree.addTopLevelItem(role_item)
            
            for permission in Permission:
                perm_item = QTreeWidgetItem([permission.value])
                perm_item.setCheckState(
                    1, 
                    Qt.Checked if permission in role.permissions 
                    else Qt.Unchecked
                )
                role_item.addChild(perm_item)

    @handle_exceptions(logger=admin_logger.error)
    async def save_permissions(self):
        for role_idx in range(self.permission_tree.topLevelItemCount()):
            role_item = self.permission_tree.topLevelItem(role_idx)
            role_name = role_item.text(0)
            permissions = set()
            
            for perm_idx in range(role_item.childCount()):
                perm_item = role_item.child(perm_idx)
                if perm_item.checkState(1) == Qt.Checked:
                    permissions.add(Permission(perm_item.text(0)))
            
            self.permission_manager.roles[role_name].permissions = permissions 
