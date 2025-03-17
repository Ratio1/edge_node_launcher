from PyQt5.QtWidgets import (QDialog, QProgressBar, QLabel, QVBoxLayout, 
                            QPushButton, QHBoxLayout, QWidget, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QPalette
import humanize

class ImagePullProgressDialog(QDialog):
    """Dialog to display Docker image pull progress"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Updating Docker Image")
        self.setMinimumWidth(500)
        self.setMinimumHeight(200)
        
        # Apply system colors for consistent appearance
        self.setStyleSheet("""
            QDialog {
                border: none;
                border-radius: 8px;
            }
            QLabel {
                background-color: transparent;
                font-size: 14px;
            }
            QProgressBar {
                border: 1px solid palette(mid);
                border-radius: 4px;
                text-align: center;
                background-color: palette(base);
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: palette(highlight);
                width: 1px;
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)
        
        self.setup_ui()
        self.layer_widgets = {}
        
    def setup_ui(self):
        """Set up the dialog UI"""
        main_layout = QVBoxLayout(self)
        
        # Status label at the top
        self.status_label = QLabel("Checking for updates...")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Main progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Progress size label
        self.size_label = QLabel("")
        self.size_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.size_label)
        
        # Scroll area for layer progress
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.layers_container = QWidget()
        self.layers_layout = QVBoxLayout(self.layers_container)
        scroll_area.setWidget(self.layers_container)
        main_layout.addWidget(scroll_area)
        
        # Cancel button
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)
    
    @pyqtSlot(int, int, str, str)
    def update_progress(self, current: int, total: int, layer_id: str, status: str):
        """Update the progress display.
        
        Args:
            current: Current download size in bytes
            total: Total download size in bytes
            layer_id: Layer identifier
            status: Current status
        """
        # Update overall progress
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            
            # Format size information
            current_human = humanize.naturalsize(current)
            total_human = humanize.naturalsize(total)
            self.size_label.setText(f"{current_human} / {total_human} ({percent}%)")
        
        # Create or update layer progress
        if layer_id not in self.layer_widgets:
            # Create new layer progress widgets
            layer_container = QWidget()
            layer_layout = QHBoxLayout(layer_container)
            layer_layout.setContentsMargins(0, 0, 0, 0)
            
            layer_label = QLabel(f"Layer {layer_id[:8]}...")
            layer_label.setMinimumWidth(100)
            
            layer_bar = QProgressBar()
            layer_bar.setRange(0, 100)
            
            layer_size = QLabel()
            layer_size.setMinimumWidth(150)
            
            layer_layout.addWidget(layer_label)
            layer_layout.addWidget(layer_bar)
            layer_layout.addWidget(layer_size)
            
            self.layers_layout.addWidget(layer_container)
            self.layer_widgets[layer_id] = (layer_bar, layer_size)
        
        # Update layer progress
        layer_bar, layer_size = self.layer_widgets[layer_id]
        if status == "Downloading" and total > 0:
            layer_current, layer_total = 0, 0
            for i, part in enumerate(status.split()):
                try:
                    if i == 1:  # Current size
                        layer_current = int(part)
                    elif i == 3:  # Total size
                        layer_total = int(part)
                except ValueError:
                    pass
            
            if layer_total > 0:
                layer_percent = int((layer_current / layer_total) * 100)
                layer_bar.setValue(layer_percent)
                layer_size.setText(f"{humanize.naturalsize(layer_current)} / {humanize.naturalsize(layer_total)}")
    
    @pyqtSlot(str)
    def update_status(self, message: str):
        """Update the status message.
        
        Args:
            message: Status message to display
        """
        # Update status label with the message
        self.status_label.setText(message)
        
        # Without JSON progress, we may not have detailed progress information
        # If the message contains progress information, try to update the progress bar
        if "Downloading" in message and "[" in message and "]" in message:
            try:
                # Try to extract progress percentage from messages like:
                # "Downloading [=====>   ] 45%"
                percent_str = message.split("]")[0].split("[")[1].strip()
                if "%" in percent_str:
                    percent = int(percent_str.replace("%", "").strip())
                    self.progress_bar.setValue(percent)
            except (IndexError, ValueError):
                pass  # Ignore parsing errors
        
    def closeEvent(self, event):
        """Handle dialog close event"""
        # This will be called when the dialog is closed
        self.reject()
        super().closeEvent(event)
        
    def safe_close(self):
        """Safely close the dialog with a timer to prevent direct deletion."""
        # Use a short timer to ensure proper context for closing
        QTimer.singleShot(100, self.close) 