from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QProgressBar, QFrame,
    QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QPalette
import platform
import re
import logging
from app_forms.frm_utils import LoadingIndicator
from utils.const import DARK_STYLESHEET, LIGHT_COLORS, DARK_COLORS

class DockerPullDialog(QDialog):
    """Dialog for Docker image pull progress."""
    
    # Signal emitted when pull is complete
    pull_complete = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, parent=None):
        """Initialize the dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Pulling Docker Image")
        self.setMinimumWidth(600)  # Increased width
        self.setMinimumHeight(500)  # Increased height
        
        # Set up the dialog UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(15)  # Increased spacing
        layout.setContentsMargins(25, 25, 25, 25)  # Increased margins
        
        # Title
        title_label = QLabel("Pulling Docker Image")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")  # Larger font
        title_label.setAlignment(Qt.AlignCenter)
        
        # Info label
        self.info_label = QLabel("Preparing to pull Docker image...")
        self.info_label.setStyleSheet("font-size: 14px;")
        self.info_label.setWordWrap(True)
        
        # Overall progress
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_progress.setMinimumHeight(25)  # Taller progress bar
        self.overall_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 6px;
                text-align: center;
                height: 25px;
                background-color: #222;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 6px;
            }
        """)
        
        # Layer progress section
        layer_frame = QFrame()
        layer_frame.setFrameShape(QFrame.StyledPanel)
        layer_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        # Create a scroll area for layers
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #334155;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #475569;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Container widget for the scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)  # Increased spacing between layers
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        
        # Layer label
        layer_label = QLabel("Layer Progress:")
        layer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        scroll_layout.addWidget(layer_label)
        
        # Layer progress container
        self.layer_layout = QVBoxLayout()
        self.layer_layout.setSpacing(10)
        scroll_layout.addLayout(self.layer_layout)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        
        # Add scroll area to layer frame
        layer_frame_layout = QVBoxLayout(layer_frame)
        layer_frame_layout.setContentsMargins(0, 0, 0, 0)
        layer_frame_layout.addWidget(scroll_area)
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.overall_progress)
        layout.addWidget(layer_frame, 1)  # Give the layer frame stretch factor
        
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
        # Log the raw Docker pull output
        logging.info(f"Docker pull output: {line.strip()}")
        
        # Process the line to extract layer information
        if "Pulling from" in line:
            repo_info = line.strip()
            logging.info(f"Pulling Docker image repository: {repo_info}")
            self.info_label.setText(f"Pulling image: {line}")
            return
            
        # Match layer ID - handle both old and new Docker output formats
        layer_match = re.search(r'([a-f0-9]{12}): (.*)', line)
        digest_match = re.search(r'(sha256:[a-f0-9]{64}): (.*)', line)
        
        if layer_match or digest_match:
            match = layer_match or digest_match
            layer_id = match.group(1)
            status = match.group(2)
            
            # Initialize layer if not seen before
            if layer_id not in self.layers:
                self.layers[layer_id] = {
                    'id': layer_id,
                    'status': status,
                    'progress': 0
                }
                self.total_layers += 1
                logging.info(f"New layer detected: {layer_id} - Total layers: {self.total_layers}")
                
                # Create progress bar for this layer
                layer_layout = QHBoxLayout()
                layer_layout.setSpacing(12)  # Increased spacing
                
                layer_label = QLabel(f"{layer_id[:8]}...")
                layer_label.setFixedWidth(90)  # Slightly wider for better readability
                layer_label.setStyleSheet("color: #60a5fa; font-weight: bold; font-family: monospace; font-size: 13px;")
                
                status_label = QLabel(status)
                status_label.setStyleSheet("color: #e2e8f0; font-family: monospace; font-size: 13px;")
                
                layer_progress = QProgressBar()
                layer_progress.setRange(0, 100)
                layer_progress.setValue(0)
                layer_progress.setMinimumHeight(20)  # Taller progress bars
                layer_progress.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #475569;
                        border-radius: 5px;
                        text-align: center;
                        height: 20px;
                        background-color: #334155;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QProgressBar::chunk {
                        background-color: #3b82f6;
                        border-radius: 5px;
                    }
                """)
                
                layer_layout.addWidget(layer_label)
                layer_layout.addWidget(layer_progress, 1)  # Give progress bar stretch factor
                layer_layout.addWidget(status_label)
                
                self.layer_widgets[layer_id] = {
                    'layout': layer_layout,
                    'label': layer_label,
                    'progress': layer_progress,
                    'status': status_label
                }
                
                self.layer_layout.addLayout(layer_layout)
            
            # Update layer status
            self.layers[layer_id]['status'] = status
            
            # Update status label if it exists
            if layer_id in self.layer_widgets and 'status' in self.layer_widgets[layer_id]:
                self.layer_widgets[layer_id]['status'].setText(status)
            
            # Check for progress information
            progress_match = re.search(r'(\d+)%', status)
            if progress_match:
                progress = int(progress_match.group(1))
                self.layers[layer_id]['progress'] = progress
                
                # Log progress updates at 25% intervals to avoid excessive logging
                prev_progress = getattr(self, f"_prev_progress_{layer_id}", -25)
                if progress >= prev_progress + 25 or progress == 100:
                    logging.info(f"Layer {layer_id}: {progress}% complete - Status: {status}")
                    setattr(self, f"_prev_progress_{layer_id}", progress - (progress % 25))
                
                # Update progress bar
                if layer_id in self.layer_widgets:
                    self.layer_widgets[layer_id]['progress'].setValue(progress)
            else:
                # Log status updates without progress percentage
                logging.info(f"Layer {layer_id} status update: {status}")
            
            # Update overall progress
            self._update_overall_progress()
            
            # Process events to ensure UI updates
            QApplication.processEvents()
        # Handle newer Docker output format with direct status updates
        elif "Downloading" in line or "Extracting" in line or "Download complete" in line or "Pull complete" in line:
            # For newer Docker output that doesn't always include layer IDs
            # Create a synthetic layer ID based on the line content
            line_hash = str(hash(line) % 10000).zfill(12)  # Create a 12-char hash as ID
            status = line.strip()
            
            # Initialize layer if not seen before
            if line_hash not in self.layers:
                self.layers[line_hash] = {
                    'id': line_hash,
                    'status': status,
                    'progress': 0
                }
                self.total_layers += 1
                logging.info(f"New status line detected: {status} - Total layers: {self.total_layers}")
                
                # Create progress bar for this status
                layer_layout = QHBoxLayout()
                layer_layout.setSpacing(12)  # Increased spacing
                
                layer_label = QLabel("Layer")
                layer_label.setFixedWidth(90)  # Slightly wider for better readability
                layer_label.setStyleSheet("color: #60a5fa; font-weight: bold; font-family: monospace; font-size: 13px;")
                
                status_label = QLabel(status)
                status_label.setStyleSheet("color: #e2e8f0; font-family: monospace; font-size: 13px;")
                
                layer_progress = QProgressBar()
                layer_progress.setRange(0, 100)
                layer_progress.setValue(0)
                layer_progress.setMinimumHeight(20)  # Taller progress bars
                layer_progress.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #475569;
                        border-radius: 5px;
                        text-align: center;
                        height: 20px;
                        background-color: #334155;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QProgressBar::chunk {
                        background-color: #3b82f6;
                        border-radius: 5px;
                    }
                """)
                
                layer_layout.addWidget(layer_label)
                layer_layout.addWidget(layer_progress, 1)  # Give progress bar stretch factor
                layer_layout.addWidget(status_label)
                
                self.layer_widgets[line_hash] = {
                    'layout': layer_layout,
                    'label': layer_label,
                    'progress': layer_progress,
                    'status': status_label
                }
                
                self.layer_layout.addLayout(layer_layout)
            
            # Update layer status
            self.layers[line_hash]['status'] = status
            
            # Update status label if it exists
            if line_hash in self.layer_widgets and 'status' in self.layer_widgets[line_hash]:
                self.layer_widgets[line_hash]['status'].setText(status)
            
            # Check for progress information in newer format
            progress_match = re.search(r'(\d+\.\d+)MB/(\d+\.\d+)MB', status)
            if progress_match:
                current = float(progress_match.group(1))
                total = float(progress_match.group(2))
                if total > 0:
                    progress = int((current / total) * 100)
                    self.layers[line_hash]['progress'] = progress
                    
                    # Update progress bar
                    if line_hash in self.layer_widgets:
                        self.layer_widgets[line_hash]['progress'].setValue(progress)
            elif "Download complete" in status or "Pull complete" in status:
                # Set to 100% when complete
                self.layers[line_hash]['progress'] = 100
                if line_hash in self.layer_widgets:
                    self.layer_widgets[line_hash]['progress'].setValue(100)
            
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
        
        # Log overall progress at 10% intervals to avoid excessive logging
        prev_overall_progress = getattr(self, "_prev_overall_progress", -10)
        if overall_percent >= prev_overall_progress + 10 or overall_percent == 100:
            logging.info(f"Docker pull overall progress: {overall_percent}% complete ({self.total_layers} layers)")
            setattr(self, "_prev_overall_progress", overall_percent - (overall_percent % 10))
        
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
        
        # Close immediately and then use a timer to ensure proper cleanup
        self.close()
        # Use a short timer to ensure proper cleanup
        QTimer.singleShot(100, self.deleteLater)

    def set_pull_complete(self, success, message):
        """Handle pull completion.
        
        Args:
            success: Whether the pull was successful
            message: Success or error message
        """
        # Update UI to show completion status
        if success:
            self.set_message("Docker image pull completed successfully!")
            # Set overall progress to 100%
            self.overall_progress.setValue(100)
        else:
            self.set_message(f"Docker image pull failed: {message}")
        
        # Process events to ensure UI updates immediately
        QApplication.processEvents()
        
        # Emit the signal to notify the parent
        self.pull_complete.emit(success, message)
        
        # Close the dialog automatically after a short delay
        QTimer.singleShot(100, self.safe_close)
