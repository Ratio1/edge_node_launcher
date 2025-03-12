import webbrowser
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QApplication)
from PyQt5.QtCore import Qt

class DockerCheckDialog(QDialog):
    def __init__(self, parent=None, icon=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Docker Check")
        if icon:
            self.setWindowIcon(icon)
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Message label
        self.message = QLabel(
            'Docker is not installed or not running.\n'
            'Please install Docker and start it to continue.'
        )
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Download Docker button
        self.download_button = QPushButton('Download Docker')
        self.download_button.clicked.connect(self.open_docker_download)
        button_layout.addWidget(self.download_button)
        
        # Try Again button
        self.retry_button = QPushButton('Try Again')
        self.retry_button.setProperty("type", "confirm")  # Set property for styling
        self.retry_button.clicked.connect(self.accept)
        button_layout.addWidget(self.retry_button)
        
        # Quit button
        self.quit_button = QPushButton('Quit')
        self.quit_button.setProperty("type", "cancel")  # Set property for styling
        self.quit_button.clicked.connect(self.reject)
        button_layout.addWidget(self.quit_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Apply theme from parent if available
        if parent and hasattr(parent, '_current_stylesheet'):
            self.setStyleSheet(parent._current_stylesheet)
        
        # Center the dialog on the screen
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def open_docker_download(self):
        """Open the Docker download page in the default browser."""
        webbrowser.open('https://www.docker.com/products/docker-desktop') 