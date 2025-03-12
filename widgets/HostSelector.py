from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QPushButton,
    QCheckBox
)
from PyQt5.QtCore import pyqtSignal, QThread, Qt, QTimer
from PyQt5.QtGui import QFont, QColor
import subprocess
import os

from models.AnsibleHosts import AnsibleHostsManager

class SSHCheckThread(QThread):
    status_updated = pyqtSignal(str, bool)  # host, is_online
    
    def __init__(self, host, ssh_command):
        super().__init__()
        self.host = host
        self.ssh_command = ssh_command
        
    def run(self):
        try:
            print(f"Checking SSH connection to {self.host}...")
            print(f"SSH command: {' '.join(self.ssh_command)}")
            
            # Define standard SSH options with appropriate timeouts
            ssh_options = [
                '-o', 'ConnectTimeout=5',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'BatchMode=yes',
                '-o', 'ServerAliveInterval=2',
                '-o', 'UserKnownHostsFile=/dev/null',
            ]
            
            # Create a set of options already in the command
            existing_options = set()
            for i in range(len(self.ssh_command)):
                if self.ssh_command[i] == '-o' and i + 1 < len(self.ssh_command):
                    option_key = self.ssh_command[i+1].split('=')[0]
                    existing_options.add(option_key)
            
            # Only add options that aren't already present
            final_options = []
            for i in range(0, len(ssh_options), 2):
                if i + 1 < len(ssh_options):
                    option_key = ssh_options[i+1].split('=')[0]
                    if option_key not in existing_options:
                        final_options.extend([ssh_options[i], ssh_options[i+1]])
            
            # Build the final command
            cmd = self.ssh_command + final_options + ['echo', 'Connection successful']
            
            print(f"Full command: {' '.join(cmd)}")
            
            # Run the command with a timeout
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                timeout=8,  # 8 second timeout
                text=True
            )
            
            # Check if the command was successful and returned the expected output
            if result.returncode == 0 and 'Connection successful' in result.stdout:
                print(f"SSH connection to {self.host} successful")
                print(f"  stdout: {result.stdout.strip()}")
                self.status_updated.emit(self.host, True)
            else:
                print(f"SSH connection to {self.host} failed with return code {result.returncode}")
                print(f"  stdout: {result.stdout}")
                print(f"  stderr: {result.stderr}")
                self.status_updated.emit(self.host, False)
                
        except subprocess.TimeoutExpired as e:
            print(f"SSH connection to {self.host} timed out after {e.timeout} seconds")
            print(f"Command: {' '.join(e.cmd)}")
            if hasattr(e, 'stdout') and e.stdout:
                print(f"  stdout: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"  stderr: {e.stderr}")
            self.status_updated.emit(self.host, False)
        except subprocess.CalledProcessError as e:
            print(f"SSH connection to {self.host} failed with error: {str(e)}")
            print(f"Return code: {e.returncode}")
            if hasattr(e, 'stdout') and e.stdout:
                print(f"  stdout: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"  stderr: {e.stderr}")
            self.status_updated.emit(self.host, False)
        except Exception as e:
            print(f"SSH check error for {self.host}: {str(e)}")
            import traceback
            traceback.print_exc()
            self.status_updated.emit(self.host, False)

class StatusIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.setAlignment(Qt.AlignCenter)
        self.setProperty("is_online", False)
        self.set_status(False)

    def set_status(self, is_online):
        """Set the status indicator color based on online status."""
        print(f"StatusIndicator.set_status called with is_online={is_online}")
        
        # Set the property first
        self.setProperty("is_online", is_online)
        
        # Then update the style
        color = "#4CAF50" if is_online else "#FF5252"  # Green if online, red if offline
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 6px;
                margin: 2px;
            }}
        """)
        
        # Force style recalculation
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Force update
        self.update()

class HostSelector(QWidget):
    host_selected = pyqtSignal(str)  # Emitted when a host is selected
    mode_changed = pyqtSignal(bool)  # Emitted when mode is changed (True for multi-host)
    host_status_updated = pyqtSignal(str, bool)  # Emitted when host status is updated (host_name, is_online)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hosts_manager = AnsibleHostsManager()
        self.status_threads = {}  # Keep track of status check threads
        self.status_indicators = {}  # Keep track of status indicators
        self._is_pro_mode = False  # Track pro mode state
        self.initUI()
        
        # Set up timer for periodic status checks
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._check_current_host_status)
        self.status_timer.start(10000)  # Check every 10 seconds

    def initUI(self):
        layout = QVBoxLayout()
        
        # Mode selector
        mode_layout = QHBoxLayout()
        self.mode_checkbox = QCheckBox("Multi-host Mode")
        self.mode_checkbox.setFont(QFont("Courier New", 10, QFont.Bold))
        self.mode_checkbox.stateChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_checkbox)
        layout.addLayout(mode_layout)

        # Host selector - vertical layout
        host_layout = QVBoxLayout()
        
        # Label in its own row
        self.host_label = QLabel("Select Host:")
        self.host_label.setFont(QFont("Courier New", 10))
        host_layout.addWidget(self.host_label)
        
        # Dropdown, status indicator and refresh button in a horizontal layout
        controls_layout = QHBoxLayout()
        
        # Create a widget to hold the combobox and status indicator
        combo_container = QWidget()
        combo_layout = QHBoxLayout(combo_container)
        combo_layout.setContentsMargins(0, 0, 0, 0)
        combo_layout.setSpacing(4)
        
        self.host_combo = QComboBox()
        self.host_combo.setFont(QFont("Courier New", 10))
        self.host_combo.setMinimumWidth(200)
        
        # Add status indicator next to the combobox
        self.current_status = StatusIndicator()
        
        combo_layout.addWidget(self.host_combo)
        combo_layout.addWidget(self.current_status)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setFont(QFont("Courier New", 10))
        
        controls_layout.addWidget(combo_container)
        controls_layout.addWidget(self.refresh_button)
        
        host_layout.addLayout(controls_layout)
        layout.addLayout(host_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.refresh_button.clicked.connect(self.refresh_hosts)
        self.host_combo.currentTextChanged.connect(self._on_host_selected)
        
        # Initial state
        self.host_label.setVisible(False)
        self.host_combo.setVisible(False)
        self.refresh_button.setVisible(False)
        self.current_status.setVisible(False)
        
        # Load hosts
        self.refresh_hosts()

    def refresh_hosts(self):
        """Refresh the list of available hosts."""
        current_host = self.host_combo.currentText()  # Store current selection
        
        # Clear and reload hosts from the manager
        self.host_combo.clear()
        hosts = self.hosts_manager.get_host_names()
        for host in hosts:
            self.host_combo.addItem(host)
            
        # Restore previous selection if it exists
        if current_host and current_host in hosts:
            self.host_combo.setCurrentText(current_host)
        elif hosts:
            self.host_combo.setCurrentIndex(0)
            
        # Check status of current host
        if self.host_combo.currentText():
            self.check_host_status(self.host_combo.currentText())
            
    def check_host_status(self, host_name: str):
        """Check if a host is online."""
        if not host_name:
            return
            
        # Check if we're in simple mode - if so, skip SSH checks
        if hasattr(self, '_is_pro_mode') and not self._is_pro_mode:
            print(f"Simple mode: skipping SSH check for host {host_name}")
            # Emit a fake "online" status to avoid blocking the UI
            self.host_status_updated.emit(host_name, True)
            return
            
        try:
            # Stop any running status check
            if hasattr(self, 'status_thread') and self.status_thread and self.status_thread.isRunning():
                try:
                    self.status_thread.terminate()
                    self.status_thread.wait(1000)  # Wait up to 1 second for thread to terminate
                    if self.status_thread.isRunning():
                        print(f"Warning: Status check thread for {host_name} could not be terminated")
                except Exception as e:
                    print(f"Error terminating status thread: {str(e)}")
                
            # Get SSH command for the host
            ssh_command_str = self.hosts_manager.get_ssh_command(host_name)
            if not ssh_command_str:
                print(f"No SSH command available for host: {host_name}")
                self.current_status.setProperty("is_online", False)
                self.current_status.set_status(False)
                self.host_status_updated.emit(host_name, False)
                return
                
            # Get the host configuration to build the command properly
            host_config = self.hosts_manager.get_host(host_name)
            if not host_config:
                print(f"No host configuration found for: {host_name}")
                self.current_status.setProperty("is_online", False)
                self.current_status.set_status(False)
                self.host_status_updated.emit(host_name, False)
                return
                
            # Convert the SSH command string to a list
            # This is important because SSHCheckThread expects a list, not a string
            ssh_command = ssh_command_str.split()
            
            print(f"Using SSH command: {ssh_command}")
            
            # Start status check thread
            self.status_thread = SSHCheckThread(host_name, ssh_command)
            self.status_thread.status_updated.connect(self._on_status_updated)
            self.status_thread.start()
            
        except Exception as e:
            print(f"Error checking host status: {str(e)}")
            import traceback
            traceback.print_exc()
            self.current_status.setProperty("is_online", False)
            self.current_status.set_status(False)
            self.host_status_updated.emit(host_name, False)

    def _on_status_updated(self, host_name, is_online):
        """Handle status update from the check thread.
        
        Updates the status indicator for the current host and emits a signal
        if the status has changed.
        """
        print(f"Received status update for {host_name}: {'online' if is_online else 'offline'}")
        
        # Update the status indicator if this is the current host
        if host_name == self.host_combo.currentText():
            # Check if status has changed
            old_status = self.current_status.property("is_online")
            if old_status != is_online:
                print(f"Host {host_name} status changed: {old_status} -> {is_online}")
            
            # Update the status indicator
            print(f"Setting status indicator for {host_name} to {'online' if is_online else 'offline'}")
            self.current_status.set_status(is_online)
            
            # Force a repaint to ensure the UI updates
            self.current_status.update()
            
            # Emit signal that host status has been updated
            self.host_status_updated.emit(host_name, is_online)

    def get_current_host(self):
        """Get the currently selected host name."""
        return self.host_combo.currentText()

    def _on_host_selected(self, host_name):
        """Handle host selection."""
        if host_name:
            self.check_host_status(host_name)
            if self.mode_checkbox.isChecked():
                self.host_selected.emit(host_name)

    def _on_mode_changed(self, state):
        """Handle mode change."""
        # If in pro mode, force multi-host mode to be enabled
        if self._is_pro_mode and not state:
            self.mode_checkbox.setChecked(True)
            return

        is_multi_host = bool(state)
        self.host_label.setVisible(is_multi_host)
        self.host_combo.setVisible(is_multi_host)
        self.refresh_button.setVisible(is_multi_host)
        self.current_status.setVisible(is_multi_host)
        self.mode_changed.emit(is_multi_host)

    def get_ssh_command(self, host_name: str) -> str:
        """Get SSH command for the selected host."""
        return self.hosts_manager.get_ssh_command(host_name)

    def apply_stylesheet(self, is_dark_theme: bool):
        """Apply theme-specific styles."""
        if is_dark_theme:
            # Dark theme
            text_color = "white"
            bg_color = "#2b2b2b"
            border_color = "#555555"
            hover_color = "#3b3b3b"
            
            # Style for checkbox
            checkbox_style = f"""
                QCheckBox {{
                    color: {text_color};
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid {border_color};
                    border-radius: 4px;
                    background: {bg_color};
                }}
                QCheckBox::indicator:checked {{
                    background: #4CAF50;
                    border: 2px solid #4CAF50;
                }}
                QCheckBox::indicator:hover {{
                    border: 2px solid #4CAF50;
                }}
            """
            
            # Style for combobox
            combobox_style = f"""
                QComboBox {{
                    color: {text_color};
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    padding: 4px;
                    min-width: 100px;
                }}
                QComboBox:hover {{
                    background-color: {hover_color};
                    border: 1px solid #4CAF50;
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 20px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid {text_color};
                    margin-right: 8px;
                }}
                QComboBox QAbstractItemView {{
                    color: {text_color};
                    background-color: {bg_color};
                    selection-background-color: {hover_color};
                    selection-color: {text_color};
                }}
            """
            
            # Style for refresh button
            button_style = f"""
                QPushButton {{
                    color: {text_color};
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    padding: 4px 12px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                    border: 1px solid #4CAF50;
                }}
            """
        else:
            # Light theme
            text_color = "black"
            bg_color = "white"
            border_color = "#cccccc"
            hover_color = "#f5f5f5"
            
            # Style for checkbox
            checkbox_style = f"""
                QCheckBox {{
                    color: {text_color};
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid {border_color};
                    border-radius: 4px;
                    background: {bg_color};
                }}
                QCheckBox::indicator:checked {{
                    background: #4CAF50;
                    border: 2px solid #4CAF50;
                }}
                QCheckBox::indicator:hover {{
                    border: 2px solid #4CAF50;
                }}
            """
            
            # Style for combobox
            combobox_style = f"""
                QComboBox {{
                    color: {text_color};
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    padding: 4px;
                    min-width: 100px;
                }}
                QComboBox:hover {{
                    background-color: {hover_color};
                    border: 1px solid #4CAF50;
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 20px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid {text_color};
                    margin-right: 8px;
                }}
                QComboBox QAbstractItemView {{
                    color: {text_color};
                    background-color: {bg_color};
                    selection-background-color: {hover_color};
                    selection-color: {text_color};
                }}
            """
            
            # Style for refresh button
            button_style = f"""
                QPushButton {{
                    color: {text_color};
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    padding: 4px 12px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                    border: 1px solid #4CAF50;
                }}
            """

        # Apply styles
        self.mode_checkbox.setStyleSheet(checkbox_style)
        self.host_combo.setStyleSheet(combobox_style)
        self.refresh_button.setStyleSheet(button_style)
        self.host_label.setStyleSheet(f"color: {text_color};")

        self.host_label.setStyleSheet(f"color: {text_color};")

    def is_multi_host_mode(self) -> bool:
        """Check if multi-host mode is enabled"""
        return self.mode_checkbox.isChecked()

    def set_multi_host_mode(self, enabled: bool):
        """Set multi-host mode state"""
        if self.mode_checkbox.isChecked() != enabled:
            self.mode_checkbox.setChecked(enabled)  # This will trigger the mode_changed signal via _on_mode_changed 

    def set_pro_mode(self, enabled: bool):
        """Set pro mode state and update UI accordingly"""
        self._is_pro_mode = enabled
        if enabled:
            # Force multi-host mode when pro mode is enabled
            self.mode_checkbox.setChecked(True)
            self.mode_checkbox.setEnabled(False)  # Disable checkbox in pro mode
        else:
            self.mode_checkbox.setEnabled(True)  # Re-enable checkbox in simple mode 

    def _check_current_host_status(self):
        """Periodically check the status of the current host."""
        # Skip periodic checks in Simple mode
        if hasattr(self, '_is_pro_mode') and not self._is_pro_mode:
            return
            
        if self.isVisible() and self.host_combo.isVisible():
            current_host = self.host_combo.currentText()
            if current_host:
                self.check_host_status(current_host) 