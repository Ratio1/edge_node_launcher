from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGridLayout, QGroupBox)
from PyQt5.QtCore import pyqtSignal, Qt
from models.NodeInfo import NodeInfo

class NodeInfoWidget(QWidget):
    """
    Widget for displaying node information
    """
    # Signals
    refresh_requested = pyqtSignal()  # Emitted when refresh button is clicked
    copy_address_requested = pyqtSignal(str)  # Emitted when copy address button is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize UI components
        self.lbl_node_address = QLabel("N/A")
        self.lbl_eth_address = QLabel("N/A")
        self.lbl_node_status = QLabel("Unknown")
        self.lbl_uptime = QLabel("N/A")
        self.lbl_node_name = QLabel("N/A")
        
        self.btn_copy_address = QPushButton("Copy")
        self.btn_copy_eth = QPushButton("Copy")
        self.btn_refresh = QPushButton("Refresh")
        
        # Setup UI layout
        self.init_ui()
        
        # Connect signals
        self.connect_signals()
    
    def init_ui(self):
        """Initialize the UI components and layout"""
        # Main layout
        layout = QVBoxLayout()
        
        # Create info group box
        info_group = QGroupBox("Node Information")
        info_layout = QGridLayout()
        
        # Add node status row
        info_layout.addWidget(QLabel("Status:"), 0, 0)
        info_layout.addWidget(self.lbl_node_status, 0, 1)
        
        # Add node name row
        info_layout.addWidget(QLabel("Node Name:"), 1, 0)
        info_layout.addWidget(self.lbl_node_name, 1, 1)
        
        # Add uptime row
        info_layout.addWidget(QLabel("Uptime:"), 2, 0)
        info_layout.addWidget(self.lbl_uptime, 2, 1)
        
        # Add Node address row with copy button
        info_layout.addWidget(QLabel("Node Address:"), 3, 0)
        addr_layout = QHBoxLayout()
        addr_layout.addWidget(self.lbl_node_address, 1)
        addr_layout.addWidget(self.btn_copy_address, 0)
        info_layout.addLayout(addr_layout, 3, 1)
        
        # Add ETH address row with copy button
        info_layout.addWidget(QLabel("ETH Address:"), 4, 0)
        eth_layout = QHBoxLayout()
        eth_layout.addWidget(self.lbl_eth_address, 1)
        eth_layout.addWidget(self.btn_copy_eth, 0)
        info_layout.addLayout(eth_layout, 4, 1)
        
        # Set info group layout
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Add refresh button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_refresh)
        layout.addLayout(button_layout)
        
        # Set layout
        self.setLayout(layout)
        
        # Set text alignment
        self.lbl_node_address.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_eth_address.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_node_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_uptime.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_node_name.setTextInteractionFlags(Qt.TextSelectableByMouse)
    
    def connect_signals(self):
        """Connect widget signals to slots"""
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        self.btn_copy_address.clicked.connect(lambda: self.copy_address_requested.emit('node'))
        self.btn_copy_eth.clicked.connect(lambda: self.copy_address_requested.emit('eth'))
    
    def update_node_info(self, node_info: NodeInfo = None):
        """
        Update the displayed node information
        
        Args:
            node_info: NodeInfo object containing node information
        """
        if node_info:
            # Update node address
            self.lbl_node_address.setText(node_info.address or "N/A")
            
            # Update ETH address
            self.lbl_eth_address.setText(node_info.ethereum_address or "N/A")
            
            # Update status
            status_text = "Running" if node_info.is_running else "Stopped"
            self.lbl_node_status.setText(status_text)
            
            # Update uptime if available
            if node_info.uptime:
                uptime_text = self._format_uptime(node_info.uptime)
                self.lbl_uptime.setText(uptime_text)
            else:
                self.lbl_uptime.setText("N/A")
            
            # Update node name
            self.lbl_node_name.setText(node_info.name or "N/A")
        else:
            self.clear_info()
    
    def clear_info(self):
        """Clear all displayed information"""
        self.lbl_node_address.setText("N/A")
        self.lbl_eth_address.setText("N/A")
        self.lbl_node_status.setText("Unknown")
        self.lbl_uptime.setText("N/A")
        self.lbl_node_name.setText("N/A")
    
    def _format_uptime(self, uptime_seconds: int) -> str:
        """
        Format uptime in seconds to a human-readable string
        
        Args:
            uptime_seconds: Uptime in seconds
            
        Returns:
            str: Formatted uptime string
        """
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{int(days)}d {int(hours)}h {int(minutes)}m"
        elif hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s" 