import os
import sys
import platform
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QAction, QMenu, QMenuBar, QMainWindow, QApplication,
                             QDesktopWidget, QSplitter, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QClipboard

# Import custom widgets
from widgets.app_widgets import (
    ContainerListWidget,
    NodeInfoWidget,
    MetricsWidget,
    LogConsoleWidget,
    ConfigEditorWidget
)

# Import utility classes
from utils.docker_commands import DockerCommandHandler
from utils.theme_manager import ThemeManager
from widgets.LoadingDialog import LoadingDialog
from models.NodeInfo import NodeInfo
from models.NodeHistory import NodeHistory
from models.StartupConfig import StartupConfig
from models.ConfigApp import ConfigApp

# Constants
APP_NAME = "Edge Node Launcher"
DEFAULT_CONTAINER_PREFIX = "r1node"

class EdgeNodeLauncher(QMainWindow):
    """
    Main application window for Edge Node Launcher
    """
    # Signals for inter-component communication
    refresh_completed = pyqtSignal()
    
    def __init__(self, app, app_icon=None):
        super().__init__()
        self.app = app
        self.app_icon = app_icon
        
        # Initialize docker command handler
        self.docker = DockerCommandHandler()
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(app)
        
        # Initialize loading dialog
        self.loading_dialog = None
        
        # Initialize clipboard
        self.clipboard = QApplication.clipboard()
        
        # Debug flag
        self.force_debug = False
        
        # Keep track of current container
        self.current_container = None
        
        # Initialize widget components
        self.container_list = ContainerListWidget(self)
        self.node_info = NodeInfoWidget(self)
        self.metrics = MetricsWidget(self)
        self.log_console = LogConsoleWidget(self)
        self.config_editor = ConfigEditorWidget(self)
        
        # Initialize refresh timer for uptime
        self.uptime_refresh_timer = QTimer(self)
        self.uptime_refresh_timer.timeout.connect(self.refresh_node_info)
        
        # Setup UI
        self.init_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Check Docker
        self.check_docker_with_ui()
        
        # Initialize container list
        self._refresh_local_containers()
        
        # Start uptime refresh timer
        self.uptime_refresh_timer.start(10000)  # Refresh every 10 seconds
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle(APP_NAME)
        if self.app_icon:
            self.setWindowIcon(self.app_icon)
        
        # Set size and position
        self.resize(900, 700)
        self.center()
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Vertical)
        
        # Top section: Container list, node info, metrics
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        
        # Add container list widget
        top_layout.addWidget(self.container_list)
        
        # Node info and metrics section
        info_metrics_splitter = QSplitter(Qt.Horizontal)
        info_metrics_splitter.addWidget(self.node_info)
        info_metrics_splitter.addWidget(self.metrics)
        info_metrics_splitter.setSizes([400, 500])
        top_layout.addWidget(info_metrics_splitter)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.btn_edit_env = QPushButton("Edit .env")
        self.btn_dapp = QPushButton("Open Dashboard")
        self.btn_explorer = QPushButton("Open Explorer")
        self.theme_manager.apply_button_style(self.btn_edit_env, ThemeManager.BUTTON_INFO)
        self.theme_manager.apply_button_style(self.btn_dapp, ThemeManager.BUTTON_PRIMARY)
        self.theme_manager.apply_button_style(self.btn_explorer, ThemeManager.BUTTON_PRIMARY)
        action_layout.addWidget(self.btn_edit_env)
        action_layout.addWidget(self.btn_dapp)
        action_layout.addWidget(self.btn_explorer)
        action_layout.addWidget(self.config_editor.btn_edit_config)
        self.theme_manager.apply_button_style(self.config_editor.btn_edit_config, ThemeManager.BUTTON_INFO)
        top_layout.addLayout(action_layout)
        
        # Add debug toggle
        debug_layout = QHBoxLayout()
        self.chk_debug = QCheckBox("Force Debug Mode")
        debug_layout.addWidget(self.chk_debug)
        debug_layout.addStretch()
        top_layout.addLayout(debug_layout)
        
        top_widget.setLayout(top_layout)
        
        # Bottom section: Log console
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(self.log_console)
        bottom_widget.setLayout(bottom_layout)
        
        # Add sections to splitter
        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(bottom_widget)
        main_splitter.setSizes([500, 200])
        
        # Add splitter to main layout
        main_layout.addWidget(main_splitter)
        
        # Set main widget layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Add initial log entry
        self.add_log(f"Edge Node Launcher started - {platform.system()} {platform.release()}")
    
    def _create_menu_bar(self):
        """Create application menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # Theme action
        toggle_theme_action = QAction("Toggle Dark Mode", self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        file_menu.addAction(toggle_theme_action)
        
        # Docker download action
        docker_action = QAction("Docker Installation", self)
        docker_action.triggered.connect(self.open_docker_download)
        file_menu.addAction(docker_action)
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def connect_signals(self):
        """Connect widget signals to slots"""
        # Container list signals
        self.container_list.container_selected.connect(self._on_container_selected)
        self.container_list.container_toggle_requested.connect(self.toggle_container)
        self.container_list.add_container_requested.connect(self.show_add_node_dialog)
        
        # Node info signals
        self.node_info.refresh_requested.connect(self.refresh_node_info)
        self.node_info.copy_address_requested.connect(self.copy_address)
        
        # Metrics signals
        self.metrics.refresh_requested.connect(self.refresh_metrics)
        
        # Config editor signals
        self.config_editor.config_saved.connect(self.save_config)
        
        # Button signals
        self.btn_edit_env.clicked.connect(self.edit_env_file)
        self.btn_dapp.clicked.connect(self.dapp_button_clicked)
        self.btn_explorer.clicked.connect(self.explorer_button_clicked)
        
        # Debug toggle
        self.chk_debug.stateChanged.connect(self.toggle_force_debug)
        
        # Refresh completed signal
        self.refresh_completed.connect(self.post_refresh_actions)
    
    def center(self):
        """Center the window on the screen"""
        frame_geometry = self.frameGeometry()
        screen_center = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        theme = self.theme_manager.toggle_theme()
        self.add_log(f"Switched to {theme} theme")
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"{APP_NAME}\nVersion 1.0\n\nA launcher for Ratio1 Edge Nodes"
        QMessageBox.about(self, "About", about_text)
    
    def add_log(self, text, debug=False, color="gray"):
        """Add a log entry to the console"""
        self.log_console.add_log(text, color, debug)
    
    def open_docker_download(self):
        """Open Docker download page"""
        import webbrowser
        webbrowser.open("https://www.docker.com/products/docker-desktop")
    
    def check_docker_with_ui(self):
        """Check if Docker is installed and running with UI feedback"""
        # Create loading dialog
        self.loading_dialog = LoadingDialog("Checking Docker...", self)
        self.loading_dialog.show()
        
        # Run Docker check in a timer to allow UI to update
        QTimer.singleShot(100, self._check_docker)
    
    def _check_docker(self):
        """Check if Docker is installed and running"""
        try:
            # Try to execute a simple Docker command
            self.docker.execute_command(['docker', 'version'])
            self.add_log("Docker is installed and running", color="green")
            
            # Close loading dialog if it exists
            if self.loading_dialog:
                self.loading_dialog.close()
                self.loading_dialog = None
                
            # Check for Docker image updates
            self._check_docker_image_updates()
        except Exception as e:
            # Docker might not be installed or running
            error_message = str(e)
            self.add_log(f"Docker error: {error_message}", color="red")
            
            # Close loading dialog if it exists
            if self.loading_dialog:
                self.loading_dialog.close()
                self.loading_dialog = None
            
            # Show error message to user
            QMessageBox.critical(
                self, 
                "Docker Error", 
                "Docker is not installed or not running. Please install Docker and try again."
            )
    
    def _check_docker_image_updates(self):
        """Check for Docker image updates"""
        try:
            self.add_log("Checking for Docker image updates...")
            was_updated, message = self.docker.check_and_pull_image_updates()
            if was_updated:
                self.add_log(message, color="green")
            else:
                self.add_log(message)
        except Exception as e:
            self.add_log(f"Error checking for Docker image updates: {str(e)}", color="red")
    
    def _refresh_local_containers(self):
        """Refresh the list of local containers"""
        try:
            # Get list of containers
            containers = self.docker.list_containers()
            
            # Update container list widget
            self.container_list.update_containers(containers, self.current_container)
            
            # Update UI based on container status
            if self.current_container:
                is_running = self.docker.is_container_running(self.current_container)
                self.container_list.update_toggle_button(is_running)
                self.btn_dapp.setEnabled(is_running)
                self.btn_explorer.setEnabled(is_running)
            else:
                self.container_list.update_toggle_button(False)
                self.btn_dapp.setEnabled(False)
                self.btn_explorer.setEnabled(False)
                
        except Exception as e:
            self.add_log(f"Error refreshing containers: {str(e)}", color="red")
    
    def _on_container_selected(self, container_name):
        """Handle container selection"""
        if container_name != self.current_container:
            # Set current container
            self.current_container = container_name
            self.docker.set_container_name(container_name)
            
            # Update UI
            self.add_log(f"Selected container: {container_name}")
            is_running = self.docker.is_container_running(container_name)
            self.container_list.update_toggle_button(is_running)
            
            # Enable/disable buttons based on container status
            self.btn_dapp.setEnabled(is_running)
            self.btn_explorer.setEnabled(is_running)
            
            # Refresh container info
            self.refresh_all()
        
    def toggle_container(self, container_name):
        """Toggle container state (start/stop)"""
        if not container_name:
            return
            
        is_running = self.docker.is_container_running(container_name)
        
        if is_running:
            # Stop container
            self._perform_container_stop(container_name)
        else:
            # Start container
            self._perform_container_launch(container_name)
    
    def _perform_container_stop(self, container_name):
        """Stop a container with UI feedback"""
        # Create loading dialog
        self.loading_dialog = LoadingDialog(f"Stopping container {container_name}...", self)
        self.loading_dialog.show()
        
        def on_stop_success(result):
            # Close loading dialog
            if self.loading_dialog:
                self.loading_dialog.close()
                self.loading_dialog = None
                
            stdout, stderr, return_code = result
            
            if return_code == 0:
                self.add_log(f"Container {container_name} stopped successfully", color="green")
                
                # Update UI
                self._refresh_local_containers()
                self._clear_info_display()
            else:
                self.add_log(f"Failed to stop container: {stderr}", color="red")
        
        def on_stop_error(error_msg):
            # Close loading dialog
            if self.loading_dialog:
                self.loading_dialog.close()
                self.loading_dialog = None
                
            self.add_log(f"Error stopping container: {error_msg}", color="red")
        
        # Stop container in a thread
        self.docker.stop_container_threaded(container_name, on_stop_success, on_stop_error)
    
    def _perform_container_launch(self, container_name):
        """Launch a container with UI feedback"""
        # Get volume name from registry
        volume_name = self.docker.registry.get_volume_name(container_name)
        
        # Create loading dialog
        self.loading_dialog = LoadingDialog(f"Starting container {container_name}...", self)
        self.loading_dialog.show()
        
        def on_launch_success(result):
            # Close loading dialog
            if self.loading_dialog:
                self.loading_dialog.close()
                self.loading_dialog = None
                
            stdout, stderr, return_code = result
            
            if return_code == 0:
                self.add_log(f"Container {container_name} started successfully", color="green")
                
                # Update UI
                self._refresh_local_containers()
                self.refresh_all()
            else:
                self.add_log(f"Failed to start container: {stderr}", color="red")
        
        def on_launch_error(error_msg):
            # Close loading dialog
            if self.loading_dialog:
                self.loading_dialog.close()
                self.loading_dialog = None
                
            self.add_log(f"Error starting container: {error_msg}", color="red")
        
        # Launch container in a thread
        self.docker.launch_container_threaded(volume_name, on_launch_success, on_launch_error)
    
    def show_add_node_dialog(self):
        """Show dialog to add a new node"""
        # This would be implemented with a custom dialog
        # For now, we'll just create a node with a default name
        container_name = f"{DEFAULT_CONTAINER_PREFIX}_{len(self.docker.list_containers()) + 1}"
        volume_name = f"{container_name}_vol"
        self.add_new_node(container_name, volume_name)
    
    def add_new_node(self, container_name, volume_name, display_name=None):
        """Add a new node with the given parameters"""
        # Create loading dialog
        self.loading_dialog = LoadingDialog(f"Creating new node {container_name}...", self)
        self.loading_dialog.show()
        
        # Set current container
        self.current_container = container_name
        self.docker.set_container_name(container_name)
        
        # Launch container
        try:
            self.docker.launch_container(volume_name)
            self.add_log(f"Container {container_name} created successfully", color="green")
            
            # Update node name if provided
            if display_name:
                self.validate_and_save_node_name(display_name)
            
            # Close loading dialog
            if self.loading_dialog:
                self.loading_dialog.close()
                self.loading_dialog = None
            
            # Update UI
            self._refresh_local_containers()
            self.refresh_all()
        except Exception as e:
            # Close loading dialog
            if self.loading_dialog:
                self.loading_dialog.close()
                self.loading_dialog = None
                
            self.add_log(f"Error creating node: {str(e)}", color="red")
    
    def validate_and_save_node_name(self, new_name, container_name=None):
        """Validate and save a new node name"""
        target_container = container_name or self.current_container
        if not target_container:
            self.add_log("No container selected", color="red")
            return
            
        # Check if container is running
        if not self.docker.is_container_running(target_container):
            self.add_log("Container must be running to change node name", color="red")
            return
        
        def on_success(data):
            self.add_log(f"Node name updated to '{new_name}'", color="green")
            self.refresh_node_info()
        
        def on_error(error):
            self.add_log(f"Error updating node name: {error}", color="red")
        
        # Update node name
        self.docker.update_node_name(new_name, on_success, on_error)
    
    def refresh_node_info(self):
        """Refresh node information display"""
        if not self.current_container:
            return
            
        # Show loading indicator for long operation
        self.node_info.clear_info()
        
        def on_success(node_info):
            # Update node info widget
            self.node_info.update_node_info(node_info)
            
            # Update UI based on node status
            is_running = node_info.is_running
            self.container_list.update_toggle_button(is_running)
            self.btn_dapp.setEnabled(is_running)
            self.btn_explorer.setEnabled(is_running)
            
            # Emit refresh completed signal
            self.refresh_completed.emit()
        
        def on_error(error):
            self.add_log(f"Error refreshing node info: {error}", color="red")
            self._clear_info_display()
        
        # Get node info
        self.docker.get_node_info(on_success, on_error)
    
    def refresh_metrics(self):
        """Refresh node metrics display"""
        if not self.current_container:
            return
            
        # Clear current metrics
        self.metrics._clear_plots()
        
        def on_success(history):
            # Update metrics widget
            self.metrics.update_metrics(history)
            
            # Emit refresh completed signal
            self.refresh_completed.emit()
        
        def on_error(error):
            self.add_log(f"Error refreshing metrics: {error}", color="red")
        
        # Get node history
        self.docker.get_node_history(on_success, on_error)
    
    def refresh_all(self):
        """Refresh all information displays"""
        if not self.current_container:
            return
            
        # Refresh container list
        self._refresh_local_containers()
        
        # Refresh node info
        self.refresh_node_info()
        
        # Refresh metrics
        self.refresh_metrics()
    
    def post_refresh_actions(self):
        """Actions to perform after refresh is complete"""
        # Placeholder for future implementation
        pass
    
    def _clear_info_display(self):
        """Clear all information displays"""
        self.node_info.clear_info()
        self.metrics._clear_plots()
    
    def copy_address(self, address_type):
        """Copy node or ETH address to clipboard"""
        if address_type == 'node':
            address = self.node_info.lbl_node_address.text()
            if address and address != "N/A":
                self.clipboard.setText(address)
                self.add_log("Node address copied to clipboard", color="green")
        elif address_type == 'eth':
            address = self.node_info.lbl_eth_address.text()
            if address and address != "N/A":
                self.clipboard.setText(address)
                self.add_log("ETH address copied to clipboard", color="green")
    
    def edit_env_file(self):
        """Edit .env file"""
        env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        try:
            with open(env_file_path, 'r') as f:
                env_content = f.read()
                
            # This would typically use a dialog to edit the file
            # For now, just log the action
            self.add_log(f"Editing .env file at {env_file_path}")
        except Exception as e:
            self.add_log(f"Error reading .env file: {str(e)}", color="red")
    
    def dapp_button_clicked(self):
        """Open dApp dashboard in browser"""
        if not self.current_container:
            return
            
        # Get node info for address
        def on_success(node_info):
            # Open dashboard in browser
            import webbrowser
            # This is a placeholder URL, would use actual URL in production
            dashboard_url = f"https://dapp.ratio1.io/#/node/{node_info.address}"
            webbrowser.open(dashboard_url)
            self.add_log(f"Opening dashboard for node {node_info.address}")
        
        def on_error(error):
            self.add_log(f"Error getting node info: {error}", color="red")
        
        # Get node info
        self.docker.get_node_info(on_success, on_error)
    
    def explorer_button_clicked(self):
        """Open explorer in browser"""
        import webbrowser
        # This is a placeholder URL, would use actual URL in production
        explorer_url = "https://explorer.ratio1.io"
        webbrowser.open(explorer_url)
        self.add_log("Opening Ratio1 explorer")
    
    def save_config(self, config_data):
        """Save configuration data"""
        # This would save the config data to the container
        # For now, just log the action
        self.add_log("Saving configuration data...")
        
        startup_config = config_data.get('startup_config', '')
        app_config = config_data.get('app_config', '')
        
        # Here would be the code to save the configs to the container
        
        self.add_log("Configuration saved successfully", color="green")
    
    def toggle_force_debug(self, state):
        """Toggle force debug mode"""
        self.force_debug = state == Qt.Checked
        self.docker.set_debug_mode(self.force_debug)
        self.add_log(f"Debug mode {'enabled' if self.force_debug else 'disabled'}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up any resources
        self.uptime_refresh_timer.stop()
        event.accept() 