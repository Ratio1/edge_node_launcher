from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
from widgets.CenteredComboBox import CenteredComboBox

class ContainerListWidget(QWidget):
    """
    Widget for displaying and selecting Docker containers
    """
    # Signals
    container_selected = pyqtSignal(str)  # Emitted when a container is selected (container_name)
    container_toggle_requested = pyqtSignal(str)  # Emitted when a container start/stop is requested
    add_container_requested = pyqtSignal()  # Emitted when add container button is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize UI components
        self.containers_combo = CenteredComboBox()
        self.btn_toggle = QPushButton("Start Container")
        self.btn_add_node = QPushButton("Add Node")
        
        # Setup UI layout
        self.init_ui()
        
        # Connect signals
        self.connect_signals()
    
    def init_ui(self):
        """Initialize the UI components and layout"""
        # Main layout
        layout = QVBoxLayout()
        
        # Combo box for container selection
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(self.containers_combo)
        layout.addLayout(combo_layout)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_toggle)
        button_layout.addWidget(self.btn_add_node)
        layout.addLayout(button_layout)
        
        # Set layout
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connect widget signals to slots"""
        self.containers_combo.currentIndexChanged.connect(self._on_container_selected)
        self.btn_toggle.clicked.connect(self._on_toggle_clicked)
        self.btn_add_node.clicked.connect(self._on_add_node_clicked)
    
    def _on_container_selected(self, index):
        """Handle container selection from combo box"""
        if index >= 0:
            container_name = self.containers_combo.itemData(index)
            if container_name:
                self.container_selected.emit(container_name)
    
    def _on_toggle_clicked(self):
        """Handle container toggle button click"""
        index = self.containers_combo.currentIndex()
        if index >= 0:
            container_name = self.containers_combo.itemData(index)
            if container_name:
                self.container_toggle_requested.emit(container_name)
    
    def _on_add_node_clicked(self):
        """Handle add node button click"""
        self.add_container_requested.emit()
    
    def update_containers(self, containers, current_container=None):
        """
        Update the containers combo box with the provided containers
        
        Args:
            containers: List of container dictionaries with 'name', 'running', etc.
            current_container: Name of the currently selected container
        """
        # Save current container name
        current_name = current_container or (
            self.containers_combo.itemData(self.containers_combo.currentIndex()) 
            if self.containers_combo.currentIndex() >= 0 else None
        )
        
        # Clear combo box
        self.containers_combo.clear()
        
        # Add containers to combo box
        select_index = 0
        for i, container in enumerate(containers):
            name = container.get("name", "")
            self.containers_combo.addItem(f"{name} ({'Running' if container.get('running', False) else 'Stopped'})", name)
            
            # If this is the current container, set as selected
            if name == current_name:
                select_index = i
        
        # Set current index
        if containers:
            self.containers_combo.setCurrentIndex(select_index)
    
    def update_toggle_button(self, is_running):
        """
        Update the toggle button text based on container state
        
        Args:
            is_running: Whether the container is running
        """
        self.btn_toggle.setText("Stop Container" if is_running else "Start Container")
    
    def get_current_container(self):
        """
        Get the currently selected container name
        
        Returns:
            str: Current container name or None
        """
        index = self.containers_combo.currentIndex()
        if index >= 0:
            return self.containers_combo.itemData(index)
        return None 