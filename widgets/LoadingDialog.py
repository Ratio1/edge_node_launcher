from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QApplication
)
from PyQt5.QtCore import Qt, QTimer
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
        
        # Set consistent blue background color for the entire dialog
        # Using QColor from the blue palette that matches the app theme
        blue_bg_color = "#1a5fb4"  # A nice medium blue that works well with both dark/light text
        text_color = "white"  # White text for better contrast on blue
        
        # Apply stylesheet with blue background
        base_style = f"""
            QDialog {{
                background-color: {blue_bg_color};
                color: {text_color};
                border: none;
            }}
            QLabel {{
                color: {text_color};
                background-color: transparent;
            }}
            QDialog::title {{
                background-color: {blue_bg_color};
            }}
        """
        
        # Add Linux-specific title bar styling if needed
        if linux_titlebar_style:
            self.setStyleSheet(base_style + f"""
                QDialog::title {{
                    background-color: {blue_bg_color};
                }}
                QDialogButtonBox {{
                    background-color: {blue_bg_color};
                }}
                QDialogButtonBox QPushButton {{
                    background-color: {blue_bg_color};
                    color: {text_color};
                }}
            """)
        else:
            self.setStyleSheet(base_style)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)  # Set layout early so it's available
        
        # Loading indicator (green spinner looks good on blue background)
        self.loading_indicator = LoadingIndicator(size=size)
        self.loading_indicator.setColor(QColor("lightgreen"))  # Set spinner color for better visibility
        self.loading_indicator.start()
        
        # Labels
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {text_color}; padding: 5px;")
        title_label.setAlignment(Qt.AlignCenter)
        
        self.info_label = QLabel(message)
        self.info_label.setStyleSheet(f"color: {text_color}; font-size: 14px;")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout with some spacing
        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addWidget(self.loading_indicator, 0, Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.info_label)
        
        # Add margin to layout
        layout.setContentsMargins(20, 20, 20, 20)
    
    def set_message(self, message):
        """Update the dialog message.
        
        Args:
            message: New message to display
        """
        if hasattr(self, 'info_label'):
            self.info_label.setText(message)
            # Process events to ensure UI updates immediately
            QApplication.processEvents()
    
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
    
    def safe_close(self):
        """Safely close the dialog with a timer to prevent direct deletion."""
        if hasattr(self, 'loading_indicator'):
            self.loading_indicator.stop()
        
        # Use a short timer to ensure proper context for closing
        QTimer.singleShot(100, self.close) 