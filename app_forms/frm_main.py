import sys
import platform
import os
import json
import dataclasses
import subprocess

from datetime import datetime, timedelta
from time import time
from typing import Optional
import re

from PyQt5.QtWidgets import (
  QApplication,
  QWidget,
  QVBoxLayout,
  QPushButton,
  QLabel,
  QGridLayout,
  QFrame,
  QTextEdit,
  QDialog,
  QHBoxLayout,
  QSpacerItem,
  QSizePolicy,
  QCheckBox,
  QStyle,
  QComboBox,
  QMessageBox,
  QFileDialog,
  QLineEdit, QGroupBox,
  QGraphicsDropShadowEffect,
  QTabWidget,
  QDialogButtonBox,
  QPlainTextEdit,
  QMenuBar,
  QMenu,
  QAction,
  QSplitter,
  QProgressBar,
  QDesktopWidget,
  QMainWindow,
  QScrollArea,
  QToolButton,
  QTextBrowser,
  QListWidget,
  QGridLayout,
  QStackedWidget,
  QFormLayout,
  QListWidgetItem
)
from PyQt5.QtCore import (
    Qt, QTimer, QSize, QThread, QObject, pyqtSignal, QUrl, QSettings,
    QProcess, QPropertyAnimation, QModelIndex, QSortFilterProxyModel
)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter
import pyqtgraph as pg
from PyQt5.QtSvg import QSvgRenderer

from models.NodeInfo import NodeInfo
from models.NodeHistory import NodeHistory
from widgets.ToastWidget import ToastWidget, NotificationType
from utils.const import *
from utils.docker import _DockerUtilsMixin
from utils.docker_commands import DockerCommandHandler
from utils.updater import _UpdaterMixin
from utils.docker_utils import get_volume_name, generate_container_name
from utils.config_manager import ConfigManager, ContainerConfig

from utils.icon import ICON_BASE64

from app_forms.frm_utils import (
  get_icon_from_base64, DateAxisItem, LoadingIndicator
)

from ver import __VER__ as __version__
from widgets.dialogs.AuthorizedAddressedDialog import AuthorizedAddressesDialog
from models.AllowedAddress import AllowedAddress, AllowedAddressList
from models.StartupConfig import StartupConfig
from models.ConfigApp import ConfigApp
from widgets.HostSelector import HostSelector
from widgets.ModeSwitch import ModeSwitch
from widgets.dialogs.DockerCheckDialog import DockerCheckDialog
from widgets.CenteredComboBox import CenteredComboBox
from widgets.LoadingDialog import LoadingDialog


def get_platform_and_os_info():
  platform_info = platform.platform()
  os_name = platform.system()
  os_version = platform.version()
  return platform_info, os_name, os_version

def log_with_color(message, color="gray"):
  """
    Log message with color in the terminal.
    :param message: Message to log
    :param color: Color of the message
  """
  color_codes = {
    "yellow": "\033[93m",
    "red": "\033[91m",
    "gray": "\033[90m",
    "light": "\033[97m",
    "green": "\033[92m",
    "blue" : "\033[94m",
    "cyan" : "\033[96m",
  }
  start_color = color_codes.get(color, "\033[90m")
  end_color = "\033[0m"
  print(f"{start_color}{message}{end_color}", flush=True)
  return

class EdgeNodeLauncher(QWidget, _DockerUtilsMixin, _UpdaterMixin):
  def __init__(self, app_icon=None):
    self.logView = None
    self.log_buffer = []
    self.__force_debug = False
    super().__init__()

    # Set current environment (you'll need to get this from your configuration)
    self.current_environment = DEFAULT_ENVIRONMENT

    self.__current_node_uptime = -1
    self.__current_node_epoch = -1
    self.__current_node_epoch_avail = -1
    self.__current_node_ver = -1
    self.__display_uptime = None

    self._current_stylesheet = DARK_STYLESHEET  # Default to dark theme
    self.__last_plot_data = None
    self.__last_auto_update_check = 0
    self.__last_docker_image_check = 0
    
    self.__version__ = __version__
    self.__last_timesteps = []
    self._icon = get_icon_from_base64(ICON_BASE64)
    self.setWindowIcon(self._icon)
    
    # Initialize the button colors based on current theme
    self.init_button_colors()

    self.runs_in_production = self.is_running_in_production()

    # Set the application icon - use the provided icon directly
    self._icon = app_icon
    if self._icon is None:
      # Only fall back to base64 if no icon provided
      from utils.icon_helper import get_app_icon
      self._icon = get_app_icon()
      self.add_log("Loaded application icon via helper", debug=True)
    else:
      self.add_log("Using provided application icon", debug=True)

    # Apply window icon immediately
    self.setWindowIcon(self._icon)

    # Initialize config manager for container configurations
    self.config_manager = ConfigManager()

    # Initialize force debug from saved settings
    self.__force_debug = self.config_manager.get_force_debug()

    self.initUI()
    
    # Set initial theme class
    self.force_debug_checkbox.setProperty('class', 'dark')

    self.__cwd = os.getcwd()
    
    self.showMaximized()
    self.add_log(f'Edge Node Launcher v{self.__version__} started. Running in production: {self.runs_in_production}, running with debugger: {self.runs_with_debugger()}, running in ipython: {self.runs_from_ipython()},  running from exe: {not self.not_running_from_exe()}')
    self.add_log(f'Running from: {self.__cwd}')

    platform_info, os_name, os_version = get_platform_and_os_info()
    self.add_log(f'Platform: {platform_info}')
    self.add_log(f'OS: {os_name} {os_version}')

    # Check Docker and handle UI interactions
    if not self.check_docker_with_ui():
        self.close()
        sys.exit(1)

    self.docker_initialize()
    self.docker_handler = DockerCommandHandler(DOCKER_CONTAINER_NAME)

    # Initialize container list
    self.refresh_container_list()

    # Set initial container status
    self.container_last_run_status = False
    
    # Check if container is running and update UI accordingly
    if self.is_container_running():
        self.add_log("Container is running on startup, updating UI", debug=True)
        self.post_launch_setup()
        self.refresh_local_address()
        self.plot_data()  # Initial plot
    else:
        self.add_log("No running container found on startup", debug=True)

    # Ensure button state is correct
    self.update_toggle_button_text()

    self.timer = QTimer(self)
    self.timer.timeout.connect(self.refresh_all)
    self.timer.start(REFRESH_TIME)  # Refresh every 10 seconds
    self.toast = ToastWidget(self)

    # Initialize copy button icons based on current theme
    self.update_copy_button_icons()

  def init_button_colors(self):
    """Initialize or update button colors based on current theme"""
    is_dark = self._current_stylesheet == DARK_STYLESHEET
    colors = DARK_COLORS if is_dark else LIGHT_COLORS
    
    self.button_colors = {
        'start': {
            'bg': colors['toggle_button_start_bg'],
            'hover': colors['toggle_button_start_hover'],
            'text': colors['toggle_button_start_text'],
            'border': colors['toggle_button_start_border']
        },
        'stop': {
            'bg': colors['toggle_button_stop_bg'],
            'hover': colors['toggle_button_stop_hover'],
            'text': colors['toggle_button_stop_text'],
            'border': colors['toggle_button_stop_border']
        },
        'disabled': {
            'bg': colors['toggle_button_disabled_bg'],
            'hover': colors['toggle_button_disabled_hover'],
            'text': colors['toggle_button_disabled_text'],
            'border': colors['toggle_button_disabled_border']
        },
        'toggle_start': {
            'bg': colors['toggle_button_start_bg'],
            'hover': colors['toggle_button_start_hover'],
            'text': colors['toggle_button_start_text'],
            'border': colors['toggle_button_start_border']
        },
        'toggle_stop': {
            'bg': colors['toggle_button_stop_bg'],
            'hover': colors['toggle_button_stop_hover'],
            'text': colors['toggle_button_stop_text'],
            'border': colors['toggle_button_stop_border']
        },
        'toggle_disabled': {
            'bg': colors['toggle_button_disabled_bg'],
            'text': colors['toggle_button_disabled_text'],
            'border': colors['toggle_button_disabled_border'],
            'hover': colors['toggle_button_disabled_hover']
        }
    }

  def apply_button_style(self, button, style_type):
    """Apply button style based on button colors and state
    
    Args:
        button: The button to style
        style_type: The type of style to apply ('start', 'stop', 'disabled')
    """
    if style_type == 'disabled':
        button.setStyleSheet(f"background-color: {self.button_colors['disabled']['bg']}; color: {self.button_colors['disabled']['text']};")
        return
    
    # Check if the style type has a hover property
    has_hover = 'hover' in self.button_colors[style_type]
    
    hover_css = f"""
        QPushButton:hover {{
            background-color: {self.button_colors[style_type]['hover']};
        }}
    """ if has_hover else ""
    
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {self.button_colors[style_type]['bg']};
            color: {self.button_colors[style_type]['text']};
            border: 2px solid {self.button_colors[style_type]['border']};
            padding: 5px 10px;
            border-radius: 15px;
        }}
        {hover_css}
    """)

  def check_docker_with_ui(self):
    """Check Docker status and handle UI interactions.
    
    Returns:
        bool: True if Docker is ready to use, False otherwise
    """
    while True:
        is_installed, is_running, error_msg = super().check_docker()
        if is_installed and is_running:
            return True
            
        # Show the Docker check dialog
        dialog = DockerCheckDialog(self, self._icon)
        if error_msg:
            dialog.message.setText(error_msg + '\nPlease install/start Docker and try again.')
        
        result = dialog.exec_()
        if result == QDialog.Accepted:  # User clicked "Try Again"
            continue
        else:  # User clicked "Quit" or closed the dialog
            return False
  
  @staticmethod
  def not_running_from_exe():
    """
    Checks if the script is running from a PyInstaller-generated executable.

    Returns
    -------
    bool
      True if running from a PyInstaller executable, False otherwise.
    """
    return not (hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'))
  
  @staticmethod
  def runs_from_ipython():
    try:
      __IPYTHON__
      return True
    except NameError:
      return False
    
  @staticmethod
  def runs_with_debugger():
    gettrace = getattr(sys, 'gettrace', None)
    if gettrace is None:
      return False
    else:
      return not gettrace() is None    
    
  def is_running_in_production(self):
    return not (self.runs_from_ipython() or self.runs_with_debugger() or self.not_running_from_exe())
  
  
  def add_log(self, line, debug=False, color="gray"):
    show = (debug and not self.runs_in_production) or not debug
    show = show or self.__force_debug
    if show:      
      timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
      line = f'{timestamp} {line}'
      if self.logView is not None:
        self.logView.append(line)
      else:
        self.log_buffer.append(line)
      QApplication.processEvents()  # Flush the event queue
      if debug or self.__force_debug:
        log_with_color(line, color=color)
    return  
  
  def center(self):
    screen_geometry = QApplication.desktop().screenGeometry()
    x = (screen_geometry.width() - self.width()) // 2
    y = (screen_geometry.height() - self.height()) // 2
    self.move(x, y)
    return

  def set_windows_taskbar_icon(self):
    # Set app id for Windows taskbar
    if os.name == 'nt':  # Windows
      try:
        import ctypes
        myappid = 'ratio1.edge_node_launcher'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.add_log(f"Set Windows taskbar AppUserModelID to {myappid}", debug=True)
      except Exception as e:
        self.add_log(f"Error setting Windows AppUserModelID: {str(e)}", debug=True)

    # Apply icon to window and application
    self.setWindowIcon(self._icon)
    app = QApplication.instance()
    if app:
      app.setWindowIcon(self._icon)
      self.add_log(f"Applied icon to application and window", debug=True)
    return

  def initUI(self):
    HEIGHT = 1100
    self.setWindowTitle(WINDOW_TITLE)
    self.setGeometry(0, 0, 1800, HEIGHT)
    self.center()

    # Set the icon right at the beginning
    self.setWindowIcon(self._icon)
    self.set_windows_taskbar_icon()

    # Create the main layout
    main_layout = QVBoxLayout(self)
    main_layout.setContentsMargins(10, 10, 10, 10)  # Add padding around the entire window content
    main_layout.setSpacing(0)

    # Content area with overlay for mode switch
    content_widget = QWidget()
    content_widget.setLayout(QHBoxLayout())
    content_widget.layout().setContentsMargins(0, 0, 0, 0)
    content_widget.layout().setSpacing(0)

    # Left menu layout with fixed width
    menu_widget = QWidget()
    menu_widget.setFixedWidth(300)  # Set the fixed width here
    menu_layout = QVBoxLayout(menu_widget)
    menu_layout.setAlignment(Qt.AlignTop)
    menu_layout.setContentsMargins(0, 2, 0, 2)  # Small top and bottom margins, no side margins
    
    top_button_area = QVBoxLayout()
    top_button_area.setObjectName("topButtonArea")
    top_button_area.setContentsMargins(5, 0, 5, 4)  # Add left and right margins (5px)

    # Container selector area
    container_selector_layout = QVBoxLayout()  # Changed to QVBoxLayout
    # container_selector_layout.setContentsMargins(5, 4, 5, 4)  # Add left and right margins (5px)
    # Add Node button
    self.add_node_button = QPushButton("Add New Node")
    self.add_node_button.clicked.connect(self.show_add_node_dialog)
    self.add_node_button.setObjectName("addNodeButton")
    container_selector_layout.addWidget(self.add_node_button)

    # Container dropdown
    self.container_combo = CenteredComboBox()
    self.container_combo.setFont(QFont("Courier New", 10))
    self.container_combo.currentTextChanged.connect(self._on_container_selected)
    self.container_combo.setMinimumHeight(32)  # Make dropdown slightly taller
    
    # Set the initial theme directly
    is_dark = self._current_stylesheet == DARK_STYLESHEET
    if hasattr(self.container_combo, 'set_theme'):
        self.container_combo.set_theme(is_dark)
    container_selector_layout.addWidget(self.container_combo)
    
    top_button_area.addLayout(container_selector_layout)

    # Launch Edge Node button
    self.toggleButton = QPushButton(LAUNCH_CONTAINER_BUTTON_TEXT)
    self.toggleButton.setObjectName("startNodeButton")
    self.toggleButton.clicked.connect(self.toggle_container)
    self.apply_button_style(self.toggleButton, 'toggle_start')
    top_button_area.addWidget(self.toggleButton)

    # Docker download button right under Launch Edge Node
    self.docker_download_button = QPushButton(DOWNLOAD_DOCKER_BUTTON_TEXT)
    self.docker_download_button.setToolTip(DOCKER_DOWNLOAD_TOOLTIP)
    self.docker_download_button.clicked.connect(self.open_docker_download)
    # top_button_area.addWidget(self.docker_download_button)

    # dApp button
    self.dapp_button = QPushButton(DAPP_BUTTON_TEXT)
    self.dapp_button.clicked.connect(self.dapp_button_clicked)
    top_button_area.addWidget(self.dapp_button)

    # Explorer button
    self.explorer_button = QPushButton(EXPLORER_BUTTON_TEXT)
    self.explorer_button.clicked.connect(self.explorer_button_clicked)
    top_button_area.addWidget(self.explorer_button)
    
    # Add some spacing between the explorer button and info box
    top_button_area.addSpacing(7)
    
    # Info box
    info_box = QGroupBox()
    info_box.setObjectName("infoBox")
    info_box.setContentsMargins(5, 0, 5, 0)  # Add left and right margins directly to the widget
    info_box_layout = QVBoxLayout()
    info_box_layout.setContentsMargins(5, 6, 5, 8)  # Left, Top, Right, Bottom margins inside the box

    # Add loading indicator
    self.loading_indicator = LoadingIndicator(size=30)
    self.loading_indicator.hide()  # Initially hidden
    loading_layout = QHBoxLayout()
    loading_layout.addStretch()
    loading_layout.addWidget(self.loading_indicator)
    loading_layout.addStretch()
    info_box_layout.addLayout(loading_layout)

    # Address display with copy button
    addr_layout = QHBoxLayout()
    self.addressDisplay = QLabel('')
    self.addressDisplay.setFont(QFont("Courier New"))
    self.addressDisplay.setObjectName("infoBoxText")
    addr_layout.addWidget(self.addressDisplay)
    
    # Add copy address button
    self.copyAddrButton = QPushButton()
    self.copyAddrButton.setToolTip(COPY_ADDRESS_TOOLTIP)
    self.copyAddrButton.clicked.connect(self.copy_address)
    self.copyAddrButton.setFixedSize(28, 28)  # Slightly larger button size
    self.copyAddrButton.setObjectName("copyAddrButton")
    self.copyAddrButton.hide()  # Initially hidden
    addr_layout.addWidget(self.copyAddrButton)
    addr_layout.addStretch()
    info_box_layout.addLayout(addr_layout)

    # ETH address display with copy button
    eth_addr_layout = QHBoxLayout()
    self.ethAddressDisplay = QLabel('')
    self.ethAddressDisplay.setObjectName("infoBoxText")
    self.ethAddressDisplay.setFont(QFont("Courier New"))
    eth_addr_layout.addWidget(self.ethAddressDisplay)
    
    # Add copy ethereum address button
    self.copyEthButton = QPushButton()
    self.copyEthButton.setToolTip(COPY_ETH_ADDRESS_TOOLTIP)
    self.copyEthButton.clicked.connect(self.copy_eth_address)
    self.copyEthButton.setFixedSize(28, 28)  # Slightly larger button size
    self.copyEthButton.setObjectName("copyEthButton")
    self.copyEthButton.hide()  # Initially hidden
    eth_addr_layout.addWidget(self.copyEthButton)
    eth_addr_layout.addStretch()
    info_box_layout.addLayout(eth_addr_layout)

    self.nameDisplay = QLabel('')
    self.nameDisplay.setFont(QFont("Courier New"))
    self.nameDisplay.setObjectName("infoBoxText")
    info_box_layout.addWidget(self.nameDisplay)

    self.node_uptime = QLabel(UPTIME_LABEL)
    self.node_uptime.setObjectName("infoBoxText")
    self.node_uptime.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_uptime)

    self.node_epoch = QLabel(EPOCH_LABEL)
    self.node_epoch.setObjectName("infoBoxText")
    self.node_epoch.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_epoch)

    self.node_epoch_avail = QLabel(EPOCH_AVAIL_LABEL)
    self.node_epoch_avail.setObjectName("infoBoxText")
    self.node_epoch_avail.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_epoch_avail)

    self.node_version = QLabel()
    self.node_version.setObjectName("infoBoxText")
    self.node_version.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_version)
    
    info_box.setLayout(info_box_layout)
    top_button_area.addWidget(info_box)
    
    menu_layout.addLayout(top_button_area)

    # Spacer to push bottom_button_area to the bottom
    menu_layout.addSpacerItem(QSpacerItem(20, int(HEIGHT * 0.75), QSizePolicy.Minimum, QSizePolicy.Expanding))

    # Bottom button area
    bottom_button_area = QVBoxLayout()
    bottom_button_area.setObjectName("bottomButtonArea")
    bottom_button_area.setContentsMargins(5, 4, 5, 0)  # Add left and right margins (5px)
    
    ## buttons
    # Add Rename Node button
    self.renameNodeButton = QPushButton(RENAME_NODE_BUTTON_TEXT)
    self.renameNodeButton.clicked.connect(self.show_rename_dialog)
    bottom_button_area.addWidget(self.renameNodeButton)

    # Toggle theme button
    self.themeToggleButton = QPushButton(LIGHT_DASHBOARD_BUTTON_TEXT)
    # self.themeToggleButton.setCheckable(True)
    self.themeToggleButton.clicked.connect(self.toggle_theme)
    bottom_button_area.addWidget(self.themeToggleButton)    
    
    # add a checkbox item to force debug
    self.force_debug_checkbox = QCheckBox('Force Debug Mode')
    self.force_debug_checkbox.setChecked(self.__force_debug)  # Set initial state from config
    self.force_debug_checkbox.setFont(QFont("Courier New", 9, QFont.Bold))
    
    # Apply custom styling to the debug checkbox
    is_dark = self._current_stylesheet == DARK_STYLESHEET
    if is_dark:
        self.force_debug_checkbox.setStyleSheet(DETAILED_CHECKBOX_STYLE.format(
            debug_checkbox_color=DARK_COLORS["debug_checkbox_color"]
        ))
    else:
        self.force_debug_checkbox.setStyleSheet(DETAILED_CHECKBOX_STYLE.format(
            debug_checkbox_color=LIGHT_COLORS["debug_checkbox_color"]
        ))
    
    self.force_debug_checkbox.stateChanged.connect(self.toggle_force_debug)
    bottom_button_area.addWidget(self.force_debug_checkbox)

    bottom_button_area.addStretch()
    menu_layout.addLayout(bottom_button_area)
    
    content_widget.layout().addWidget(menu_widget)

    # Right panel with mode switch overlay
    right_container = QWidget()
    right_container_layout = QVBoxLayout(right_container)
    right_container_layout.setContentsMargins(0, 0, 0, 29)
    right_container_layout.setSpacing(0)

    # Add a small spacer between mode switch and graphs
    right_container_layout.addSpacing(5)
    
    # Right side layout (for graphs)
    right_panel = QWidget()
    right_panel_layout = QVBoxLayout(right_panel)
    right_panel_layout.setContentsMargins(10, 0, 10, 10)  # Set consistent padding for right panel with equal left and right margins

    # the graph area
    self.graphView = QWidget()
    graph_layout = QGridLayout()
    graph_layout.setSpacing(10)  # Add some spacing between graphs
    graph_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins from graph layout
    
    # Create plot containers with proper styling
    cpu_container = QWidget()
    memory_container = QWidget()
    gpu_container = QWidget()
    gpu_memory_container = QWidget()
    
    # Set the plot-container class for styling
    cpu_container.setProperty('class', 'plot-container')
    memory_container.setProperty('class', 'plot-container')
    gpu_container.setProperty('class', 'plot-container')
    gpu_memory_container.setProperty('class', 'plot-container')
    
    # Create plot widgets
    self.cpu_plot = pg.PlotWidget()
    self.memory_plot = pg.PlotWidget()
    self.gpu_plot = pg.PlotWidget()
    self.gpu_memory_plot = pg.PlotWidget()
    
    # Create layouts for containers
    cpu_layout = QVBoxLayout(cpu_container)
    memory_layout = QVBoxLayout(memory_container)
    gpu_layout = QVBoxLayout(gpu_container)
    gpu_memory_layout = QVBoxLayout(gpu_memory_container)
    
    # Set margins and spacing
    for layout in [cpu_layout, memory_layout, gpu_layout, gpu_memory_layout]:
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
    
    # Add plots to their containers
    cpu_layout.addWidget(self.cpu_plot)
    memory_layout.addWidget(self.memory_plot)
    gpu_layout.addWidget(self.gpu_plot)
    gpu_memory_layout.addWidget(self.gpu_memory_plot)
    
    # Add containers to the grid layout
    graph_layout.addWidget(cpu_container, 0, 0)
    graph_layout.addWidget(memory_container, 0, 1)
    graph_layout.addWidget(gpu_container, 1, 0)
    graph_layout.addWidget(gpu_memory_container, 1, 1)
    
    self.graphView.setLayout(graph_layout)
    right_panel_layout.addWidget(self.graphView)

    graph_layout.addWidget(self.cpu_plot, 0, 0)
    graph_layout.addWidget(self.memory_plot, 0, 1)
    graph_layout.addWidget(self.gpu_plot, 1, 0)
    graph_layout.addWidget(self.gpu_memory_plot, 1, 1)
    
    self.graphView.setLayout(graph_layout)
    right_panel_layout.addWidget(self.graphView)

    right_panel_layout.setSpacing(10)

    # the log scroll text area
    self.logView = QTextEdit()
    self.logView.setReadOnly(True)
    self.logView.setStyleSheet(self._current_stylesheet)
    self.logView.setFixedHeight(150)
    self.logView.setFont(QFont("Courier New"))
    right_panel_layout.addWidget(self.logView)
    if self.log_buffer:
        for line in self.log_buffer:
            self.logView.append(line)
        self.log_buffer = []

    right_container_layout.addWidget(right_panel)
    
    # Add the main content widgets
    content_widget.layout().addWidget(menu_widget)
    content_widget.layout().addWidget(right_container)
    
    main_layout.addWidget(content_widget)

    self.setLayout(main_layout)
    self.apply_stylesheet()

    return
  
  def toggle_theme(self):
    if self._current_stylesheet == DARK_STYLESHEET:
        self._current_stylesheet = LIGHT_STYLESHEET
        self.themeToggleButton.setText(DARK_DASHBOARD_BUTTON_TEXT)
        self.force_debug_checkbox.setProperty('class', 'light')
        is_dark = False
    else:
        self._current_stylesheet = DARK_STYLESHEET
        self.themeToggleButton.setText(LIGHT_DASHBOARD_BUTTON_TEXT)
        self.force_debug_checkbox.setProperty('class', 'dark')
        is_dark = True
    
    # Update button colors for the new theme
    self.init_button_colors()
    
    # Update copy button icons for the new theme
    self.update_copy_button_icons()
    
    self.apply_stylesheet()
    self.plot_graphs()
    
    # Update the toggle button styling for theme change
    self.update_toggle_button_text()
    
    # Also directly re-apply the current button style to ensure it updates
    current_text = self.toggleButton.text()
    if current_text == LAUNCH_CONTAINER_BUTTON_TEXT:
        self.apply_button_style(self.toggleButton, 'toggle_start')
    elif current_text == STOP_CONTAINER_BUTTON_TEXT:
        self.apply_button_style(self.toggleButton, 'toggle_stop')
    
    # Apply theme to the combobox dropdown using the new method
    if hasattr(self.container_combo, 'set_theme'):
        self.container_combo.set_theme(is_dark)
    elif hasattr(self.container_combo, 'apply_default_theme'):
        self.container_combo.apply_default_theme()
    
    # Force style update
    self.force_debug_checkbox.style().unpolish(self.force_debug_checkbox)
    self.force_debug_checkbox.style().polish(self.force_debug_checkbox)

  def update_copy_button_icons(self):
    """Update the copy button icons based on the current theme."""
    try:
      # Import the icon module - handle both relative and absolute imports
      try:
        # Try relative import first (works in development)
        import sys
        from pathlib import Path
        
        # Add parent directory to path if needed
        parent_dir = Path(__file__).resolve().parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.append(str(parent_dir))
            
        from app_icons import get_copy_icon
      except ImportError:
        # Fallback for packaged app
        from app_icons import get_copy_icon
        
      # Determine if we're using light theme
      is_light_theme = self._current_stylesheet == LIGHT_STYLESHEET
      
      # Get the icon with appropriate color
      copy_icon = get_copy_icon(is_light_theme)
      
      # Set icon size
      icon_size = QSize(20, 20)
      
      # Apply to buttons
      self.copyAddrButton.setIcon(copy_icon)
      self.copyAddrButton.setIconSize(icon_size)
      self.copyEthButton.setIcon(copy_icon)
      self.copyEthButton.setIconSize(icon_size)
      
    except Exception as e:
      # Log error and fallback to text
      self.add_log(f"Error setting copy icons: {str(e)}", debug=True)
      
      # Fallback to system icon if there's an error
      try:
        default_icon = self.style().standardIcon(QStyle.SP_DialogSaveButton)
        self.copyAddrButton.setIcon(default_icon)
        self.copyAddrButton.setIconSize(QSize(20, 20))
        self.copyEthButton.setIcon(default_icon)
        self.copyEthButton.setIconSize(QSize(20, 20))
      except:
        # Last resort fallback to text
        self.copyAddrButton.setText("Copy")
        self.copyEthButton.setText("Copy")

  def change_text_color(self):
    if self._current_stylesheet == DARK_STYLESHEET:
      self.force_debug_checkbox.setStyleSheet(DETAILED_CHECKBOX_STYLE.format(debug_checkbox_color=DARK_COLORS["debug_checkbox_color"]))
    else:
      self.force_debug_checkbox.setStyleSheet(DETAILED_CHECKBOX_STYLE.format(debug_checkbox_color=LIGHT_COLORS["debug_checkbox_color"]))

  def apply_stylesheet(self):
    is_dark = self._current_stylesheet == DARK_STYLESHEET
    self.logView.setObjectName("logView")  # Set object name for logView
    self.change_text_color()

    # Apply larger font size for info box labels on macOS
    if platform.system().lower() == 'darwin':
      # Additional macOS-specific styles
      macos_style = """
        #infoBox QLabel {
          font-size: 12pt !important;
        }
        #infoBoxText QLabel {
          font-size: 12pt !important;
        }
        QComboBox QAbstractItemView {
          min-width: 254px !important; /* Wider dropdown on macOS */
        }
      """
      # Apply base stylesheet plus macOS modifications
      self.setStyleSheet(self._current_stylesheet + macos_style)
      
      # Apply margin directly to logView with its own stylesheet
      self.logView.setStyleSheet("""
        QTextEdit#logView {
          margin-bottom: 6px;
        }
      """)
    else:
      # Apply regular stylesheet for other platforms
      self.setStyleSheet(self._current_stylesheet)
      self.logView.setStyleSheet("")
    
    # Reset plot backgrounds
    self.cpu_plot.setBackground(None)
    self.memory_plot.setBackground(None)
    self.gpu_plot.setBackground(None)
    self.gpu_memory_plot.setBackground(None)

  def toggle_container(self):
    """Toggle the Docker container state (start/stop)."""
    try:
        # Get the current container name
        container_name = self.docker_handler.container_name
        
        # Check if container is running
        is_running = self.is_container_running()
        
        if is_running:
            # Container is running, stop it
            self._stop_container()
        else:
            # Container is not running, start it
            self._start_container()
            
    except Exception as e:
        self.add_log(f"Error toggling container: {str(e)}", color="red")
        self.toast.show_notification(NotificationType.ERROR, f"Error toggling container: {str(e)}")

  def _stop_container(self):
    """Stop the Docker container."""
    try:
        # Get the current container name
        container_name = self.docker_handler.container_name
        
        # Get node alias from config if available for better user feedback
        node_display_name = container_name
        container_config = self.config_manager.get_container(container_name)
        if container_config and container_config.node_alias:
            node_display_name = container_config.node_alias
            message = f"Please wait while node '{node_display_name}' is being stopped..."
        else:
            message = "Please wait while Edge Node is being stopped..."
            
        # Show loading dialog for stopping operation
        self.toggle_dialog = LoadingDialog(
            self, 
            title="Stopping Node", 
            message=message,
            size=50
        )
        self.toggle_dialog.show()
        
        # Update message to indicate starting the stop process
        self.toggle_dialog.update_progress("Preparing to stop Docker container...")
        
        # Clear info displays
        self._clear_info_display()
        self.loading_indicator.start()
        
        # Update loading dialog with progress
        if hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None and self.toggle_dialog.isVisible():
            self.toggle_dialog.update_progress("Stopping Docker container...")
        
        # Define success callback for threaded operation
        def on_stop_success(result):
            stdout, stderr, return_code = result
            if return_code != 0:
                # Handle error case
                error_msg = f"Failed to stop container: {stderr}"
                self.add_log(error_msg, color="red")
                self.toast.show_notification(NotificationType.ERROR, error_msg)
                return
            
            # Update loading dialog with progress    
            if hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None and self.toggle_dialog.isVisible():
                self.toggle_dialog.update_progress("Container stopped, updating UI...")
                
            # Clear and update all UI elements
            self.update_toggle_button_text()
            self.refresh_local_address()  # Updates address displays with cached data
            self.maybe_refresh_uptime()   # Updates uptime displays
            self.plot_data()              # Clears plots
            
            # Stop loading indicator
            self.loading_indicator.stop()
            
            # Update loading dialog with completion message
            if hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None and self.toggle_dialog.isVisible():
                self.toggle_dialog.update_progress("Container stopped successfully!")
                
            # Close the loading dialog after a short delay to show success message
            toggle_dialog_visible = hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None and self.toggle_dialog.isVisible()
            if toggle_dialog_visible:
                QTimer.singleShot(500, lambda: self.toggle_dialog.safe_close() if hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None else None)
                # Schedule removal of the reference after a delay
                QTimer.singleShot(1000, lambda: setattr(self, 'toggle_dialog', None) if hasattr(self, 'toggle_dialog') else None)
            
            # Process events to ensure immediate UI update
            QApplication.processEvents()
            
            # Show success notification
            # Get node alias from config if available
            node_display_name = container_name
            container_config = self.config_manager.get_container(container_name)
            if container_config and container_config.node_alias:
                node_display_name = container_config.node_alias
                self.toast.show_notification(NotificationType.SUCCESS, f"Node '{node_display_name}' stopped successfully")
            else:
                self.toast.show_notification(NotificationType.SUCCESS, "Edge Node stopped successfully")
        
        # Define error callback for threaded operation
        def on_stop_error(error_msg):
            # Stop loading indicator in case of error
            self.loading_indicator.stop()
            
            # Update loading dialog with error message
            if hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None and self.toggle_dialog.isVisible():
                self.toggle_dialog.update_progress(f"Error: {error_msg}")
                
            # Close the loading dialog after a short delay to show error message
            toggle_dialog_visible = hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None and self.toggle_dialog.isVisible()
            if toggle_dialog_visible:
                QTimer.singleShot(1500, lambda: self.toggle_dialog.safe_close() if hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None else None)
                # Schedule removal of the reference after a delay
                QTimer.singleShot(2000, lambda: setattr(self, 'toggle_dialog', None) if hasattr(self, 'toggle_dialog') else None)
                
            self.add_log(f"Error stopping container: {error_msg}", color="red")
            self.toast.show_notification(NotificationType.ERROR, f"Error stopping container: {error_msg}")
        
        # Pass the container name explicitly to ensure we're stopping the right one
        self.docker_handler.stop_container_threaded(container_name, on_stop_success, on_stop_error)
        
    except Exception as e:
        # Stop loading indicator in case of error
        self.loading_indicator.stop()
        
        # Update loading dialog with error message
        if hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None and self.toggle_dialog.isVisible():
            self.toggle_dialog.update_progress(f"Error: {str(e)}")
            
        # Close the loading dialog after a short delay to show error message
        toggle_dialog_visible = hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None and self.toggle_dialog.isVisible()
        if toggle_dialog_visible:
            QTimer.singleShot(1500, lambda: self.toggle_dialog.safe_close() if hasattr(self, 'toggle_dialog') and self.toggle_dialog is not None else None)
            # Schedule removal of the reference after a delay
            QTimer.singleShot(2000, lambda: setattr(self, 'toggle_dialog', None) if hasattr(self, 'toggle_dialog') else None)
            
        self.add_log(f"Error stopping container: {str(e)}", color="red")
        self.toast.show_notification(NotificationType.ERROR, f"Error stopping container: {str(e)}")

  def _start_container(self):
    """Start the Docker container."""
    try:
        # Get the current container name
        container_name = self.docker_handler.container_name
        
        # Get volume name from config or generate one
        volume_name = None
        container_config = self.config_manager.get_container(container_name)
        if container_config:
            volume_name = container_config.volume
            self.add_log(f"Using existing volume name from config: {volume_name}", debug=True)
        else:
            volume_name = get_volume_name(container_name)
            self.add_log(f"Generated volume name: {volume_name}", debug=True)
        
        # Get node alias from config if available for better user feedback
        node_display_name = container_name
        container_config = self.config_manager.get_container(container_name)
        if container_config and container_config.node_alias:
            node_display_name = container_config.node_alias
            message = f"Please wait while node '{node_display_name}' is being launched..."
        else:
            message = "Please wait while Edge Node is being launched..."
            
        # Show loading dialog for launching operation
        self.launcher_dialog = LoadingDialog(
            self, 
            title="Launching Node", 
            message=message,
            size=50
        )
        self.launcher_dialog.show()
        
        # Update message to indicate starting the launch process
        self.launcher_dialog.update_progress("Preparing to launch Docker container...")
        
        # Process events to ensure dialog is visible and responsive
        QApplication.processEvents()
        
        # Start the container launch process
        self._perform_container_launch(container_name, volume_name)
        
    except Exception as e:
        # Stop loading indicator on error
        self.loading_indicator.stop()
        
        # Close the launcher dialog if it exists
        launcher_dialog_visible = hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible()
        if launcher_dialog_visible:
            self.launcher_dialog.safe_close()
            # Schedule removal of the reference after a delay
            QTimer.singleShot(500, lambda: setattr(self, 'launcher_dialog', None) if hasattr(self, 'launcher_dialog') else None)
            
        self.add_log(f"Error launching container: {str(e)}", color="red")
        self.toast.show_notification(NotificationType.ERROR, f"Error launching container: {str(e)}")

  def plot_data(self):
    """Plot container metrics data."""
    # Get the currently selected container
    container_name = self.container_combo.currentText()
    if not container_name:
        self.add_log("No container selected, cannot plot data", debug=True)
        return
        
    # Make sure we're working with the correct container
    self.docker_handler.set_container_name(container_name)
    
    if not self.is_container_running():
        self.add_log(f"Container {container_name} is not running, skipping plot data", debug=True)
        return

    def on_success(history: NodeHistory) -> None:
        # Make sure we're still on the same container
        if container_name != self.container_combo.currentText():
            self.add_log(f"Container changed during data plotting, ignoring results", debug=True)
            return
            
        self.__last_plot_data = history
        self.plot_graphs()
        
        # Update uptime and other metrics
        self.__current_node_uptime = history.uptime
        self.__current_node_epoch = history.current_epoch
        self.__current_node_epoch_avail = history.current_epoch_avail
        self.__current_node_ver = history.version
        
        self.maybe_refresh_uptime()
        self.add_log(f"Updated metrics for container {container_name}", debug=True)

    def on_error(error):
        # Make sure we're still on the same container
        if container_name != self.container_combo.currentText():
            self.add_log(f"Container changed during data plotting, ignoring error", debug=True)
            return
            
        self.add_log(f'Error getting metrics for {container_name}: {error}', debug=True)
        
        # If this is a timeout error, log it more prominently
        if "timed out" in error.lower():
            self.add_log(f"Metrics request for {container_name} timed out. This may indicate network issues or high load on the remote host.", color="red")

    try:
        self.add_log(f"Plotting data for container: {container_name}", debug=True)
        self.docker_handler.get_node_history(on_success, on_error)
    except Exception as e:
        self.add_log(f"Failed to start metrics request for {container_name}: {str(e)}", debug=True, color="red")
        on_error(str(e))

  def plot_graphs(self, history: Optional[NodeHistory] = None, limit: int = 100) -> None:
    """Plot the graphs with the given history data.
    
    Args:
        history: The history data to plot. If None, use the last data.
        limit: The maximum number of points to plot.
    """
    # Get the currently selected container
    container_name = self.container_combo.currentText()
    if not container_name:
        self.add_log("No container selected, cannot plot graphs", debug=True)
        return
     
    # Use provided history or last data
    if history is None:
       history = self.__last_plot_data
     
    if history is None:
        self.add_log(f"No history data available for container {container_name}", debug=True)
        return
    
    # Make sure we have timestamps
    if not history.timestamps or len(history.timestamps) == 0:
        self.add_log(f"No timestamps in history data for container {container_name}", debug=True)
        return
    
    # Clean and limit data
    timestamps = history.timestamps
    if len(timestamps) > limit:
        timestamps = timestamps[-limit:]
     
    # Get colors based on theme
    colors = DARK_COLORS if self._current_stylesheet == DARK_STYLESHEET else LIGHT_COLORS
    
    # Helper function to update a plot
    def update_plot(plot_widget, timestamps, data, name, color):
        plot_widget.clear()
        if data and len(data) > 0:
            # Ensure data length matches timestamps
            if len(data) > len(timestamps):
                data = data[-len(timestamps):]
            elif len(data) < len(timestamps):
                # Pad with zeros if needed
                data = [0] * (len(timestamps) - len(data)) + data
            
            # Convert string timestamps to numeric values for plotting
            numeric_timestamps = []
            for ts in timestamps:
                try:
                    if isinstance(ts, str):
                        # Convert ISO format string to timestamp
                        numeric_timestamps.append(datetime.fromisoformat(ts).timestamp())
                    else:
                        numeric_timestamps.append(float(ts))
                except (ValueError, TypeError):
                    # If conversion fails, use the index as a fallback
                    self.add_log(f"Failed to convert timestamp: {ts}", debug=True)
                    numeric_timestamps.append(len(numeric_timestamps))
            
            # Plot with numeric timestamps
            plot_widget.plot(numeric_timestamps, data, pen=color, name=name)
    
    # CPU Plot
    cpu_date_axis = DateAxisItem(orientation='bottom')
    cpu_date_axis.setTimestamps(timestamps, parent="cpu")
    self.cpu_plot.getAxis('bottom').setTickSpacing(60, 10)
    self.cpu_plot.getAxis('bottom').setStyle(tickTextOffset=10)
    self.cpu_plot.setAxisItems({'bottom': cpu_date_axis})
    self.cpu_plot.setTitle(CPU_LOAD_TITLE)
    update_plot(self.cpu_plot, timestamps, history.cpu_load, 'CPU Load', colors["graph_cpu_color"])
    
    # Memory Plot
    mem_date_axis = DateAxisItem(orientation='bottom')
    mem_date_axis.setTimestamps(timestamps, parent="mem")
    self.memory_plot.getAxis('bottom').setTickSpacing(60, 10)
    self.memory_plot.getAxis('bottom').setStyle(tickTextOffset=10)
    self.memory_plot.setAxisItems({'bottom': mem_date_axis})
    self.memory_plot.setTitle(MEMORY_USAGE_TITLE)
    update_plot(self.memory_plot, timestamps, history.occupied_memory, 'Occupied Memory', colors["graph_memory_color"])
    
    # GPU Plot if available
    if history and history.gpu_load:
      gpu_date_axis = DateAxisItem(orientation='bottom')
      gpu_date_axis.setTimestamps(timestamps, parent="gpu")
      self.gpu_plot.getAxis('bottom').setTickSpacing(60, 10)
      self.gpu_plot.getAxis('bottom').setStyle(tickTextOffset=10)
      self.gpu_plot.setAxisItems({'bottom': gpu_date_axis})
      self.gpu_plot.setTitle(GPU_LOAD_TITLE)
      update_plot(self.gpu_plot, timestamps, history.gpu_load, 'GPU Load', colors["graph_gpu_color"])

    # GPU Memory if available
    if history and history.gpu_occupied_memory:
      gpumem_date_axis = DateAxisItem(orientation='bottom')
      gpumem_date_axis.setTimestamps(timestamps, parent="gpu_mem")
      self.gpu_memory_plot.getAxis('bottom').setTickSpacing(60, 10)
      self.gpu_memory_plot.getAxis('bottom').setStyle(tickTextOffset=10)
      self.gpu_memory_plot.setAxisItems({'bottom': gpumem_date_axis})
      self.gpu_memory_plot.setTitle(GPU_MEMORY_LOAD_TITLE)
      update_plot(self.gpu_memory_plot, timestamps, history.gpu_occupied_memory, 'Occupied GPU Memory', colors["graph_gpu_memory_color"])
      
    self.add_log(f"Updated graphs for container {container_name} with {len(timestamps)} data points", debug=True)

  def update_plot(plot_widget, timestamps, data, name, color):
    """Update a plot with the given data."""
    plot_widget.setTitle(name)

  def refresh_local_address(self):
    """Refresh the node address display."""
    # Get the current index and container name from the data
    current_index = self.container_combo.currentIndex()
    if current_index < 0:
      # Only update if there's no address already displayed
      if not hasattr(self, 'node_addr') or not self.node_addr:
        self.addressDisplay.setText('Address: No container selected')
        self.ethAddressDisplay.setText('ETH Address: Not available')
        self.nameDisplay.setText('')
        self.copyAddrButton.hide()
        self.copyEthButton.hide()
      return

    # Get the actual container name from the item data
    container_name = self.container_combo.itemData(current_index)
    if not container_name:
      # Only update if there's no address already displayed
      if not hasattr(self, 'node_addr') or not self.node_addr:
        self.addressDisplay.setText('Address: No container selected')
        self.ethAddressDisplay.setText('ETH Address: Not available')
        self.nameDisplay.setText('')
        self.copyAddrButton.hide()
        self.copyEthButton.hide()
      return

    # Make sure we're working with the correct container
    self.docker_handler.set_container_name(container_name)

    # Check if container is running
    is_running = self.is_container_running()
    
    # If not running, check if we have cached address data in config
    if not is_running:
      config_container = self.config_manager.get_container(container_name)
      if config_container and config_container.node_address:
        # If we have cached data, keep displaying it but indicate node is not running
        if not hasattr(self, 'node_addr') or not self.node_addr:
          self.node_addr = config_container.node_address
          self.node_eth_address = config_container.eth_address
          self.node_name = config_container.node_alias
          
          # Format addresses with clear labels and truncated values
          if self.node_addr:
            if len(self.node_addr) > 24:  # Only truncate if long enough
              str_display = f"Address: {self.node_addr[:16]}...{self.node_addr[-8:]}"
            else:
              str_display = f"Address: {self.node_addr}"
            self.addressDisplay.setText(str_display)
            self.copyAddrButton.setVisible(True)
          
          if self.node_eth_address:
            if len(self.node_eth_address) > 24:  # Only truncate if long enough
              str_eth_display = f"ETH Address: {self.node_eth_address[:16]}...{self.node_eth_address[-8:]}"
            else:
              str_eth_display = f"ETH Address: {self.node_eth_address}"
            self.ethAddressDisplay.setText(str_eth_display)
            self.copyEthButton.setVisible(True)
          
          if self.node_name:
            self.nameDisplay.setText('Name: ' + self.node_name)
        
        return
      else:
        # No cached data and not running
        if not hasattr(self, 'node_addr') or not self.node_addr:
          self.addressDisplay.setText('Address: Node not running')
          self.ethAddressDisplay.setText('ETH Address: Not available')
          self.nameDisplay.setText('')
          self.copyAddrButton.hide()
          self.copyEthButton.hide()
        return

    def on_success(node_info: NodeInfo) -> None:
      # Make sure we're still on the same container
      if container_name != self.container_combo.currentText():
        self.add_log(f"Container changed during address refresh, ignoring results", debug=True)
        return

      # Get current config to check for changes
      config_container = self.config_manager.get_container(container_name)
      
      # Check if node alias has changed
      if config_container and node_info.alias != config_container.node_alias:
          self.add_log(f"Node alias changed from '{config_container.node_alias}' to '{node_info.alias}', updating config", debug=True)
          self.config_manager.update_node_alias(container_name, node_info.alias)
          # Refresh container list to update display in dropdown
          current_container = container_name  # Store current selection
          self.refresh_container_list()
          # Restore the selection
          for i in range(self.container_combo.count()):
              if self.container_combo.itemData(i) == current_container:
                  self.container_combo.setCurrentIndex(i)
                  break

      self.node_name = node_info.alias
      self.nameDisplay.setText('Name: ' + node_info.alias)

      if node_info.address != self.node_addr:
        self.node_addr = node_info.address
        self.node_eth_address = node_info.eth_address

        # Format addresses with clear labels and truncated values
        if self.node_addr:
          if len(self.node_addr) > 24:  # Only truncate if long enough
            str_display = f"Address: {self.node_addr[:16]}...{self.node_addr[-8:]}"
          else:
            str_display = f"Address: {self.node_addr}"
          self.addressDisplay.setText(str_display)
          self.copyAddrButton.setVisible(bool(self.node_addr))

        if self.node_eth_address:
          if len(self.node_eth_address) > 24:  # Only truncate if long enough
            str_eth_display = f"ETH Address: {self.node_eth_address[:16]}...{self.node_eth_address[-8:]}"
          else:
            str_eth_display = f"ETH Address: {self.node_eth_address}"
          self.ethAddressDisplay.setText(str_eth_display)
          self.copyEthButton.setVisible(bool(self.node_eth_address))

        self.add_log(
          f'Node info updated for {container_name}: {self.node_addr} : {self.node_name}, ETH: {self.node_eth_address}')

        # Save addresses to config for this specific container
        if container_name:
          # Update node address in config
          self.config_manager.update_node_address(container_name, self.node_addr)
          # Update ETH address in config
          self.config_manager.update_eth_address(container_name, self.node_eth_address)
          self.add_log(f"Saved node address and ETH address to config for {container_name}", debug=True)

    def on_error(error):
      # Make sure we're still on the same container
      if container_name != self.container_combo.currentText():
        self.add_log(f"Container changed during address refresh, ignoring error", debug=True)
        return

      # Don't clear the display if we already have data - just log the error
      if hasattr(self, 'node_addr') and self.node_addr:
        self.add_log(f'Error getting node info for {container_name}: {error}', debug=True)
        
        # If this is a timeout error, log it more prominently
        if "timed out" in error.lower():
          self.add_log(
            f"Node info request for {container_name} timed out. This may indicate network issues or high load on the remote host.",
            color="red")
      else:
        self.add_log(f'Error getting node info for {container_name}: {error}', debug=True)
        self.addressDisplay.setText('Address: Error getting node info')
        self.ethAddressDisplay.setText('ETH Address: Not available')
        self.nameDisplay.setText('')
        self.copyAddrButton.hide()
        self.copyEthButton.hide()

        # If this is a timeout error, log it more prominently
        if "timed out" in error.lower():
          self.add_log(
            f"Node info request for {container_name} timed out. This may indicate network issues or high load on the remote host.",
            color="red")

    try:
      self.add_log(f"Refreshing address for container: {container_name}", debug=True)
      self.docker_handler.get_node_info(on_success, on_error)
    except Exception as e:
      self.add_log(f"Failed to start node info request for {container_name}: {str(e)}", debug=True, color="red")
      on_error(str(e))

  def maybe_refresh_uptime(self):
    """Update uptime, epoch and epoch availability displays.
    
    This method updates the UI with the latest uptime, epoch, and epoch availability data.
    It only updates if the data has changed.
    """
    # Get the currently selected container
    container_name = self.container_combo.currentText()
    if not container_name:
        self.add_log("No container selected, cannot refresh uptime", debug=True)
        return
    
    # Get current values
    uptime = self.__current_node_uptime
    node_epoch = self.__current_node_epoch
    node_epoch_avail = self.__current_node_epoch_avail
    ver = self.__current_node_ver
    color = 'black'
    
    # Check if container is running
    if not self.is_container_running():
      uptime = "STOPPED"
      node_epoch = "N/A"
      node_epoch_avail = 0
      ver = "N/A"
      color = 'red'
      
    # Only update if values have changed
    if uptime != self.__display_uptime:

      self.node_uptime.setText(f'Up Time: {uptime}')

      self.node_epoch.setText(f'Epoch: {node_epoch}')

      prc = round(node_epoch_avail * 100 if node_epoch_avail > 0 else node_epoch_avail, 2) if node_epoch_avail is not None else 0
      self.node_epoch_avail.setText(f'Epoch avail: {prc}%')

      self.node_version.setText(f'Running ver: {ver}')

      self.__display_uptime = uptime
      self.add_log(f"Updated uptime display for container {container_name}", debug=True)
    return

  def copy_address(self):
    """Copy the node address to clipboard for the currently selected container."""
    # Get the currently selected container
    container_name = self.container_combo.currentText()
    if not container_name:
        self.toast.show_notification(NotificationType.ERROR, "No container selected")
        return
    
    # Check if we have an address
    if not self.node_addr:
      # Try to get from config
      config_container = self.config_manager.get_container(container_name)
      if config_container and config_container.node_address:
          self.node_addr = config_container.node_address
      else:
          self.toast.show_notification(NotificationType.ERROR, NOTIFICATION_ADDRESS_COPY_FAILED)
          return

    clipboard = QApplication.clipboard()
    clipboard.setText(self.node_addr)
    self.toast.show_notification(NotificationType.SUCCESS, NOTIFICATION_ADDRESS_COPIED.format(address=self.node_addr))
    self.add_log(f"Copied node address for container {container_name}", debug=True)
    return

  def copy_eth_address(self):
    """Copy the ETH address to clipboard for the currently selected container."""
    # Get the currently selected container
    container_name = self.container_combo.currentText()
    if not container_name:
        self.toast.show_notification(NotificationType.ERROR, "No container selected")
        return
    
    # Check if we have an address
    if not self.node_eth_address:
      # Try to get from config
      config_container = self.config_manager.get_container(container_name)
      if config_container and config_container.eth_address:
          self.node_eth_address = config_container.eth_address
      else:
          self.toast.show_notification(NotificationType.ERROR, NOTIFICATION_ADDRESS_COPY_FAILED)
          return

    clipboard = QApplication.clipboard()
    clipboard.setText(self.node_eth_address)
    self.toast.show_notification(NotificationType.SUCCESS, NOTIFICATION_ADDRESS_COPIED.format(address=self.node_eth_address))
    self.add_log(f"Copied ETH address for container {container_name}", debug=True)
    return

  def refresh_all(self):
    """Refresh all data and UI elements."""
    self._refresh_local_containers()

    # Check for updates periodically
    if (time() - self.__last_auto_update_check) > AUTO_UPDATE_CHECK_INTERVAL:
      verbose = self.__last_auto_update_check == 0
      self.__last_auto_update_check = time()
      self.check_for_updates(verbose=verbose or FULL_DEBUG)

    # Check for Docker image updates every 5 minutes (300 seconds)
    if (time() - self.__last_docker_image_check) > DOCKER_IMAGE_AUTO_UPDATE_CHECK_INTERVAL:
      self.__last_docker_image_check = time()
      self._check_docker_image_updates()

  def _check_docker_image_updates(self):
    """Check if there's an updated Docker image and pull it if available."""
    try:
      # First ensure we have Docker
      if not self.check_docker():
        return
        
      # Get proper image name and tag
      from utils.const import DOCKER_IMAGE, DOCKER_TAG
      
      self.add_log(f"Checking for Docker image updates...", debug=True)
      
      # Use the docker_handler service to check for and pull updates
      was_updated, message = self.docker_handler.check_and_pull_image_updates(
        image_name=DOCKER_IMAGE,
        tag=DOCKER_TAG
      )
      
      # Log the result
      if was_updated:
        self.add_log(message, color="green")
      else:
        self.add_log(message, debug=True)
        
    except Exception as e:
      self.add_log(f"Error checking for Docker image updates: {str(e)}", debug=True)

  def _refresh_local_containers(self):
    """Refresh local container list and info."""
    try:
        # Clear any remote connection settings to ensure we're using local Docker
        # Instead of calling clear_remote_connection(), directly set remote_ssh_command to None
        if hasattr(self, 'docker_handler'):
            self.docker_handler.remote_ssh_command = None
        
        if hasattr(self, 'ssh_service'):
            self.ssh_service.clear_configuration()
        
        # We don't need to refresh the container list on every refresh
        # The container list only changes when containers are added or removed
        # self.refresh_container_list()
        
        # Update container info if running
        if self.is_container_running():
            try:
                # Refresh address first (usually faster)
                self.refresh_local_address()
                
                # Then plot data (can be slower)
                try:
                    self.plot_data()
                except Exception as e:
                    self.add_log(f"Error plotting data for local container: {str(e)}", debug=True, color="red")
            except Exception as e:
                self.add_log(f"Error refreshing local container info: {str(e)}", color="red")
        
        # Always update the toggle button text
        self.update_toggle_button_text()
    except Exception as e:
        self.add_log(f"Error in local container refresh: {str(e)}", color="red")
        # Ensure toggle button text is updated even if there's an error
        self.update_toggle_button_text()


  def dapp_button_clicked(self):
    import webbrowser
    dapp_url = DAPP_URLS.get(self.current_environment)
    if dapp_url:
      webbrowser.open(dapp_url)
      self.add_log(f'Opening dApp URL: {dapp_url}', debug=True)
    else:
      self.add_log(f'Unknown environment: {self.current_environment}', debug=True)
      self.toast.show_notification(
        NotificationType.ERROR,
        f'Unknown environment: {self.current_environment}'
      )
    return
  
  
  def explorer_button_clicked(self):
    self.toast.show_notification(
      NotificationType.INFO,
      'Ratio1 Explorer is not yet implemented'
    )
    return
  
  
  def toggle_force_debug(self, state):
    """Toggle force debug mode based on checkbox state.
    
    Args:
        state: The state of the checkbox (Qt.Checked or Qt.Unchecked)
    """
    from PyQt5.QtCore import Qt
    
    is_checked = state == Qt.Checked
    self.__force_debug = is_checked
    
    # Save the debug state
    self.config_manager.set_force_debug(is_checked)
    
    # Log the change
    if is_checked:
        self.add_log("Force debug mode enabled", color="yellow")
    else:
        self.add_log("Force debug mode disabled", color="yellow")
    
    # Update docker handler debug mode if it exists
    if hasattr(self, 'docker_handler') and self.docker_handler is not None:
        try:
            self.docker_handler.set_debug_mode(is_checked)
        except Exception as e:
            self.add_log(f"Failed to set docker handler debug mode: {str(e)}", color="red")
    
    # If a container is running, we might need to restart it for the change to take effect
    if self.is_container_running():
        self.add_log("Note: You may need to restart the container for debug mode changes to take effect", color="yellow")

  def show_rename_dialog(self):
    # Get the current index and container name from the data
    current_index = self.container_combo.currentIndex()
    if current_index < 0:
        self.toast.show_notification(NotificationType.ERROR, "No container selected")
        return
        
    container_name = self.container_combo.itemData(current_index)
    if not container_name:
        self.toast.show_notification(NotificationType.ERROR, "No container selected")
        return
    
    # Check if container is running
    if not self.is_container_running():
        self.toast.show_notification(NotificationType.ERROR, "Container not running. Could not change node name.")
        return
    
    # Get current node alias if it exists
    container_config = self.config_manager.get_container(container_name)
    current_alias = container_config.node_alias if container_config and container_config.node_alias else ""
    
    # Create dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Change Node Name")
    dialog.setMinimumWidth(400)
    
    layout = QVBoxLayout()
    
    # Add explanation
    explanation = QLabel("Enter a friendly name for this node:")
    layout.addWidget(explanation)
    
    # Add input field
    name_input = QLineEdit()
    name_input.setText(current_alias)
    name_input.setPlaceholderText("Enter node name")
    
    # Apply theme-appropriate styles
    is_dark = self._current_stylesheet == DARK_STYLESHEET
    text_color = "white" if is_dark else "black"
    name_input.setStyleSheet(f"color: {text_color};")
    layout.addWidget(name_input)
    
    # Add buttons
    button_layout = QHBoxLayout()
    save_btn = QPushButton("Save")
    save_btn.setProperty("type", "confirm")  # Set property for styling
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setProperty("type", "cancel")  # Set property for styling
    
    button_layout.addWidget(save_btn)
    button_layout.addWidget(cancel_btn)
    layout.addLayout(button_layout)
    
    dialog.setLayout(layout)
    dialog.setStyleSheet(self._current_stylesheet)  # Apply current theme
    
    # Connect buttons
    save_btn.clicked.connect(lambda: self.validate_and_save_node_name(name_input.text(), dialog, container_name))
    cancel_btn.clicked.connect(dialog.reject)
    
    dialog.exec_()

  def validate_and_save_node_name(self, new_name: str, dialog: QDialog, container_name: str = None):
    """Validate and save a new node name.
    
    Args:
        new_name: The new name to save
        dialog: The dialog to close on success
        container_name: Optional container name. If not provided, will use current selection.
    """
    # Strip whitespace
    new_name = new_name.strip()
    
    # If container_name not provided, get from current selection
    if not container_name:
        current_index = self.container_combo.currentIndex()
        if current_index < 0:
            self.toast.show_notification(NotificationType.ERROR, "No container selected")
            return
        container_name = self.container_combo.itemData(current_index)
        if not container_name:
            self.toast.show_notification(NotificationType.ERROR, "No container selected")
            return
    
    # Check if name exceeds max length
    if len(new_name) > MAX_ALIAS_LENGTH:
        # Show warning dialog
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        warning_dialog = QDialog(self)
        warning_dialog.setWindowTitle("Warning")
        warning_dialog.setMinimumWidth(400)
        layout = QVBoxLayout()
        
        warning_text = f"Node name exceeds maximum length of {MAX_ALIAS_LENGTH} characters.\nIt will be truncated to: {new_name[:MAX_ALIAS_LENGTH]}"
        layout.addWidget(QLabel(warning_text))
        
        button_layout = QHBoxLayout()
        proceed_btn = QPushButton("Proceed")
        proceed_btn.setProperty("type", "confirm")  # Set property for styling
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("type", "cancel")  # Set property for styling
        
        button_layout.addWidget(proceed_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        warning_dialog.setLayout(layout)
        warning_dialog.setStyleSheet(self._current_stylesheet)  # Apply current theme
        
        # Connect buttons
        proceed_btn.clicked.connect(warning_dialog.accept)
        cancel_btn.clicked.connect(warning_dialog.reject)
        
        if warning_dialog.exec_() == QDialog.Accepted:
            new_name = new_name[:MAX_ALIAS_LENGTH]
        else:
            return  # Return to editing if user cancels
    
    def on_success(data: dict) -> None:
        self.add_log('Successfully renamed node, restarting container...', debug=True)
        self.toast.show_notification(
            NotificationType.SUCCESS,
            'Node renamed successfully. Restarting...'
        )
        dialog.accept()
        
        # Get the actual node name from the container
        def update_config_with_container_name(node_info: NodeInfo) -> None:
            # Update config with the name from the container
            if node_info.alias:
                self.config_manager.update_node_alias(container_name, node_info.alias)
                self.add_log(f"Saved node alias '{node_info.alias}' from container to config", debug=True)
                
                # Refresh the container list to update the display name in the dropdown
                current_container = container_name  # Store current selection
                self.refresh_container_list()
                # Restore the selection
                for i in range(self.container_combo.count()):
                    if self.container_combo.itemData(i) == current_container:
                        self.container_combo.setCurrentIndex(i)
                        break
        
        def on_node_info_error(error):
            self.add_log(f"Error getting node info after rename: {error}", debug=True)
            # Still proceed with restart even if we couldn't get the node info
            self.stop_container()
            self.launch_container()
            self.post_launch_setup()
            self.refresh_local_address()
        
        # Get node info to update config with actual container name
        self.docker_handler.get_node_info(update_config_with_container_name, on_node_info_error)
        
        # Stop and restart the container
        self.stop_container()
        self.launch_container()
        self.post_launch_setup()
        self.refresh_local_address()

    def on_error(error: str) -> None:
        self.add_log(f'Error renaming node: {error}', debug=True)
        self.toast.show_notification(
            NotificationType.ERROR,
            'Failed to rename node'
        )

    self.docker_handler.update_node_name(new_name, on_success, on_error)

  def _clear_info_display(self):
    """Clear all information displays."""
    # Set text color based on theme
    text_color = "white" if self._current_stylesheet == DARK_STYLESHEET else "black"
    
    # Get the current container name if available
    container_name = None
    if hasattr(self, 'container_combo') and self.container_combo.currentIndex() >= 0:
        container_name = self.container_combo.itemData(self.container_combo.currentIndex())
    
    # Check if we have cached data for this container
    cached_data = None
    if container_name:
        cached_data = self.config_manager.get_container(container_name)
    
    # If we have cached data, use it instead of clearing
    if cached_data and cached_data.node_address:
        # Update instance variables
        self.node_addr = cached_data.node_address
        self.node_eth_address = cached_data.eth_address
        self.node_name = cached_data.node_alias
        
        # Update displays with cached data but indicate node is not running
        if hasattr(self, 'nameDisplay') and self.node_name:
            self.nameDisplay.setText('Name: ' + self.node_name)

        if hasattr(self, 'addressDisplay') and self.node_addr:
            if len(self.node_addr) > 24:  # Only truncate if long enough
              str_display = f"Address: {self.node_addr[:16]}...{self.node_addr[-8:]}"
            else:
              str_display = f"Address: {self.node_addr}"
            self.addressDisplay.setText(str_display)
            # self.addressDisplay.setStyleSheet(f"color: {text_color};")
            if hasattr(self, 'copyAddrButton'):
                self.copyAddrButton.setVisible(True)
        
        if hasattr(self, 'ethAddressDisplay') and self.node_eth_address:
            if len(self.node_eth_address) > 24:  # Only truncate if long enough
              str_eth_display = f"ETH Address: {self.node_eth_address[:16]}...{self.node_eth_address[-8:]}"
            else:
              str_eth_display = f"ETH Address: {self.node_eth_address}"
            self.ethAddressDisplay.setText(str_eth_display)
            if hasattr(self, 'copyEthButton'):
                self.copyEthButton.setVisible(True)
    else:
        # No cached data, clear displays
        if hasattr(self, 'nameDisplay'):
            self.nameDisplay.setText('Name: -')

        if hasattr(self, 'addressDisplay'):
            self.addressDisplay.setText('Address: Not available')
            if hasattr(self, 'copyAddrButton'):
                self.copyAddrButton.hide()
        
        if hasattr(self, 'ethAddressDisplay'):
            self.ethAddressDisplay.setText('ETH Address: Not available')
            if hasattr(self, 'copyEthButton'):
                self.copyEthButton.hide()
        
        # Clear instance variables
        self.node_addr = None
        self.node_eth_address = None
        self.node_name = None
    
    if hasattr(self, 'local_address_label'):
        self.local_address_label.setText("Local Address: -")
    
    if hasattr(self, 'eth_address_label'):
        self.eth_address_label.setText("ETH Address: -")
    
    if hasattr(self, 'uptime_label'):
        self.uptime_label.setText("Uptime: -")
    
    if hasattr(self, 'node_uptime'):
        self.node_uptime.setText(UPTIME_LABEL)

    if hasattr(self, 'node_epoch'):
        self.node_epoch.setText(EPOCH_LABEL)

    if hasattr(self, 'node_epoch_avail'):
        self.node_epoch_avail.setText(EPOCH_AVAIL_LABEL)

    if hasattr(self, 'node_version'):
        self.node_version.setText('')

    # Reset state variables
    if hasattr(self, '__display_uptime'):
        self.__display_uptime = None
    
    if hasattr(self, '__current_node_uptime'):
        self.__current_node_uptime = -1
    
    if hasattr(self, '__current_node_epoch'):
        self.__current_node_epoch = -1
    
    if hasattr(self, '__current_node_epoch_avail'):
        self.__current_node_epoch_avail = -1
    
    if hasattr(self, '__current_node_ver'):
        self.__current_node_ver = -1
    
    if hasattr(self, '__last_plot_data'):
        self.__last_plot_data = None
    
    if hasattr(self, '__last_timesteps'):
        self.__last_timesteps = []
    
    # Clear all graphs
    if hasattr(self, 'cpu_plot'):
        self.cpu_plot.clear()
    
    if hasattr(self, 'memory_plot'):
        self.memory_plot.clear()
    
    if hasattr(self, 'gpu_plot'):
        self.gpu_plot.clear()
    
    if hasattr(self, 'gpu_memory_plot'):
        self.gpu_memory_plot.clear()
    
    # Reset graph titles and labels with current theme color
    for plot_name in ['cpu_plot', 'memory_plot', 'gpu_plot', 'gpu_memory_plot']:
        if hasattr(self, plot_name):
            plot = getattr(self, plot_name)
            plot.setTitle('')
            plot.setLabel('left', '')
            plot.setLabel('bottom', '')
    
    # Update toggle button state and color (commented out but updated to use new styling)
    # if hasattr(self, 'toggleButton'):
    #     self.toggleButton.setText(LAUNCH_CONTAINER_BUTTON_TEXT)
    #     self.apply_button_style(self.toggleButton, 'start')

  def open_docker_download(self):
    """Open Docker download page in default browser."""
    import webbrowser
    webbrowser.open('https://docs.docker.com/get-docker/')

  def _on_container_selected(self, container_name: str):
    """Handle container selection and update dashboard display"""
    # Always clear previous container's data first to ensure no data mixing
    self._clear_info_display()
    
    if not container_name:
        return
        
    try:
        self.add_log(f"Selected container: {container_name}", debug=True)
        
        # Get the current index and actual container name from the data
        current_index = self.container_combo.currentIndex()
        if current_index >= 0:
            actual_container_name = self.container_combo.itemData(current_index)
            if actual_container_name:
                # Update both docker handler and mixin container name
                self.docker_handler.set_container_name(actual_container_name)
                self.docker_container_name = actual_container_name
                self.add_log(f"Updated container name to: {actual_container_name}", debug=True)
        
        # Check if container exists in Docker
        container_exists = self.container_exists_in_docker(container_name)
        
        # Get container config
        config_container = self.config_manager.get_container(container_name)
        
        # If container doesn't exist in Docker but exists in config, show a message
        if not container_exists:
            if config_container:
                self.add_log(f"Container {container_name} exists in config but not in Docker. It will be recreated when launched.", debug=True)
                
                # Display saved addresses if available
                if config_container.node_address:
                    self.node_addr = config_container.node_address
                    if len(self.node_addr) > 24:  # Only truncate if long enough
                      str_display = f"Address: {self.node_addr[:16]}...{self.node_addr[-8:]}"
                    else:
                      str_display = f"Address: {self.node_addr}"
                    self.addressDisplay.setText(str_display)
                    self.copyAddrButton.setVisible(True)
                    self.add_log(f"Displaying saved node address for {container_name}", debug=True)
                
                if config_container.eth_address:
                    self.node_eth_address = config_container.eth_address
                    if len(self.node_eth_address) > 24:  # Only truncate if long enough
                      str_eth_display = f"ETH Address: {self.node_eth_address[:16]}...{self.node_eth_address[-8:]}"
                    else:
                      str_eth_display = f"ETH Address: {self.node_eth_address}"
                    self.ethAddressDisplay.setText(str_eth_display)
                    self.copyEthButton.setVisible(True)
                    self.add_log(f"Displaying saved ETH address for {container_name}", debug=True)
                
                if config_container.node_alias:
                    self.node_name = config_container.node_alias
                    self.nameDisplay.setText('Name: ' + config_container.node_alias)
                    self.add_log(f"Displaying saved node alias for {container_name}", debug=True)
                
                return
        
        # Update UI elements
        self.update_toggle_button_text()
        
        # If container is running, update all information displays
        if self.is_container_running():
            self.post_launch_setup()
            self.refresh_local_address()  # Updates address displays with cached data
            self.plot_data()  # Updates graphs and metrics
            self.maybe_refresh_uptime()  # Updates uptime, epoch, and version info
            self.add_log(f"Updated UI with running container data for: {container_name}", debug=True)
        else:
            # Display saved addresses from config if available
            if config_container:
                if config_container.node_address:
                    self.node_addr = config_container.node_address
                    if len(self.node_addr) > 24:  # Only truncate if long enough
                      str_display = f"Address: {self.node_addr[:16]}...{self.node_addr[-8:]}"
                    else:
                      str_display = f"Address: {self.node_addr}"
                    self.addressDisplay.setText(str_display)
                    self.copyAddrButton.setVisible(True)
                    self.add_log(f"Displaying saved node address for {container_name}", debug=True)
                
                if config_container.eth_address:
                    self.node_eth_address = config_container.eth_address
                    if len(self.node_eth_address) > 24:  # Only truncate if long enough
                      str_eth_display = f"ETH Address: {self.node_eth_address[:16]}...{self.node_eth_address[-8:]}"
                    else:
                      str_eth_display = f"ETH Address: {self.node_eth_address}"
                    self.ethAddressDisplay.setText(str_eth_display)
                    self.copyEthButton.setVisible(True)
                    self.add_log(f"Displaying saved ETH address for {container_name}", debug=True)
                
                self.add_log(f"Container {container_name} is not running, displaying saved data", debug=True)
            
    except Exception as e:
        self._clear_info_display()
        self.add_log(f"Error selecting container {container_name}: {str(e)}", debug=True, color="red")
        self.toast.show_notification(NotificationType.ERROR, f"Error selecting container: {str(e)}")

  def show_add_node_dialog(self):
    """Show confirmation dialog for adding a new node."""
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton

    # Generate the container name that would be used
    container_name = generate_container_name()
    volume_name = get_volume_name(container_name)

    # Create dialog
    dialog = QDialog(self)
    dialog.setWindowTitle(ADD_NEW_NODE_DIALOG_TITLE)
    dialog.setMinimumWidth(400)

    layout = QVBoxLayout()

    # Add info text with more descriptive message
    info_text = f"This action will create a new Edge Node. \n\nDo you want to proceed?"
    info_label = QLabel(info_text)
    info_label.setWordWrap(True)  # Enable word wrapping for better readability
    layout.addWidget(info_label)

    # Add buttons
    button_layout = QHBoxLayout()
    create_button = QPushButton("Create Node")
    cancel_button = QPushButton("Cancel")

    # Apply the same styling as Start/Stop buttons
    self.apply_button_style(create_button, 'start')  # Use 'start' style for Create button
    self.apply_button_style(cancel_button, 'stop')   # Use 'stop' style for Cancel button

    button_layout.addWidget(create_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)
    dialog.setStyleSheet(self._current_stylesheet)  # Apply current theme

    # Connect buttons
    create_button.clicked.connect(lambda: self._create_node_with_name(container_name, volume_name, None, dialog))
    cancel_button.clicked.connect(dialog.reject)

    dialog.exec_()

  def _create_node_with_name(self, container_name, volume_name, display_name, dialog):
    """Create a new node with the given name and close the dialog."""
    dialog.accept()
    self.add_new_node(container_name, volume_name, display_name)

  def add_new_node(self, container_name: str, volume_name: str, display_name: str = None):
    """Add a new node with the given container name and volume name,
       select it in the UI, and start it immediately."""
    try:
      from datetime import datetime

      # Show the loading dialog - now with blue background
      node_display_name = display_name if display_name else None
      
      if node_display_name:
        message = f"Please wait while node '{node_display_name}' is being launched..."
      else:
        message = "Please wait while new Edge Node is being launched..."
        
      self.startup_dialog = LoadingDialog(
          self, 
          title="Starting Node", 
          message=message,
          size=50
      )
      self.startup_dialog.show()
      
      # Process events to ensure dialog is visible
      QApplication.processEvents()
      
      # Add a small delay to ensure dialog is fully rendered
      QTimer.singleShot(100, lambda: self._perform_add_new_node(container_name, volume_name, display_name))

    except Exception as e:
      self.add_log(f"Failed to create new node: {str(e)}", color="red")
      # Close the loading dialog if it's still open
      startup_dialog_visible = hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible()
      if startup_dialog_visible:
        self.startup_dialog.safe_close()
        # Schedule removal of the reference after a delay
        QTimer.singleShot(500, lambda: setattr(self, 'startup_dialog', None) if hasattr(self, 'startup_dialog') else None)

  def _perform_add_new_node(self, container_name, volume_name, display_name):
    """Perform the actual node creation after the dialog is shown."""
    try:
      from datetime import datetime

      # 1) Create & store this container's config
      container_config = ContainerConfig(
        name=container_name,
        volume=volume_name,
        created_at=datetime.now().isoformat(),
        last_used=datetime.now().isoformat(),
        node_alias=display_name
      )
      self.config_manager.add_container(container_config)

      # 2) Refresh the list in the combo box, so it includes the new container
      self.refresh_container_list()

      # 3) Programmatically select the newly created container in the ComboBox
      #    We typically match itemData(...) to the container_name
      index = -1
      for i in range(self.container_combo.count()):
        if self.container_combo.itemData(i) == container_name:
          index = i
          break

      if index >= 0:
        self.container_combo.setCurrentIndex(index)

      # 4) Tell the Docker handler to manage this newly selected container
      self.docker_handler.set_container_name(container_name)

      # 5) Actually start (launch) the container so it shows "active" in the UI
      self.launch_container(volume_name)

      self.add_log(f"Successfully created and started new node: {container_name}", color="green")
      
      # Show success notification
      node_display_name = "Edge Node"
      if display_name:
        node_display_name = display_name
        self.toast.show_notification(NotificationType.SUCCESS, f"New Node '{node_display_name}' created successfully")
      else:
        self.toast.show_notification(NotificationType.SUCCESS, "New Edge Node created successfully")

    except Exception as e:
      self.add_log(f"Failed to create new node: {str(e)}", color="red")
    finally:
      # Close the loading dialog if it's still open
      startup_dialog_visible = hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible()
      if startup_dialog_visible:
        self.startup_dialog.safe_close()
        # Schedule removal of the reference after a delay
        QTimer.singleShot(500, lambda: setattr(self, 'startup_dialog', None) if hasattr(self, 'startup_dialog') else None)

  def launch_container(self, volume_name: str = None):
    """Launch the currently selected container with a mounted volume.
    
    Args:
        volume_name: Optional volume name to mount. If None, will be retrieved from config
                    or generated based on container name.
    """
    container_name = self.docker_handler.container_name
    
    # If volume_name is not provided, try to get it from config
    if volume_name is None:
        container_config = self.config_manager.get_container(container_name)
        if container_config and container_config.volume:
            volume_name = container_config.volume
            self.add_log(f"Using existing volume name from config: {volume_name}", debug=True)
        else:
            # Generate volume name based on container name
            volume_name = get_volume_name(container_name)
            self.add_log(f"Generated volume name: {volume_name}", debug=True)
    
    # Ensure volume_name is not None or empty
    if not volume_name:
        self.add_log(f"Warning: No volume name provided for container {container_name}. Using default.", color="yellow")
        volume_name = get_volume_name(container_name)
    
    # Check if volume exists in Docker
    volume_exists = self.config_manager.volume_exists_in_docker(volume_name)
    if not volume_exists:
        self.add_log(f"Volume {volume_name} does not exist. It will be created automatically.", debug=True)
    else:
        self.add_log(f"Using existing volume: {volume_name}", debug=True)
    
    self.add_log(f'Launching container {container_name} with volume {volume_name}...')
    
    try:
        # Show loading dialog if not already showing one from add_new_node or toggle_container
        startup_dialog_visible = hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible()
        launcher_dialog_visible = hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible()
        
        if not startup_dialog_visible and not launcher_dialog_visible:
            # Get node alias from config if available for better user feedback
            container_config = self.config_manager.get_container(container_name)
            node_alias = None
            if container_config and container_config.node_alias:
                node_alias = container_config.node_alias
                message = f"Please wait while node '{node_alias}' is being launched..."
            else:
                message = "Please wait while Edge Node is being launched..."
                
            self.launcher_dialog = LoadingDialog(
                self, 
                title="Launching Node", 
                message=message,
                size=50
            )
            self.launcher_dialog.show()
            
            # Update message to indicate starting the launch process
            self.launcher_dialog.update_progress("Preparing to launch Docker container...")
            
            # Process events to ensure dialog is visible and responsive
            QApplication.processEvents()
            
            # Add a small delay to ensure dialog is fully rendered
            QTimer.singleShot(100, lambda: self._perform_container_launch(container_name, volume_name))
        else:
            # If we already have a dialog visible, just perform the launch
            # If launcher_dialog is visible, update its progress message
            if launcher_dialog_visible:
                self.launcher_dialog.update_progress("Launching Docker container...")
            # If startup_dialog is visible, update its progress message
            elif startup_dialog_visible:
                self.startup_dialog.update_progress("Launching Docker container...")
                
            # Perform the launch operation
            self._perform_container_launch(container_name, volume_name)
            
    except Exception as e:
        # Stop loading indicator on error
        self.loading_indicator.stop()
        
        # Close the startup dialog if it exists
        startup_dialog_visible = hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible()
        if startup_dialog_visible:
            self.startup_dialog.safe_close()
            # Schedule removal of the reference after a delay
            QTimer.singleShot(500, lambda: setattr(self, 'startup_dialog', None) if hasattr(self, 'startup_dialog') else None)
            
        # Close the launcher dialog if it exists
        launcher_dialog_visible = hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible()
        if launcher_dialog_visible:
            self.launcher_dialog.safe_close()
            # Schedule removal of the reference after a delay
            QTimer.singleShot(500, lambda: setattr(self, 'launcher_dialog', None) if hasattr(self, 'launcher_dialog') else None)
            
        error_msg = f"Failed to launch container: {str(e)}"
        self.add_log(error_msg, color="red")
        self.toast.show_notification(NotificationType.ERROR, error_msg)

  def _perform_container_launch(self, container_name, volume_name):
    """Perform the actual container launch operation after the dialog is shown."""
    try:
        # Clear info displays
        self._clear_info_display()
        self.loading_indicator.start()
        
        # Update loading dialog with progress
        if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
            self.launcher_dialog.update_progress("Preparing Docker command...")
        
        # Get the Docker command that will be executed (for logging purposes only)
        command = self.docker_handler.get_launch_command(volume_name=volume_name)
        # Log the command without debug flag to ensure it's always visible
        self.add_log(f'Docker command: {" ".join(command)}', color="blue")
        
        # First check if the container already exists
        container_exists = self.container_exists_in_docker(container_name)
        if container_exists:
            # Update loading dialog with progress
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.update_progress(f"Removing existing container '{container_name}' before launch...")
            self.add_log(f"Container {container_name} already exists, removing it first", color="yellow")
        
        # Check if Docker image exists
        image_exists = self.docker_handler._ensure_image_exists()
        if not image_exists:
            # Close the existing launcher dialog if it's open
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.safe_close()
                QTimer.singleShot(500, lambda: setattr(self, 'launcher_dialog', None) if hasattr(self, 'launcher_dialog') else None)
            
            # Show Docker pull dialog
            from widgets.DockerPullDialog import DockerPullDialog
            self.docker_pull_dialog = DockerPullDialog(self)
            
            # Connect the pull_complete signal to handle completion
            self.docker_pull_dialog.pull_complete.connect(self._on_docker_pull_complete)
            
            # Store volume_name for later use after pull completes
            self._pending_volume_name = volume_name
            
            # Show the dialog
            self.docker_pull_dialog.show()
            
            # Define callbacks for Docker pull
            def on_pull_success(result):
                stdout, stderr, return_code = result
                # Process each line of output to update the dialog
                for line in stdout.splitlines():
                    if hasattr(self, 'docker_pull_dialog') and self.docker_pull_dialog is not None and self.docker_pull_dialog.isVisible():
                        self.docker_pull_dialog.update_pull_progress(line)
                
                # If pull completed successfully
                if return_code == 0:
                    if hasattr(self, 'docker_pull_dialog') and self.docker_pull_dialog is not None and self.docker_pull_dialog.isVisible():
                        self.docker_pull_dialog.pull_complete.emit(True, "Docker image pulled successfully")
                else:
                    error_msg = f"Failed to pull Docker image: {stderr}"
                    self.add_log(error_msg, color="red")
                    if hasattr(self, 'docker_pull_dialog') and self.docker_pull_dialog is not None and self.docker_pull_dialog.isVisible():
                        self.docker_pull_dialog.pull_complete.emit(False, error_msg)
            
            def on_pull_error(error_msg):
                self.add_log(f"Error pulling Docker image: {error_msg}", color="red")
                if hasattr(self, 'docker_pull_dialog') and self.docker_pull_dialog is not None and self.docker_pull_dialog.isVisible():
                    self.docker_pull_dialog.pull_complete.emit(False, error_msg)
            
            # Start the Docker pull operation
            self.docker_handler.pull_image(on_pull_success, on_pull_error)
            
            # Exit this method early - we'll continue after the pull completes
            return
        
        # Update loading dialog with progress
        if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
            self.launcher_dialog.update_progress("Launching Docker container...")
        
        # Define success callback for threaded operation
        def on_launch_success(result):
            stdout, stderr, return_code = result
            if return_code != 0:
                # Handle error case
                error_msg = f"Failed to launch container: {stderr}"
                self.add_log(error_msg, color="red")
                self.toast.show_notification(NotificationType.ERROR, error_msg)
                return
            
            # Update loading dialogs with progress    
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.update_progress("Container launched, updating configuration...")
            elif hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible():
                self.startup_dialog.update_progress("Container launched, updating configuration...")
            
            # Update last used timestamp in config
            from datetime import datetime
            self.config_manager.update_last_used(container_name, datetime.now().isoformat())
            
            # Update volume name in config if it's not already set
            container_config = self.config_manager.get_container(container_name)
            if container_config and not container_config.volume:
                self.config_manager.update_volume(container_name, volume_name)
                self.add_log(f"Updated volume name in config: {volume_name}", debug=True)
            
            # Update loading dialogs with progress
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.update_progress("Updating user interface...")
            elif hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible():
                self.startup_dialog.update_progress("Updating user interface...")
            
            # Update UI after launch
            self.post_launch_setup()
            self.refresh_local_address()
            self.plot_data()
            self.update_toggle_button_text()
            
            # Stop loading indicator
            self.loading_indicator.stop()
            
            # Update loading dialogs with completion message
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.update_progress("Container launched successfully!")
            elif hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible():
                self.startup_dialog.update_progress("Container launched successfully!")
            
            # Close the loading dialogs after a short delay to show success message
            launcher_dialog_visible = hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible()
            if launcher_dialog_visible:
                QTimer.singleShot(500, lambda: self.launcher_dialog.safe_close() if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None else None)
                # Schedule removal of the reference after a delay
                QTimer.singleShot(1000, lambda: setattr(self, 'launcher_dialog', None) if hasattr(self, 'launcher_dialog') else None)
            
            startup_dialog_visible = hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible()
            if startup_dialog_visible:
                QTimer.singleShot(500, lambda: self.startup_dialog.safe_close() if hasattr(self, 'startup_dialog') and self.startup_dialog is not None else None)
                # Schedule removal of the reference after a delay
                QTimer.singleShot(1000, lambda: setattr(self, 'startup_dialog', None) if hasattr(self, 'startup_dialog') else None)
            
            # Show success notification
            # Get node alias from config if available
            node_display_name = container_name
            container_config = self.config_manager.get_container(container_name)
            if container_config and container_config.node_alias:
                node_display_name = container_config.node_alias
                self.toast.show_notification(NotificationType.SUCCESS, f"Node '{node_display_name}' launched successfully")
            else:
                self.toast.show_notification(NotificationType.SUCCESS, "Edge Node launched successfully")
        
        # Define error callback for threaded operation
        def on_launch_error(error_msg):
            # Stop loading indicator on error
            self.loading_indicator.stop()
            
            # Check if this is a "container already exists" error
            if "Conflict" in error_msg and "is already in use" in error_msg:
                # Update loading dialogs with specific error message
                if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                    self.launcher_dialog.update_progress("Container name conflict detected. Trying again with container removal...")
                elif hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible():
                    self.startup_dialog.update_progress("Container name conflict detected. Trying again with container removal...")
                
                # Try to forcefully remove the container and retry launch
                try:
                    # Extract container ID from error message if possible
                    import re
                    container_id_match = re.search(r'by container "([^"]+)"', error_msg)
                    container_id = container_id_match.group(1) if container_id_match else None
                    
                    if container_id:
                        self.add_log(f"Attempting to forcefully remove container with ID: {container_id}", color="yellow")
                        # Run docker rm -f directly 
                        remove_cmd = ['docker', 'rm', '-f', container_id]
                        result = subprocess.run(remove_cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            self.add_log("Successfully removed conflicting container, retrying launch", color="blue")
                            # Wait to ensure Docker has released the resources
                            import time
                            time.sleep(1)
                            # Retry the launch
                            self.docker_handler.launch_container_threaded(volume_name, on_launch_success, on_launch_error)
                            return
                except Exception as retry_err:
                    self.add_log(f"Failed to resolve container conflict: {retry_err}", color="red")
            
            # Update loading dialogs with error message
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.update_progress(f"Error: {error_msg}")
            elif hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible():
                self.startup_dialog.update_progress(f"Error: {error_msg}")
            
            # Close the loading dialogs after a short delay to show error message
            launcher_dialog_visible = hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible()
            if launcher_dialog_visible:
                QTimer.singleShot(1500, lambda: self.launcher_dialog.safe_close() if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None else None)
                # Schedule removal of the reference after a delay
                QTimer.singleShot(2000, lambda: setattr(self, 'launcher_dialog', None) if hasattr(self, 'launcher_dialog') else None)
            
            startup_dialog_visible = hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible()
            if startup_dialog_visible:
                QTimer.singleShot(1500, lambda: self.startup_dialog.safe_close() if hasattr(self, 'startup_dialog') and self.startup_dialog is not None else None)
                # Schedule removal of the reference after a delay
                QTimer.singleShot(2000, lambda: setattr(self, 'startup_dialog', None) if hasattr(self, 'startup_dialog') else None)
                
            error_msg = f"Failed to launch container: {error_msg}"
            self.add_log(error_msg, color="red")
            self.toast.show_notification(NotificationType.ERROR, error_msg)
        
        # Launch the container in a thread
        self.docker_handler.launch_container_threaded(volume_name, on_launch_success, on_launch_error)
        
    except Exception as e:
        # Stop loading indicator on error
        self.loading_indicator.stop()
        
        # Close the startup dialog if it exists
        startup_dialog_visible = hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible()
        if startup_dialog_visible:
            self.startup_dialog.safe_close()
            # Schedule removal of the reference after a delay
            QTimer.singleShot(500, lambda: setattr(self, 'startup_dialog', None) if hasattr(self, 'startup_dialog') else None)
            
        # Close the launcher dialog if it exists
        launcher_dialog_visible = hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible()
        if launcher_dialog_visible:
            self.launcher_dialog.safe_close()
            # Schedule removal of the reference after a delay
            QTimer.singleShot(500, lambda: setattr(self, 'launcher_dialog', None) if hasattr(self, 'launcher_dialog') else None)
            
        error_msg = f"Failed to launch container: {str(e)}"
        self.add_log(error_msg, color="red")
        self.toast.show_notification(NotificationType.ERROR, error_msg)

  def _on_docker_pull_complete(self, success, message):
    """Handle Docker pull completion.
    
    Args:
        success: Whether the pull was successful
        message: Success or error message
    """
    # Log the result
    if success:
        self.add_log("Docker image pulled successfully", color="green")
    else:
        self.add_log(f"Docker image pull failed: {message}", color="red")
        
    # Close the Docker pull dialog after a short delay
    if hasattr(self, 'docker_pull_dialog') and self.docker_pull_dialog is not None and self.docker_pull_dialog.isVisible():
        QTimer.singleShot(500, lambda: self.docker_pull_dialog.safe_close() if hasattr(self, 'docker_pull_dialog') and self.docker_pull_dialog is not None else None)
        # Schedule removal of the reference after a delay
        QTimer.singleShot(1000, lambda: setattr(self, 'docker_pull_dialog', None) if hasattr(self, 'docker_pull_dialog') else None)
    
    # If pull was successful, continue with container launch
    if success:
        # Show the launcher dialog again
        container_name = self.docker_handler.container_name
        volume_name = self._pending_volume_name
        
        # Get node alias from config if available for better user feedback
        container_config = self.config_manager.get_container(container_name)
        node_display_name = container_name
        if container_config and container_config.node_alias:
            node_display_name = container_config.node_alias
            message = f"Please wait while node '{node_display_name}' is being launched..."
        else:
            message = "Please wait while Edge Node is being launched..."
            
        # Show loading dialog for launching operation
        self.launcher_dialog = LoadingDialog(
            self, 
            title="Launching Node", 
            message=message,
            size=50
        )
        self.launcher_dialog.show()
        
        # Update message to indicate starting the launch process
        self.launcher_dialog.update_progress("Preparing to launch Docker container...")
        
        # Process events to ensure dialog is visible and responsive
        QApplication.processEvents()
        
        # Continue with container launch
        self._perform_container_launch(container_name, volume_name)
    else:
        # Show error notification
        self.toast.show_notification(NotificationType.ERROR, f"Failed to pull Docker image: {message}")
  
  def refresh_container_list(self):
    """Refresh the container list in the combo box."""
    # Store current selection
    current_index = self.container_combo.currentIndex()
    selected_container = self.container_combo.itemData(current_index) if current_index >= 0 else None
    
    # Clear the combo box
    self.container_combo.clear()
    
    # Get containers from config
    containers = self.config_manager.get_all_containers()
    
    # If no containers found, create a default one
    if not containers:
        default_container = ContainerConfig(
            name="r1node",
            volume="r1vol",
            node_alias="Default Node"
        )
        self.config_manager.add_container(default_container)
        containers = [default_container]
    
    # Sort containers by name
    containers.sort(key=lambda x: x.name.lower())
    
    # Add containers to combo box
    for container in containers:
        # Use node alias if available, otherwise use container name
        display_text = container.node_alias if container.node_alias else container.name
        self.container_combo.addItem(display_text, container.name)
    
    # Center align all items in the dropdown is now handled by our CenteredComboBox class
    
    # Restore previous selection if it exists
    if selected_container:
        index = -1
        for i in range(self.container_combo.count()):
            if self.container_combo.itemData(i) == selected_container:
                index = i
                break
        if index >= 0:
            self.container_combo.setCurrentIndex(index)
    elif self.container_combo.count() > 0:
        # If no previous selection or it wasn't found, select the first item
        self.container_combo.setCurrentIndex(0)

    self.add_log(f'Displayed {self.container_combo.count()} containers in dropdown', debug=True)

  def is_container_running(self):
    """Check if the currently selected container is running.
    
    Returns:
        bool: True if the container is running, False otherwise
    """
    try:
        # Get the current index and container name from the data
        current_index = self.container_combo.currentIndex()
        if current_index < 0:
            return False
            
        # Get the actual container name from the item data
        container_name = self.container_combo.itemData(current_index)
        if not container_name:
            return False
            
        # Make sure the docker handler has the correct container name
        self.docker_handler.set_container_name(container_name)
        
        # Use the docker_handler's is_container_running method directly
        is_running = self.docker_handler.is_container_running()
        
        # Log status changes for debugging
        if hasattr(self, 'container_last_run_status') and self.container_last_run_status != is_running:
            self.add_log(f'Container {container_name} status changed: {self.container_last_run_status} -> {is_running}', debug=True)
            self.container_last_run_status = is_running
            
        return is_running
    except Exception as e:
        self.add_log(f"Error checking if container is running: {str(e)}", debug=True, color="red")
        return False


  def container_exists_in_docker(self, container_name: str) -> bool:
    """Check if a container exists in Docker.
    
    Args:
        container_name: Name of the container to check
        
    Returns:
        bool: True if the container exists in Docker, False otherwise
    """
    try:
        # Check directly with docker ps command
        stdout, stderr, return_code = self.docker_handler.execute_command(['docker', 'ps', '-a', '--format', '{{.Names}}', '--filter', f'name={container_name}'])
        if return_code == 0:
            containers = [name.strip() for name in stdout.split('\n') if name.strip() and name.strip() == container_name]
            return len(containers) > 0
        return False
    except Exception as e:
        self.add_log(f"Error checking if container exists in Docker: {str(e)}", debug=True, color="red")
        return False

  def cleanup_container_configs(self):
    """Update container configurations with their current status.
    
    This method checks which containers exist in Docker and updates their status in the config.
    It does NOT remove any configurations to maintain persistence.
    """
    try:
        # Get all containers from config
        config_containers = self.config_manager.get_all_containers()
        
        # Track if any container status has changed
        status_changed = False
        
        # Check each container's existence in Docker
        for config_container in config_containers:
            exists_in_docker = self.container_exists_in_docker(config_container.name)
            
            # Check if this is a status change (we could store previous status in the future)
            # For now, just log the status
            self.add_log(f"Container {config_container.name} exists in Docker: {exists_in_docker}", debug=True)
            
            # We could add a status field to ContainerConfig if needed in the future
            # If we did, we would set status_changed = True if the status changed
        
        # Only refresh container list if status changed
        # Since we don't track status changes yet, we'll comment this out
        # if status_changed:
        #     self.refresh_container_list()
    except Exception as e:
        self.add_log(f"Error updating container configurations: {str(e)}", debug=True, color="red")

  def post_launch_setup(self):
    """Execute post-launch setup tasks.
    
    This method is called after a container is launched to update the UI.
    It overrides the method from _DockerUtilsMixin.
    """
    # Call the parent method first
    super().post_launch_setup()
    
    # Update button state to show container is running
    self.toggleButton.setText(STOP_CONTAINER_BUTTON_TEXT)
    self.apply_button_style(self.toggleButton, 'toggle_stop')
    self.toggleButton.setEnabled(True)
    
    # Log the setup
    self.add_log('Post-launch setup completed', debug=True)
    
    # Process events to update UI immediately
    QApplication.processEvents()
    
    return
  
  def clear_remote_connection(self):
    """Clear the remote SSH connection."""
    if hasattr(self, 'ssh_service'):
        self.ssh_service.clear_configuration()
        
    # Reset the docker handler's remote command
    if hasattr(self, 'docker_handler'):
        self.docker_handler.remote_ssh_command = None
        
    # Update UI
    self.add_log("Cleared remote connection")
    
    # Don't call _refresh_local_containers here to avoid circular dependency
    return


  def _refresh_local_containers(self):
    """Refresh local container list and info."""
    try:
        # Clear any remote connection settings to ensure we're using local Docker
        # Instead of calling clear_remote_connection(), directly set remote_ssh_command to None
        if hasattr(self, 'docker_handler'):
            self.docker_handler.remote_ssh_command = None
        
        if hasattr(self, 'ssh_service'):
            self.ssh_service.clear_configuration()
        
        # We don't need to refresh the container list on every refresh
        # The container list only changes when containers are added or removed
        # self.refresh_container_list()
        
        # Update container info if running
        if self.is_container_running():
            try:
                # Refresh address first (usually faster)
                self.refresh_local_address()
                
                # Then plot data (can be slower)
                try:
                    self.plot_data()
                except Exception as e:
                    self.add_log(f"Error plotting data for local container: {str(e)}", debug=True, color="red")
            except Exception as e:
                self.add_log(f"Error refreshing local container info: {str(e)}", color="red")
        
        # Always update the toggle button text
        self.update_toggle_button_text()
    except Exception as e:
        self.add_log(f"Error in local container refresh: {str(e)}", color="red")
        # Ensure toggle button text is updated even if there's an error
        self.update_toggle_button_text()


  def dapp_button_clicked(self):
    import webbrowser
    dapp_url = DAPP_URLS.get(self.current_environment)
    if dapp_url:
      webbrowser.open(dapp_url)
      self.add_log(f'Opening dApp URL: {dapp_url}', debug=True)
    else:
      self.add_log(f'Unknown environment: {self.current_environment}', debug=True)
      self.toast.show_notification(
        NotificationType.ERROR,
        f'Unknown environment: {self.current_environment}'
      )
    return
  
  
  def explorer_button_clicked(self):
    self.toast.show_notification(
      NotificationType.INFO,
      'Ratio1 Explorer is not yet implemented'
    )
    return
  
  
  def update_toggle_button_text(self):
    """Update the toggle button text and style based on the current container state"""
    # Get the current index from the combo box
    current_index = self.container_combo.currentIndex()
    
    # Get the current text to check if it needs to be updated
    current_text = self.toggleButton.text()
    current_enabled = self.toggleButton.isEnabled()
    
    if current_index < 0:
        # Only update if state changed
        if current_text != LAUNCH_CONTAINER_BUTTON_TEXT or current_enabled:
            self.toggleButton.setText(LAUNCH_CONTAINER_BUTTON_TEXT)
            self.apply_button_style(self.toggleButton, 'toggle_disabled')
            self.toggleButton.setEnabled(False)
        return
        
    # Get the actual container name from the item data
    container_name = self.container_combo.itemData(current_index)
    if not container_name:
        # Only update if state changed
        if current_text != LAUNCH_CONTAINER_BUTTON_TEXT or current_enabled:
            self.toggleButton.setText(LAUNCH_CONTAINER_BUTTON_TEXT)
            self.apply_button_style(self.toggleButton, 'toggle_disabled')
            self.toggleButton.setEnabled(False)
        return
    
    # Check if container exists in Docker
    container_exists = self.container_exists_in_docker(container_name)
    
    # If container doesn't exist in Docker but exists in config, show launch button
    if not container_exists:
        config_container = self.config_manager.get_container(container_name)
        if config_container:
            # Only update if state changed
            if current_text != LAUNCH_CONTAINER_BUTTON_TEXT or not current_enabled:
                self.toggleButton.setText(LAUNCH_CONTAINER_BUTTON_TEXT)
                self.apply_button_style(self.toggleButton, 'toggle_start')
                self.toggleButton.setEnabled(True)
            return
    
    # Make sure the docker handler has the correct container name
    self.docker_handler.set_container_name(container_name)
    
    # Check if the container is running using docker_handler directly
    is_running = self.docker_handler.is_container_running()
    
    # Determine the new state
    new_text = STOP_CONTAINER_BUTTON_TEXT if is_running else LAUNCH_CONTAINER_BUTTON_TEXT
    new_style = 'toggle_stop' if is_running else 'toggle_start'
    
    # Update text if changed
    if current_text != new_text:
        self.toggleButton.setText(new_text)
    
    # Always apply the style to ensure it updates when theme changes
    self.apply_button_style(self.toggleButton, new_style)
    self.toggleButton.setEnabled(True)

  def _perform_container_launch(self, container_name, volume_name):
    """Perform the actual container launch operation after the dialog is shown."""
    try:
        # Clear info displays
        self._clear_info_display()
        self.loading_indicator.start()
        
        # Update loading dialog with progress
        if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
            self.launcher_dialog.update_progress("Preparing Docker command...")
        
        # Get the Docker command that will be executed (for logging purposes only)
        command = self.docker_handler.get_launch_command(volume_name=volume_name)
        # Log the command without debug flag to ensure it's always visible
        self.add_log(f'Docker command: {" ".join(command)}', color="blue")
        
        # First check if the container already exists
        container_exists = self.container_exists_in_docker(container_name)
        if container_exists:
            # Update loading dialog with progress
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.update_progress(f"Removing existing container '{container_name}' before launch...")
            self.add_log(f"Container {container_name} already exists, removing it first", color="yellow")
        
        # Check if Docker image exists
        image_exists = self.docker_handler._ensure_image_exists()
        if not image_exists:
            # Close the existing launcher dialog if it's open
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.safe_close()
                QTimer.singleShot(500, lambda: setattr(self, 'launcher_dialog', None) if hasattr(self, 'launcher_dialog') else None)
            
            # Show Docker pull dialog
            from widgets.DockerPullDialog import DockerPullDialog
            self.docker_pull_dialog = DockerPullDialog(self)
            
            # Connect the pull_complete signal to handle completion
            self.docker_pull_dialog.pull_complete.connect(self._on_docker_pull_complete)
            
            # Store volume_name for later use after pull completes
            self._pending_volume_name = volume_name
            
            # Show the dialog
            self.docker_pull_dialog.show()
            
            # Define callbacks for Docker pull
            def on_pull_success(result):
                stdout, stderr, return_code = result
                # Process each line of output to update the dialog
                for line in stdout.splitlines():
                    if hasattr(self, 'docker_pull_dialog') and self.docker_pull_dialog is not None and self.docker_pull_dialog.isVisible():
                        self.docker_pull_dialog.update_pull_progress(line)
                
                # If pull completed successfully
                if return_code == 0:
                    if hasattr(self, 'docker_pull_dialog') and self.docker_pull_dialog is not None and self.docker_pull_dialog.isVisible():
                        self.docker_pull_dialog.pull_complete.emit(True, "Docker image pulled successfully")
                else:
                    error_msg = f"Failed to pull Docker image: {stderr}"
                    self.add_log(error_msg, color="red")
                    if hasattr(self, 'docker_pull_dialog') and self.docker_pull_dialog is not None and self.docker_pull_dialog.isVisible():
                        self.docker_pull_dialog.pull_complete.emit(False, error_msg)
            
            def on_pull_error(error_msg):
                self.add_log(f"Error pulling Docker image: {error_msg}", color="red")
                if hasattr(self, 'docker_pull_dialog') and self.docker_pull_dialog is not None and self.docker_pull_dialog.isVisible():
                    self.docker_pull_dialog.pull_complete.emit(False, error_msg)
            
            # Start the Docker pull operation
            self.docker_handler.pull_image(on_pull_success, on_pull_error)
            
            # Exit this method early - we'll continue after the pull completes
            return
        
        # Update loading dialog with progress
        if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
            self.launcher_dialog.update_progress("Launching Docker container...")
        
        # Define success callback for threaded operation
        def on_launch_success(result):
            stdout, stderr, return_code = result
            if return_code != 0:
                # Handle error case
                error_msg = f"Failed to launch container: {stderr}"
                self.add_log(error_msg, color="red")
                self.toast.show_notification(NotificationType.ERROR, error_msg)
                return
            
            # Update loading dialogs with progress    
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.update_progress("Container launched, updating configuration...")
            elif hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible():
                self.startup_dialog.update_progress("Container launched, updating configuration...")
            
            # Update last used timestamp in config
            from datetime import datetime
            self.config_manager.update_last_used(container_name, datetime.now().isoformat())
            
            # Update volume name in config if it's not already set
            container_config = self.config_manager.get_container(container_name)
            if container_config and not container_config.volume:
                self.config_manager.update_volume(container_name, volume_name)
                self.add_log(f"Updated volume name in config: {volume_name}", debug=True)
            
            # Update loading dialogs with progress
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.update_progress("Updating user interface...")
            elif hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible():
                self.startup_dialog.update_progress("Updating user interface...")
            
            # Update UI after launch
            self.post_launch_setup()
            self.refresh_local_address()
            self.plot_data()
            self.update_toggle_button_text()
            
            # Stop loading indicator
            self.loading_indicator.stop()
            
            # Update loading dialogs with completion message
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.update_progress("Container launched successfully!")
            elif hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible():
                self.startup_dialog.update_progress("Container launched successfully!")
            
            # Close the loading dialogs after a short delay to show success message
            launcher_dialog_visible = hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible()
            if launcher_dialog_visible:
                QTimer.singleShot(500, lambda: self.launcher_dialog.safe_close() if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None else None)
                # Schedule removal of the reference after a delay
                QTimer.singleShot(1000, lambda: setattr(self, 'launcher_dialog', None) if hasattr(self, 'launcher_dialog') else None)
            
            startup_dialog_visible = hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible()
            if startup_dialog_visible:
                QTimer.singleShot(500, lambda: self.startup_dialog.safe_close() if hasattr(self, 'startup_dialog') and self.startup_dialog is not None else None)
                # Schedule removal of the reference after a delay
                QTimer.singleShot(1000, lambda: setattr(self, 'startup_dialog', None) if hasattr(self, 'startup_dialog') else None)
            
            # Show success notification
            # Get node alias from config if available
            node_display_name = container_name
            container_config = self.config_manager.get_container(container_name)
            if container_config and container_config.node_alias:
                node_display_name = container_config.node_alias
                self.toast.show_notification(NotificationType.SUCCESS, f"Node '{node_display_name}' launched successfully")
            else:
                self.toast.show_notification(NotificationType.SUCCESS, "Edge Node launched successfully")
        
        # Define error callback for threaded operation
        def on_launch_error(error_msg):
            # Stop loading indicator on error
            self.loading_indicator.stop()
            
            # Check if this is a "container already exists" error
            if "Conflict" in error_msg and "is already in use" in error_msg:
                # Update loading dialogs with specific error message
                if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                    self.launcher_dialog.update_progress("Container name conflict detected. Trying again with container removal...")
                elif hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible():
                    self.startup_dialog.update_progress("Container name conflict detected. Trying again with container removal...")
                
                # Try to forcefully remove the container and retry launch
                try:
                    # Extract container ID from error message if possible
                    import re
                    container_id_match = re.search(r'by container "([^"]+)"', error_msg)
                    container_id = container_id_match.group(1) if container_id_match else None
                    
                    if container_id:
                        self.add_log(f"Attempting to forcefully remove container with ID: {container_id}", color="yellow")
                        # Run docker rm -f directly 
                        remove_cmd = ['docker', 'rm', '-f', container_id]
                        result = subprocess.run(remove_cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            self.add_log("Successfully removed conflicting container, retrying launch", color="blue")
                            # Wait to ensure Docker has released the resources
                            import time
                            time.sleep(1)
                            # Retry the launch
                            self.docker_handler.launch_container_threaded(volume_name, on_launch_success, on_launch_error)
                            return
                except Exception as retry_err:
                    self.add_log(f"Failed to resolve container conflict: {retry_err}", color="red")
            
            # Update loading dialogs with error message
            if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible():
                self.launcher_dialog.update_progress(f"Error: {error_msg}")
            elif hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible():
                self.startup_dialog.update_progress(f"Error: {error_msg}")
            
            # Close the loading dialogs after a short delay to show error message
            launcher_dialog_visible = hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible()
            if launcher_dialog_visible:
                QTimer.singleShot(1500, lambda: self.launcher_dialog.safe_close() if hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None else None)
                # Schedule removal of the reference after a delay
                QTimer.singleShot(2000, lambda: setattr(self, 'launcher_dialog', None) if hasattr(self, 'launcher_dialog') else None)
            
            startup_dialog_visible = hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible()
            if startup_dialog_visible:
                QTimer.singleShot(1500, lambda: self.startup_dialog.safe_close() if hasattr(self, 'startup_dialog') and self.startup_dialog is not None else None)
                # Schedule removal of the reference after a delay
                QTimer.singleShot(2000, lambda: setattr(self, 'startup_dialog', None) if hasattr(self, 'startup_dialog') else None)
                
            error_msg = f"Failed to launch container: {error_msg}"
            self.add_log(error_msg, color="red")
            self.toast.show_notification(NotificationType.ERROR, error_msg)
        
        # Launch the container in a thread
        self.docker_handler.launch_container_threaded(volume_name, on_launch_success, on_launch_error)
        
    except Exception as e:
        # Stop loading indicator on error
        self.loading_indicator.stop()
        
        # Close the startup dialog if it exists
        startup_dialog_visible = hasattr(self, 'startup_dialog') and self.startup_dialog is not None and self.startup_dialog.isVisible()
        if startup_dialog_visible:
            self.startup_dialog.safe_close()
            # Schedule removal of the reference after a delay
            QTimer.singleShot(500, lambda: setattr(self, 'startup_dialog', None) if hasattr(self, 'startup_dialog') else None)
            
        # Close the launcher dialog if it exists
        launcher_dialog_visible = hasattr(self, 'launcher_dialog') and self.launcher_dialog is not None and self.launcher_dialog.isVisible()
        if launcher_dialog_visible:
            self.launcher_dialog.safe_close()
            # Schedule removal of the reference after a delay
            QTimer.singleShot(500, lambda: setattr(self, 'launcher_dialog', None) if hasattr(self, 'launcher_dialog') else None)
            
        error_msg = f"Failed to launch container: {str(e)}"
        self.add_log(error_msg, color="red")
        self.toast.show_notification(NotificationType.ERROR, error_msg)
