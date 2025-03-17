from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QColor
import platform
from app_forms.frm_utils import LoadingIndicator
from utils.const import DARK_STYLESHEET, LIGHT_COLORS, DARK_COLORS

class LoadingDialog(QDialog):
    """Reusable loading dialog widget that can be used throughout the application.
    
    This dialog shows a loading spinner with a customizable message and title.
    It is designed to be used for any long-running operation in the application.
    """
    
    def __init__(self, parent=None, title="Loading", message="Please wait...", size=50, stylesheet=None):
        """Initialize the loading dialog.
        
        Args:
            parent: Parent widget
            title: Title of the dialog
            message: Message to display
            size: Size of the loading indicator
            stylesheet: Custom stylesheet to apply to the dialog
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        
        # Set window flags based on platform
        # On some platforms, we need to keep the default flags for proper functioning
        system = platform.system().lower()
        if system == "linux":
            # On Linux, we can use custom styling while keeping the title bar
            # But we need to extend the stylesheet for better title bar integration
            linux_titlebar_style = True
        elif system == "windows":
            # Windows handles the custom styling better with default decorations
            linux_titlebar_style = False
        elif system == "darwin":  # macOS
            # macOS needs special handling for proper appearance
            self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            linux_titlebar_style = False
        
        self.setFixedSize(300, 180)
        self.setModal(True)
        
        # Use system colors instead of blue background
        # This will match the application's theme
        base_style = """
            QDialog {
                border: none;
                border-radius: 8px;
            }
            QLabel {
                font-size: 14px;
            }
        """
        
        # Apply platform-specific styles
        if linux_titlebar_style:
            # On Linux, add specific styling for the title bar
            linux_style = """
                QDialog {
                    border: 1px solid #777777;
                }
            """
            base_style += linux_style
        
        # Apply the base style and any custom stylesheet
        self.setStyleSheet(base_style + (stylesheet or ""))
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create loading indicator
        self.loading_indicator = LoadingIndicator(size=size)
        
        # Create message label
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        
        # Add widgets to layout
        indicator_layout = QHBoxLayout()
        indicator_layout.addStretch()
        indicator_layout.addWidget(self.loading_indicator)
        indicator_layout.addStretch()
        
        layout.addLayout(indicator_layout)
        layout.addWidget(self.message_label)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Start the loading animation
        self.loading_indicator.start()
    
    @pyqtSlot(str)
    def set_message(self, message):
        """Update the dialog message.
        
        Args:
            message: New message to display
        """
        if hasattr(self, 'message_label'):
            self.message_label.setText(message)
    
    def closeEvent(self, event):
        """Handle the dialog close event.
        
        Args:
            event: Close event
        """
        # Ensure the timer is stopped before closing
        if hasattr(self, 'loading_indicator'):
            self.loading_indicator.stop()
        
        # Safely close without affecting parent widgets
        event.accept()
    
    @pyqtSlot()
    def safe_close(self):
        """Safely close the dialog with a timer to prevent direct deletion."""
        if hasattr(self, 'loading_indicator'):
            self.loading_indicator.stop()
        
        # Use a short timer to ensure proper context for closing
        # This must be called from the main thread
        QTimer.singleShot(100, self.close) 
    
    @pyqtSlot(str)
    def update_progress(self, message, process_events=True):
        """Update the dialog with progress information.
        
        Args:
            message: Progress message to display
            process_events: Whether to process Qt events after updating
        """
        self.set_message(message)
        if process_events:
            # Process events to ensure UI remains responsive
            QApplication.processEvents()
    
    @pyqtSlot()
    def keep_alive(self):
        """Process events to ensure the dialog remains responsive.
        
        This method can be called periodically during long operations
        to ensure the UI doesn't freeze.
        """
        QApplication.processEvents()
    
    def showEvent(self, event):
        """Override show event to ensure dialog is processed and visible."""
        super().showEvent(event)
        # Process all pending events to make sure dialog appears immediately
        QApplication.processEvents()