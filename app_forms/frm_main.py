import sys
import os
import json
import platform
import os


from datetime import datetime
from time import time
from copy import deepcopy

from PyQt5.QtWidgets import (
  QApplication, 
  QWidget, 
  QVBoxLayout, 
  QPushButton, 
  QLabel, 
  QGridLayout,
  QFrame, 
  QMessageBox, 
  QTextEdit, 
  QDialog, 
  QHBoxLayout, 
  QSpacerItem, 
  QSizePolicy,
  QCheckBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
import pyqtgraph as pg

import services.messaging_service as messaging_service
from utils.const import *
from utils.docker import _DockerUtilsMixin
from utils.updater import _UpdaterMixin

from utils.icon import ICON_BASE64

from app_forms.frm_utils import (
  get_icon_from_base64, DateAxisItem, ToggleButton1
)

from ver import __VER__ as __version__

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
  def __init__(self):
    self.logView = None
    self.log_buffer = []
    self.__force_debug = False
    super().__init__()

    self.__current_node_uptime = -1
    self.__current_node_epoch = -1
    self.__current_node_epoch_avail = -1
    self.__current_node_ver = -1
    self.__display_uptime = None


    self._current_stylesheet = DARK_STYLESHEET
    self.__last_plot_data = None
    self.__last_auto_update_check = 0
    
    self.__version__ = __version__
    self.__last_timesteps = []
    self._icon = get_icon_from_base64(ICON_BASE64)
    
    self.runs_in_production = self.is_running_in_production()
    
    self.initUI()

    self.__cwd = os.getcwd()
    
    self.showMaximized()
    self.add_log(f'Edge Node Launcher v{self.__version__} started. Running in production: {self.runs_in_production}, running with debugger: {self.runs_with_debugger()}, running in ipython: {self.runs_from_ipython()},  running from exe: {not self.not_running_from_exe()}')
    self.add_log(f'Running from: {self.__cwd}')


    platform_info, os_name, os_version = get_platform_and_os_info()
    self.add_log(f'Platform: {platform_info}')
    self.add_log(f'OS: {os_name} {os_version}')

    if not self.check_docker():
      sys.exit(1)    

    self.docker_initialize()
      
    if self.is_container_running():
      self.post_launch_setup()
      self.refresh_local_address()
      self.plot_data()  # Initial plot

    self.update_toggle_button_text()

    self.timer = QTimer(self)
    self.timer.timeout.connect(self.refresh_all)
    self.timer.start(REFRESH_TIME)  # Refresh every 10 seconds

      
    return

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
    if os.name == 'nt':
      import ctypes
      myappid = 'naeural.edge_node_launcher'  # arbitrary string
      ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # TODO: Add support for other OS (Linux, MacOS)
    return
  
  def initUI(self):
    HEIGHT = 1100
    self.setWindowTitle(WINDOW_TITLE)
    self.setGeometry(0, 0, 1800, HEIGHT)
    self.center()

    main_layout = QHBoxLayout(self)

    # Left menu layout with fixed width
    menu_widget = QWidget()
    menu_widget.setFixedWidth(300)  # Set the fixed width here
    menu_layout = QVBoxLayout(menu_widget)
    menu_layout.setAlignment(Qt.AlignTop)
    
    top_button_area = QVBoxLayout()

    self.toggleButton = QPushButton(LAUNCH_CONTAINER_BUTTON_TEXT)
    self.toggleButton.clicked.connect(self.toggle_container)
    top_button_area.addWidget(self.toggleButton)

    self.dapp_button = QPushButton(DAPP_BUTTON_TEXT)
    self.dapp_button.clicked.connect(self.dapp_button_clicked)
    top_button_area.addWidget(self.dapp_button)
    
    # b1 = ToggleButton1()
    # b2 = ToggleButton1()
    # b3 = ToggleButton1()
    # top_button_area.addWidget(b1)
    # top_button_area.addWidget(b2)
    # top_button_area.addWidget(b3)
    

    self.explorer_button = QPushButton(EXPLORER_BUTTON_TEXT)
    self.explorer_button.clicked.connect(self.explorer_button_clicked)
    top_button_area.addWidget(self.explorer_button)


    menu_layout.addLayout(top_button_area)

    # Spacer to push bottom_button_area to the bottom
    menu_layout.addSpacerItem(QSpacerItem(20, int(HEIGHT * 0.75), QSizePolicy.Minimum, QSizePolicy.Expanding))


    # Bottom button area
    bottom_button_area = QVBoxLayout()
    
    ## info box
    info_box = QFrame()
    info_box.setFrameShape(QFrame.Box)
    info_box.setFrameShadow(QFrame.Sunken)
    info_box.setLineWidth(4)
    info_box.setMidLineWidth(1)
    info_box_layout = QVBoxLayout()

    self.addressDisplay = QLabel('')
    self.addressDisplay.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.addressDisplay)

    self.nameDisplay = QLabel('')
    self.nameDisplay.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.nameDisplay)

    self.node_uptime = QLabel(UPTIME_LABEL)
    self.node_uptime.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_uptime)

    self.node_epoch = QLabel(EPOCH_LABEL)
    self.node_epoch.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_epoch)

    self.node_epoch_avail = QLabel(EPOCH_AVAIL_LABEL)
    self.node_epoch_avail.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_epoch_avail)

    self.node_version = QLabel()
    self.node_version.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_version)
    
    info_box.setLayout(info_box_layout)
    bottom_button_area.addWidget(info_box)
    
    ## buttons
    self.copyButton = QPushButton(COPY_ADDRESS_BUTTON_TEXT)
    self.copyButton.clicked.connect(self.copy_address)
    bottom_button_area.addWidget(self.copyButton)

    self.envEditButton = QPushButton(EDIT_ENV_BUTTON_TEXT)
    self.envEditButton.clicked.connect(self.edit_env_file)
    bottom_button_area.addWidget(self.envEditButton)

    self.btn_edit_addrs = QPushButton(EDIT_AUTHORIZED_ADDRS)
    self.btn_edit_addrs.clicked.connect(self.edit_addrs)
    bottom_button_area.addWidget(self.btn_edit_addrs)

    
    # view_config_files
    self.btn_view_configs = QPushButton(VIEW_CONFIGS_BUTTON_TEXT)
    self.btn_view_configs.clicked.connect(self.view_config_files)
    bottom_button_area.addWidget(self.btn_view_configs)

    
    self.deleteButton = QPushButton(DELETE_AND_RESTART_BUTTON_TEXT)
    self.deleteButton.clicked.connect(self.delete_and_restart)
    bottom_button_area.addWidget(self.deleteButton)

    # Toggle theme button
    self.themeToggleButton = QPushButton(LIGHT_DASHBOARD_BUTTON_TEXT)
    # self.themeToggleButton.setCheckable(True)
    self.themeToggleButton.clicked.connect(self.toggle_theme)
    bottom_button_area.addWidget(self.themeToggleButton)    
    
    # add a checkbox item to force debug
    self.force_debug_checkbox = QCheckBox('Force Debug Mode')
    self.force_debug_checkbox.setChecked(False)
    self.force_debug_checkbox.setFont(QFont("Courier New", 9, QFont.Bold))
    self.force_debug_checkbox.setStyleSheet("color: white;")
    self.force_debug_checkbox.stateChanged.connect(self.toggle_force_debug)
    bottom_button_area.addWidget(self.force_debug_checkbox)

    bottom_button_area.addStretch()
    menu_layout.addLayout(bottom_button_area)
    
    main_layout.addWidget(menu_widget)  # Add the fixed-width widget

    # Right side layout (for graphs)
    self.left_panel = QWidget()
    left_panel_layout = QVBoxLayout()
    
    # the graph area
    self.graphView = QWidget()
    graph_layout = QGridLayout()
    
    self.cpu_plot = pg.PlotWidget() #background='#243447')
    self.memory_plot = pg.PlotWidget() #background='#243447')
    self.gpu_plot = pg.PlotWidget() #background='#243447')
    self.gpu_memory_plot = pg.PlotWidget() #background='#243447')
    
    graph_layout.addWidget(self.cpu_plot, 0, 0)
    graph_layout.addWidget(self.memory_plot, 0, 1)
    graph_layout.addWidget(self.gpu_plot, 1, 0)
    graph_layout.addWidget(self.gpu_memory_plot, 1, 1)
    
    self.graphView.setLayout(graph_layout)
    left_panel_layout.addWidget(self.graphView)
    
    # the log scroll text area
    self.logView = QTextEdit()
    self.logView.setReadOnly(True)
    self.logView.setStyleSheet(self._current_stylesheet)
    self.logView.setFixedHeight(150)
    self.logView.setFont(QFont("Courier New"))
    left_panel_layout.addWidget(self.logView)
    if self.log_buffer:
      for line in self.log_buffer:
        self.logView.append(line)
      self.log_buffer = []
    # endif log buffer is populated
    
    self.left_panel.setLayout(left_panel_layout)
    main_layout.addWidget(self.left_panel)

    self.setLayout(main_layout)
    self.apply_stylesheet()
    
    self.setWindowIcon(self._icon)
    self.set_windows_taskbar_icon()

    return
  
  def toggle_theme(self):
    if self._current_stylesheet == DARK_STYLESHEET:
      self._current_stylesheet = LIGHT_STYLESHEET
      self.themeToggleButton.setText('Switch to Dark Theme')
    else:
      self._current_stylesheet = DARK_STYLESHEET
      self.themeToggleButton.setText('Switch to Light Theme')
    self.apply_stylesheet()
    self.plot_graphs()
    return  

  def apply_stylesheet(self):
    self.setStyleSheet(self._current_stylesheet)
    self.logView.setStyleSheet(self._current_stylesheet)
    self.cpu_plot.setBackground(None)  # Reset the background to let the stylesheet take effect
    self.memory_plot.setBackground(None)
    self.gpu_plot.setBackground(None)
    self.gpu_memory_plot.setBackground(None)
    return

  def toggle_container(self):
    if self.is_container_running():
      self.add_log('Edge Node is running, user requested stopping the container...')
      self.stop_container()
    else:
      self.launch_container()
    self.update_toggle_button_text()
    return

  def update_toggle_button_text(self):
    if self.is_container_running():
      self.toggleButton.setText(STOP_CONTAINER_BUTTON_TEXT)
      self.toggleButton.setStyleSheet("background-color: red; color: white;")
    else:
      self.toggleButton.setText(LAUNCH_CONTAINER_BUTTON_TEXT)
      self.toggleButton.setStyleSheet("background-color: green; color: white;")
    return
  
  def edit_file(self, file_path, func, title='Edit File'):
    env_content = ''
    try:
      with open(file_path, 'r') as file:
        env_content = file.read()
    except FileNotFoundError:
      pass    
    
    # Create the text edit widget with Courier New font and light font color
    text_edit = QTextEdit()
    text_edit.setText(env_content)
    # text_edit.setFont(QFont("Courier New", 14))
    # text_edit.setStyleSheet("color: #FFFFFF; background-color: #0D1F2D;")

    # Create the dialog
    dialog = QDialog(self)
    dialog.setWindowTitle(title)
    dialog.setGeometry(0, 0, 1000, 900)  # Enlarge the edit window

    # Center the dialog on the screen
    screen_geometry = QApplication.desktop().screenGeometry()
    x = (screen_geometry.width() - dialog.width()) // 2
    y = (screen_geometry.height() - dialog.height()) // 2
    dialog.move(x, y)

    dialog_layout = QVBoxLayout()
    dialog_layout.addWidget(text_edit)

    # Save button
    save_button = QPushButton('Save')
    save_button.clicked.connect(lambda: func(text_edit.toPlainText(), dialog))
    dialog_layout.addWidget(save_button)

    dialog.setLayout(dialog_layout)
    dialog.exec_()
    return    

  def edit_env_file(self):
    self.edit_file(
      file_path=self.env_file, 
      func=self.save_env_file, 
      title='Edit .env file'
    )
    return
  
  def save_env_file(self, content, dialog):
    with open(self.env_file, 'w') as file:
      file.write(content)
    dialog.accept()
    return
  
  
  def edit_addrs(self): 
    self.edit_file(
      file_path=self.addrs_file, 
      func=self.save_addrs_file, 
      title='Edit authorized addrs file'
    )
    return    
  
  
  def save_addrs_file(self, content, dialog):
    with open(self.addrs_file, 'w') as file:
      file.write(content)
    dialog.accept()
    return
  
  
  def view_config_files(self):
    config_startup_content = ''
    config_app_content = ''
    try:
      with open(self.config_startup_file, 'r') as file:
        config_startup_content = file.read()
      
      with open(self.config_app_file, 'r') as file:
        config_app_content = file.read()
    except FileNotFoundError:
      return

    # Create the text edit widget with Courier New font and light font color
    startup_text_edit = QTextEdit()
    startup_text_edit.setText(config_startup_content)
    startup_text_edit.setFont(QFont("Courier New", 11))
    startup_text_edit.setStyleSheet("color: #FFFFFF; background-color: #0D1F2D;")

    app_text_edit = QTextEdit()
    app_text_edit.setText(config_app_content)
    app_text_edit.setFont(QFont("Courier New", 11))
    app_text_edit.setStyleSheet("color: #FFFFFF; background-color: #0D1F2D;")

    # Create the dialog
    dialog = QDialog(self)
    dialog.setWindowTitle('View config files')
    dialog.setGeometry(0, 0, 1000, 900)  # Enlarge the edit window

    # Center the dialog on the screen
    screen_geometry = QApplication.desktop().screenGeometry()
    x = (screen_geometry.width() - dialog.width()) // 2
    y = (screen_geometry.height() - dialog.height()) // 2
    dialog.move(x, y)

    dialog_layout = QVBoxLayout()
    dialog_layout.addWidget(startup_text_edit)
    dialog_layout.addWidget(app_text_edit)

    # Save button
    save_button = QPushButton('Ok')
    save_button.clicked.connect(
      lambda: self.close_config_files(
        startup_text_edit.toPlainText(), app_text_edit.toPlainText(), dialog)
      )
    dialog_layout.addWidget(save_button)

    dialog.setLayout(dialog_layout)
    dialog.exec_()
    return  
  
  def close_config_files(self, txt_startup, txt_app, dialog):
    # TODO: edit files
    dialog.accept()
    return

  
  def check_data(self, data):
    result = False
    if 'timestamps' in data:
      self.__current_node_epoch = data.pop('epoch', -1)
      self.__current_node_epoch_avail = data.pop('epoch_avail', -1)
      self.__current_node_uptime = data.pop('uptime', -1)
      self.__current_node_ver = data.pop('version', '')
              
      start_time = data['timestamps'][0] 
      end_time = data['timestamps'][-1]
      current_timestamps = data['timestamps'].copy()
      if current_timestamps != self.__last_timesteps:
        self.__last_timesteps = current_timestamps
        data_size = len(data['timestamps'])
        if data_size > 0 and data_size > MAX_HISTORY_QUEUE:
          for key in data:
            if isinstance(data[key], list):
              data[key] = data[key][-MAX_HISTORY_QUEUE:]
        start_time = data['timestamps'][0] 
        end_time = data['timestamps'][-1]
        self.add_log('Data loaded & cleaned: {} timestamps from {} to {}'.format(
          len(data['timestamps']), start_time, end_time), debug=True
        )
        result = True
      else:
        self.add_log('Data already up-to-date. No new data.', debug=True)
    else:
      self.add_log('No timestamps data found in the file.', debug=True)
    return result

  def plot_data(self):
    data_path = os.path.join(self.volume_path, LOCAL_HISTORY_FILE)
    self.add_log(f'Loading data from: {data_path}', debug=True) 
    try:
      if os.path.exists(data_path):
        with open(data_path, 'r') as file:
          data = json.load(file)
        if self.check_data(data):
          self.plot_graphs(data)
      else:
        self.plot_graphs(None)
    except FileNotFoundError:
      self.plot_graphs(None)
    return  


  def plot_graphs(self, data=None, limit=100):
    if data is None:
      data = self.__last_plot_data
    else:
      self.__last_plot_data = deepcopy(data)
      
    timestamps = [
      datetime.fromisoformat(ts).timestamp() for ts in data['timestamps'][-limit:]
    ] if data and 'timestamps' in data else [datetime.now().timestamp()]
    start_time = datetime.fromtimestamp(timestamps[0]).strftime('%Y-%m-%d %H:%M:%S')
    end_time = datetime.fromtimestamp(timestamps[-1]).strftime('%Y-%m-%d %H:%M:%S')

    def update_plot(plot, timestamps, values, label, color):      
      plot.clear()
      plot.addLegend()
      values = [x for x in values if x is not None]
      if values:
        values = values[-limit:]
        plot.plot(timestamps, values, pen=pg.mkPen(color=color, width=2), name=label, color=color)
      else:
        plot.plot([0], [0], pen=None, symbol='o', symbolBrush=color, name='NO DATA')
      plot.setLabel('left', text=label, color=color)
      plot.setLabel('bottom', text='Time', color=color)
      if timestamps:
        plot.setLabel('bottom', f"Time ({start_time} to {end_time})", color=color)      
      plot.getAxis('bottom').autoVisible = False
      plot.getAxis('bottom').enableAutoSIPrefix(False)
      return
    

    # Plot CPU Load
    # Create the custom DateAxisItem
    cpu_data = data.get('cpu_load', []) if data else []
    cpu_date_axis = DateAxisItem(orientation='bottom')
    cpu_date_axis.setTimestamps(timestamps, parent="cpu")  # Pass the actual timestamps    
    self.cpu_plot.getAxis('bottom').setTickSpacing(60, 10)
    self.cpu_plot.getAxis('bottom').setStyle(tickTextOffset=10)
    self.cpu_plot.setAxisItems({'bottom': cpu_date_axis})
    self.cpu_plot.setTitle('CPU Load')
    color = 'white' if self._current_stylesheet == DARK_STYLESHEET else 'black'    
    self.add_log(f'Plotting data: {len(timestamps)} timestamps with color: {color}')    
    update_plot(self.cpu_plot, timestamps, cpu_data, 'CPU Load', color)

    # Plot Memory Load
    # Create the custom DateAxisItem
    mem_data = data.get('occupied_memory', []) if data else []
    mem_date_axis = DateAxisItem(orientation='bottom')
    mem_date_axis.setTimestamps(timestamps, parent="mem")  # Pass the actual timestamps    
    self.memory_plot.getAxis('bottom').setTickSpacing(60, 10)
    self.memory_plot.getAxis('bottom').setStyle(tickTextOffset=10)
    self.memory_plot.setAxisItems({'bottom': mem_date_axis})
    self.memory_plot.setTitle('Memory Load')
    # update_plot(self.memory_plot, timestamps, data.get('total_memory', []) if data else [], 'Total Memory', 'y')
    update_plot(self.memory_plot, timestamps, mem_data, 'Occupied Memory', color)

    # Plot GPU Load if available
    # Create the custom DateAxisItem
    gpu_data = data.get('gpu_load', []) if data else []
    gpu_date_axis = DateAxisItem(orientation='bottom')
    gpu_date_axis.setTimestamps(timestamps, parent="gpu")  # Pass the actual timestamps    
    self.gpu_plot.getAxis('bottom').setTickSpacing(60, 10)
    self.gpu_plot.getAxis('bottom').setStyle(tickTextOffset=10)
    self.gpu_plot.setAxisItems({'bottom': gpu_date_axis})
    self.gpu_plot.setTitle('GPU Load')
    update_plot(self.gpu_plot, timestamps, gpu_data, 'GPU Load', color)

    # Plot GPU Memory Load if available
    # Create the custom DateAxisItem
    gpu_mem_data = data.get('gpu_occupied_memory', []) if data else []
    gpumem_date_axis = DateAxisItem(orientation='bottom')
    gpumem_date_axis.setTimestamps(timestamps, parent="gpu_mem")  # Pass the actual timestamps    
    self.gpu_memory_plot.getAxis('bottom').setTickSpacing(60, 10)
    self.gpu_memory_plot.getAxis('bottom').setStyle(tickTextOffset=10)
    self.gpu_memory_plot.setAxisItems({'bottom': gpumem_date_axis})
    self.gpu_memory_plot.setTitle('GPU Memory Load')
    # update_plot(self.gpu_memory_plot, timestamps, data.get('gpu_total_memory', []) if data else [], 'Total GPU Memory', 'y')
    update_plot(self.gpu_memory_plot, timestamps, gpu_mem_data, 'Occupied GPU Memory', color)
    return



  def refresh_local_address(self):
    address_path = os.path.join(self.volume_path, LOCAL_ADDRESS_FILE)
    try:
      with open(address_path, 'r') as file:
        data = json.load(file)
        node_addr = data['address']
        node_alias= data.get('alias', '')
        node_eth_addr = data.get('eth_address', '')
        node_signature = data.get('signature', '')
        self.node_eth_addr = node_eth_addr
        self.node_signature = node_signature
        if node_addr != self.node_addr:
          self.node_addr = node_addr
          self.node_name = node_alias
          str_display = node_addr[:8] + '...' + node_addr[-8:]
          self.addressDisplay.setText('Addr: ' + str_display)
          self.nameDisplay.setText('Name: ' + node_alias)
          self.add_log(f'Local address updated: {self.node_addr} : {self.node_name}, ETH: {self.node_eth_addr}')
        # endif new address
      # endwith open                    
    except FileNotFoundError:
      self.addressDisplay.setText('Address file not found.')
      self.nameDisplay.setText('')
    except PermissionError as e:
      messaging_service.show_critical_message(self, "Permission Denied",
                           f"Unable to read the file at {address_path}. Please change the file permissions.")
    except Exception as e:
      self.add_log(f'Error loading address: {e}', debug=True)
    return
  
  def maybe_refresh_uptime(self):
    # update uptime, epoch and epoch avail
    uptime = self.__current_node_uptime
    node_epoch = self.__current_node_epoch
    node_epoch_avail = self.__current_node_epoch_avail
    ver = self.__current_node_ver
    color = 'white'
    if not self.container_last_run_status:
      uptime = "STOPPED"
      node_epoch = "N/A"
      node_epoch_avail = 0
      ver = "N/A"
      color = 'red'
    #end if overwrite if stopped      
    if uptime != self.__display_uptime:
      if self.__display_uptime is not None and node_epoch_avail is not None and node_epoch_avail > 0:
        color = 'lightgreen'
        
      self.node_uptime.setText(f'Up Time: {uptime}')
      self.node_uptime.setStyleSheet(f'color: {color}')
      
      self.node_epoch.setText(f'Epoch: {node_epoch}')
      self.node_epoch.setStyleSheet(f'color: {color}')
      
      prc = round(node_epoch_avail * 100 if node_epoch_avail > 0 else node_epoch_avail, 2) if node_epoch_avail is not None else 0
      self.node_epoch_avail.setText(f'Epoch avail: {prc}%')
      self.node_epoch_avail.setStyleSheet(f'color: {color}')
      
      self.node_version.setText(f'Running ver: {ver}')
      self.node_version.setStyleSheet(f'color: {color}')
      
      self.__display_uptime = uptime
    return
    

  def copy_address(self):
    clipboard = QApplication.clipboard()
    clipboard.setText(self.node_addr)
    return
    
  def refresh_all(self):
    t_t1 = time()
    self.update_toggle_button_text()
    t_te = time() - t_t1
    if not self.is_container_running():
      self.add_log('Edge Node is not running. Skipping refresh.')
    else:
      t0 = time()
      self.refresh_local_address()    
      t1 = time()
      self.plot_data()
      t2 = time()
      #
      t3 = time()
      self.maybe_refresh_uptime()
      t4 = time()
      self.add_log(
        f'{t1 - t0:.2f}s (refresh_local_address), {t2 - t1:.2f}s (plot_data), {t_te:.2f}s (update_toggle_button_text), {t4 - t3:.2f}s (maybe_refresh_uptime)',
        debug=True
      )
    #endif container is running
    if (time() - self.__last_auto_update_check) > AUTO_UPDATE_CHECK_INTERVAL:
      verbose = self.__last_auto_update_check == 0
      self.__last_auto_update_check = time()
      self.check_for_updates(verbose=verbose or FULL_DEBUG)
    return    



  def dapp_button_clicked(self):
    return
  
  
  def explorer_button_clicked(self):
    return
  
  
  def toggle_force_debug(self):
    self.__force_debug = self.force_debug_checkbox.isChecked()
    if self.__force_debug:
      self.add_log('Force Debug enabled.')
    else:
      self.add_log('Force Debug disabled.')
    return