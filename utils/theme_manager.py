from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import os

class ThemeManager:
    """
    Manages application theming and styling
    """
    # Theme constants
    DARK_THEME = "dark"
    LIGHT_THEME = "light"
    
    # Style constants
    BUTTON_PRIMARY = "primary"
    BUTTON_SUCCESS = "success"
    BUTTON_DANGER = "danger"
    BUTTON_WARNING = "warning"
    BUTTON_INFO = "info"
    BUTTON_DEFAULT = "default"
    
    def __init__(self, app):
        """
        Initialize the theme manager
        
        Args:
            app: QApplication instance
        """
        self.app = app
        self.current_theme = self.LIGHT_THEME
        self.styles = {}
        self._init_styles()
    
    def _init_styles(self):
        """Initialize button styles for different themes"""
        # Light theme button styles
        self.styles[self.LIGHT_THEME] = {
            self.BUTTON_PRIMARY: "QPushButton { background-color: #3498db; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #2980b9; } QPushButton:disabled { background-color: #cccccc; }",
            self.BUTTON_SUCCESS: "QPushButton { background-color: #2ecc71; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #27ae60; } QPushButton:disabled { background-color: #cccccc; }",
            self.BUTTON_DANGER: "QPushButton { background-color: #e74c3c; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #c0392b; } QPushButton:disabled { background-color: #cccccc; }",
            self.BUTTON_WARNING: "QPushButton { background-color: #f39c12; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #d35400; } QPushButton:disabled { background-color: #cccccc; }",
            self.BUTTON_INFO: "QPushButton { background-color: #9b59b6; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #8e44ad; } QPushButton:disabled { background-color: #cccccc; }",
            self.BUTTON_DEFAULT: "QPushButton { background-color: #ecf0f1; color: #34495e; border: 1px solid #bdc3c7; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #bdc3c7; } QPushButton:disabled { background-color: #ecf0f1; color: #7f8c8d; }"
        }
        
        # Dark theme button styles
        self.styles[self.DARK_THEME] = {
            self.BUTTON_PRIMARY: "QPushButton { background-color: #3498db; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #2980b9; } QPushButton:disabled { background-color: #2c3e50; }",
            self.BUTTON_SUCCESS: "QPushButton { background-color: #2ecc71; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #27ae60; } QPushButton:disabled { background-color: #2c3e50; }",
            self.BUTTON_DANGER: "QPushButton { background-color: #e74c3c; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #c0392b; } QPushButton:disabled { background-color: #2c3e50; }",
            self.BUTTON_WARNING: "QPushButton { background-color: #f39c12; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #d35400; } QPushButton:disabled { background-color: #2c3e50; }",
            self.BUTTON_INFO: "QPushButton { background-color: #9b59b6; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #8e44ad; } QPushButton:disabled { background-color: #2c3e50; }",
            self.BUTTON_DEFAULT: "QPushButton { background-color: #34495e; color: white; border: 1px solid #2c3e50; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #2c3e50; } QPushButton:disabled { background-color: #2c3e50; color: #7f8c8d; }"
        }
    
    def set_theme(self, theme):
        """
        Set the application theme
        
        Args:
            theme: Theme name (DARK_THEME or LIGHT_THEME)
        """
        # Save theme setting
        self.current_theme = theme
        
        # Apply the theme
        self._apply_theme()
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        new_theme = self.LIGHT_THEME if self.current_theme == self.DARK_THEME else self.DARK_THEME
        self.set_theme(new_theme)
        return new_theme
    
    def _apply_theme(self):
        """Apply the current theme to the application"""
        if self.current_theme == self.DARK_THEME:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
    
    def _apply_dark_theme(self):
        """Apply dark theme to the application"""
        # Create dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.black)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        
        # Apply palette
        self.app.setPalette(palette)
    
    def _apply_light_theme(self):
        """Apply light theme to the application"""
        # Create light palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.black)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.Highlight, QColor(51, 153, 255))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        # Apply palette
        self.app.setPalette(palette)
    
    def get_button_style(self, style_type):
        """
        Get a button style for the current theme
        
        Args:
            style_type: Type of button style (e.g., BUTTON_PRIMARY)
            
        Returns:
            str: CSS style string for the button
        """
        return self.styles.get(self.current_theme, {}).get(style_type, self.styles[self.current_theme][self.BUTTON_DEFAULT])
    
    def apply_button_style(self, button, style_type):
        """
        Apply a button style to a button widget
        
        Args:
            button: QPushButton instance
            style_type: Type of button style (e.g., BUTTON_PRIMARY)
        """
        style = self.get_button_style(style_type)
        button.setStyleSheet(style)
    
    def is_dark_theme(self):
        """
        Check if dark theme is active
        
        Returns:
            bool: True if dark theme is active, False otherwise
        """
        return self.current_theme == self.DARK_THEME 