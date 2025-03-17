import webbrowser
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette

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
        
        # Download Docker button - apply toggle_button_start styles
        self.download_button = QPushButton('Download Docker')
        self.download_button.clicked.connect(self.open_docker_download)
        self.download_button.setProperty("type", "toggle_button_start")
        button_layout.addWidget(self.download_button)
        
        # Try Again button - apply toggle_button_start styles
        self.retry_button = QPushButton('Try Again')
        self.retry_button.setProperty("type", "toggle_button_start")
        self.retry_button.clicked.connect(self.accept)
        button_layout.addWidget(self.retry_button)
        
        # Quit button - explicitly using toggle_button_stop styles
        self.quit_button = QPushButton('Quit')
        # Set the property to use toggle_button_stop styles
        self.quit_button.setProperty("type", "toggle_button_stop")
        self.quit_button.clicked.connect(self.reject)
        button_layout.addWidget(self.quit_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Apply base dialog styling with system colors
        base_style = """
            QDialog {
                border: none;
                border-radius: 8px;
            }
            QLabel {
                background-color: transparent;
                font-size: 14px;
            }
        """
        
        # Apply theme from parent if available
        if parent and hasattr(parent, '_current_stylesheet'):
            self.setStyleSheet(base_style + parent._current_stylesheet)
        else:
            # Apply default button styles if no parent stylesheet is available
            self.setStyleSheet(base_style + """
                QPushButton[type="toggle_button_start"] {
                    background-color: #1B47F7;
                    color: white;
                    border: 1px solid transparent;
                    border-radius: 15px;
                    padding: 10px 20px;
                    font-size: 16px;
                    min-height: 40px;
                }
                QPushButton[type="toggle_button_start"]:hover {
                    background-color: #4458FF;
                }
                QPushButton[type="toggle_button_stop"] {
                    background-color: #FADC33;
                    color: #C4AC26;
                    border: 1px solid transparent;
                    border-radius: 15px;
                    padding: 10px 20px;
                    font-size: 16px;
                    min-height: 40px;
                }
                QPushButton[type="toggle_button_stop"]:hover {
                    background-color: #FFE138;
                }
            """)
        
        # Center the dialog on the screen
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def open_docker_download(self):
        """Open the Docker download page in the default browser."""
        webbrowser.open('https://www.docker.com/products/docker-desktop')