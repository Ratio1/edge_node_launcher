from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QDialog, QTabWidget, QLabel, QDialogButtonBox)
from PyQt5.QtCore import pyqtSignal

class ConfigEditorWidget(QWidget):
    """
    Widget for editing configuration files
    """
    # Signals
    config_saved = pyqtSignal(dict)  # Emitted when configuration is saved
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize UI components
        self.btn_edit_config = QPushButton("Edit Configuration")
        
        # Setup UI layout
        self.init_ui()
        
        # Connect signals
        self.connect_signals()
    
    def init_ui(self):
        """Initialize the UI components and layout"""
        # Main layout
        layout = QVBoxLayout()
        
        # Add edit config button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_edit_config)
        layout.addLayout(button_layout)
        
        # Set layout
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connect widget signals to slots"""
        self.btn_edit_config.clicked.connect(self.open_config_editor)
    
    def open_config_editor(self, startup_config=None, app_config=None):
        """
        Open the configuration editor dialog
        
        Args:
            startup_config: Startup configuration text
            app_config: App configuration text
        """
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Configuration Files")
        dialog.setMinimumSize(600, 400)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Create startup config tab
        startup_tab = QWidget()
        startup_layout = QVBoxLayout()
        startup_label = QLabel("Startup Configuration:")
        startup_text_edit = QTextEdit()
        if startup_config:
            startup_text_edit.setText(startup_config)
        startup_layout.addWidget(startup_label)
        startup_layout.addWidget(startup_text_edit)
        startup_tab.setLayout(startup_layout)
        
        # Create app config tab
        app_tab = QWidget()
        app_layout = QVBoxLayout()
        app_label = QLabel("App Configuration:")
        app_text_edit = QTextEdit()
        if app_config:
            app_text_edit.setText(app_config)
        app_layout.addWidget(app_label)
        app_layout.addWidget(app_text_edit)
        app_tab.setLayout(app_layout)
        
        # Add tabs to tab widget
        tab_widget.addTab(startup_tab, "Startup Config")
        tab_widget.addTab(app_tab, "App Config")
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._save_config(startup_text_edit, app_text_edit, dialog))
        button_box.rejected.connect(dialog.reject)
        
        # Create dialog layout
        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(tab_widget)
        dialog_layout.addWidget(button_box)
        dialog.setLayout(dialog_layout)
        
        # Show dialog
        dialog.exec_()
    
    def _save_config(self, startup_text_edit, app_text_edit, dialog):
        """
        Save the edited configurations
        
        Args:
            startup_text_edit: QTextEdit containing startup config
            app_text_edit: QTextEdit containing app config
            dialog: Parent dialog
        """
        # Get config text
        startup_config = startup_text_edit.toPlainText()
        app_config = app_text_edit.toPlainText()
        
        # Validate configs
        try:
            # Here we would validate the config format if needed
            # For now, we'll just assume it's valid
            
            # Emit signal with configs
            self.config_saved.emit({
                'startup_config': startup_config,
                'app_config': app_config
            })
            
            # Close dialog
            dialog.accept()
        except Exception as e:
            # Show error message
            # This would typically be handled by the parent application
            print(f"Error saving config: {str(e)}")
    
    def load_config(self, startup_config, app_config):
        """
        Load config text and open the editor
        
        Args:
            startup_config: Startup configuration text
            app_config: App configuration text
        """
        self.open_config_editor(startup_config, app_config) 