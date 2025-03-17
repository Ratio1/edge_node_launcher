from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QPalette
import platform
import re
from app_forms.frm_utils import LoadingIndicator
from utils.const import DARK_STYLESHEET, LIGHT_COLORS, DARK_COLORS

class DockerPullDialog(QDialog):
    """Dialog that shows Docker pull progress with detailed layer information."""
    
    # Signal to notify when pull is complete
    pull_complete = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, parent=None, title="Pulling Docker Image", message="Please wait while the Docker image is being pulled...", size=50):
        """Initialize the Docker pull dialog.
        
        Args:
            parent: Parent widget
            title: Title of the dialog
            message: Message to display
            size: Size of the loading indicator
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        
        # Set window flags based on platform
        system = platform.system().lower()
        if system == "linux":
            linux_titlebar_style = True
        elif system == "windows":
            linux_titlebar_style = False
        elif system == "darwin":  # macOS
            self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            linux_titlebar_style = False
        
        self.setFixedSize(500, 300)  # Larger dialog to show layer progress
        self.setModal(True)
        
        # Use system colors instead of hardcoded blue background
        base_style = """
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
        """
        
        # Apply platform-specific styles
        if linux_titlebar_style:
            # On Linux, add specific styling for the title bar
            linux_style = """
                QDialog {
                    border: 1px solid palette(mid);
                }
            """
            base_style += linux_style
        
        self.setStyleSheet(base_style)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create title label
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # Create info label
        self.info_label = QLabel(message)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        
        # Create overall progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_progress.setFormat("Overall Progress: %p%")
        
        # Create layer progress section
        layer_label = QLabel("Layer Progress:")
        self.layer_layout = QVBoxLayout()
        self.layer_layout.setSpacing(5)
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.overall_progress)
        layout.addWidget(layer_label)
        layout.addLayout(self.layer_layout)
        
        self.setLayout(layout)
        
        # Initialize layer tracking
        self.layers = {}
        self.layer_widgets = {}
        self.total_layers = 0
    
    @pyqtSlot(str)
    def update_pull_progress(self, line):
        """Update the pull progress based on Docker output.
        
        Args:
            line: Line of Docker pull output
        """
        # Process the line to extract layer information
        if "Pulling from" in line:
            self.info_label.setText(f"Pulling image: {line}")
            return
            
        # Match layer ID
        layer_match = re.search(r'([a-f0-9]{12}): (.*)', line)
        if layer_match:
            layer_id = layer_match.group(1)
            status = layer_match.group(2)
            
            # Initialize layer if not seen before
            if layer_id not in self.layers:
                self.layers[layer_id] = {
                    'id': layer_id,
                    'status': status,
                    'progress': 0
                }
                self.total_layers += 1
                
                # Create progress bar for this layer
                layer_layout = QHBoxLayout()
                layer_label = QLabel(f"{layer_id[:8]}...")
                layer_label.setFixedWidth(80)
                layer_progress = QProgressBar()
                layer_progress.setRange(0, 100)
                layer_progress.setValue(0)
                
                layer_layout.addWidget(layer_label)
                layer_layout.addWidget(layer_progress)
                
                self.layer_widgets[layer_id] = {
                    'layout': layer_layout,
                    'label': layer_label,
                    'progress': layer_progress
                }
                
                self.layer_layout.addLayout(layer_layout)
            
            # Update layer status
            self.layers[layer_id]['status'] = status
            
            # Check for progress information
            progress_match = re.search(r'(\d+)%', status)
            if progress_match:
                progress = int(progress_match.group(1))
                self.layers[layer_id]['progress'] = progress
                
                # Update progress bar
                if layer_id in self.layer_widgets:
                    self.layer_widgets[layer_id]['progress'].setValue(progress)
            
            # Update overall progress
            self._update_overall_progress()
            
            # Process events to ensure UI updates
            QApplication.processEvents()
    
    def _update_overall_progress(self):
        """Update the overall progress based on layer progress."""
        if not self.total_layers:
            return
            
        total_progress = sum(layer['progress'] for layer in self.layers.values())
        overall_percent = int(total_progress / self.total_layers)
        self.overall_progress.setValue(overall_percent)
    
    @pyqtSlot(str)
    def set_message(self, message):
        """Update the dialog message.
        
        Args:
            message: New message to display
        """
        if hasattr(self, 'info_label'):
            self.info_label.setText(message)
            # Process events to ensure UI updates immediately
            QApplication.processEvents()
    
    def closeEvent(self, event):
        """Handle the dialog close event."""
        if hasattr(self, 'loading_indicator'):
            self.loading_indicator.stop()
        event.accept()
    
    @pyqtSlot()
    def safe_close(self):
        """Safely close the dialog with a timer to prevent direct deletion."""
        if hasattr(self, 'loading_indicator'):
            self.loading_indicator.stop()
        QTimer.singleShot(100, self.close)
