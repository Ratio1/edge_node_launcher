from ver import __VER__

FULL_DEBUG = True

# ============================================================================
# DIRECTORY AND FILE CONSTANTS
# ============================================================================
HOME_SUBFOLDER = ".naeural_launcher"
CONFIG_DIR = ".ratio1/edge_node_launcher"
E2_PEM_FILE = 'e2.pem'

# ============================================================================
# DOCKER CONSTANTS
# ============================================================================
DOCKER_VOLUME = 'naeural_vol'
DOCKER_IMAGE = 'naeural/edge_node'
DOCKER_TAG = 'testnet'
DOCKER_CONTAINER_NAME = 'r1node'
DOCKER_VOLUME_PATH = '/edge_node/_local_cache'

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================
SHOW_MODE_SWITCH = False  # Whether to show the Simple/Pro mode switch in the UI
REFRESH_TIME = 20_000
MAX_HISTORY_QUEUE = 5 * 60 // 10  # 5 minutes @ 10 seconds each hb
AUTO_UPDATE_CHECK_INTERVAL = 60
MAX_ALIAS_LENGTH = 15  # Maximum length for aliases (node name and authorized addresses)

# ============================================================================
# UI TEXT CONSTANTS
# ============================================================================
# Window and titles
WINDOW_TITLE = f'Edge Node Manager v{__VER__}'

# Button texts
LAUNCH_CONTAINER_BUTTON_TEXT = 'Launch Edge Node'
STOP_CONTAINER_BUTTON_TEXT = 'Stop Edge Node'
DAPP_BUTTON_TEXT = 'Launch dApp'
EXPLORER_BUTTON_TEXT = 'Ratio1 Explorer'
DELETE_AND_RESTART_BUTTON_TEXT = 'Reset Node Address'
REFRESH_LOCAL_ADDRESS_BUTTON_TEXT = 'Refresh Local Address'
COPY_ADDRESS_BUTTON_TEXT = 'Copy Address'
COPY_ETHEREUM_ADDRESS_BUTTON_TEXT = 'Copy Ethereum Address'
RENAME_NODE_BUTTON_TEXT = 'Change Node Alias'
LIGHT_DASHBOARD_BUTTON_TEXT = 'Switch to Light Theme'
DARK_DASHBOARD_BUTTON_TEXT = 'Switch to Dark Theme'
DOWNLOAD_DOCKER_BUTTON_TEXT = 'Download Docker'

# Label texts
LOCAL_NODE_ADDRESS_LABEL_TEXT = 'Local Node Address'
UPTIME_LABEL = 'Up Time:'
EPOCH_LABEL = 'Epoch:'
EPOCH_AVAIL_LABEL = 'Epochs avail:'
NODE_VERSION_LABEL = 'Running ver:'

# Status texts
NO_CONTAINER_SELECTED_TEXT = 'Address: No container selected'
ETH_ADDRESS_NOT_AVAILABLE_TEXT = 'ETH Address: Not available'
NODE_NOT_RUNNING_TEXT = 'Address: Node not running'
ERROR_GETTING_NODE_INFO_TEXT = 'Address: Error getting node info'
NAME_PREFIX_TEXT = 'Name: '
ADDRESS_PREFIX_TEXT = 'Address: '
LOCAL_ADDRESS_PREFIX_TEXT = 'Local Address: '
ETH_ADDRESS_PREFIX_TEXT = 'ETH Address: '
UPTIME_PREFIX_TEXT = 'Uptime: '
EMPTY_DASH_TEXT = '-'

# Button states
NO_CONTAINER_FOUND_TEXT = 'No Container Found'
HOST_OFFLINE_TEXT = 'Host Offline'
CHECKING_HOST_TEXT = 'Checking Host...'
SSH_ERROR_TEXT = 'SSH Error'
DOCKER_NOT_FOUND_TEXT = 'Docker Not Found'
DOCKER_NOT_RUNNING_TEXT = 'Docker Not Running'
DOCKER_CHECK_FAILED_TEXT = 'Docker Check Failed'
CONTAINER_CHECK_FAILED_TEXT = 'Container Check Failed'
CONNECTION_FAILED_TEXT = 'Connection Failed'
SELECT_HOST_TEXT = 'Select Host...'

# Plot titles
CPU_LOAD_TITLE = 'CPU Load'
MEMORY_USAGE_TITLE = 'Memory Usage'
GPU_LOAD_TITLE = 'GPU Load'
GPU_MEMORY_LOAD_TITLE = 'GPU Memory Load'

# ============================================================================
# TOOLTIP TEXTS
# ============================================================================
DOCKER_DOWNLOAD_TOOLTIP = 'Ratio1 Edge Node requires Docker Desktop running in parallel'
COPY_ADDRESS_TOOLTIP = 'Copy address'
COPY_ETH_ADDRESS_TOOLTIP = 'Copy Ethereum address'

# ============================================================================
# DIALOG TEXTS
# ============================================================================
# Dialog titles
ADD_NEW_NODE_DIALOG_TITLE = 'Add New Node'
RENAME_NODE_DIALOG_TITLE = 'Rename Node'
EDIT_AUTHORIZED_ADDRESSES_DIALOG_TITLE = 'Edit Authorized Addresses'
VIEW_CONFIG_FILES_DIALOG_TITLE = 'View Configuration Files'
EDIT_ENV_FILE_DIALOG_TITLE = 'Edit .env File'

# Dialog messages
RESET_NODE_CONFIRMATION_TEXT = 'Are you sure you want to reset this node?'
ENTER_NODE_NAME_TEXT = 'Enter a friendly name for this node:'
RESETTING_NODE_ADDRESS_TEXT = 'Resetting node address...'

# Input placeholders
ENTER_NODE_NAME_PLACEHOLDER = 'Enter node name'
ENTER_FRIENDLY_NODE_NAME_PLACEHOLDER = 'Enter a friendly name for your node'
ENTER_ADDRESS_PLACEHOLDER = 'Enter address'
ENTER_ALIAS_PLACEHOLDER = 'Enter alias'

# ============================================================================
# LOG MESSAGES
# ============================================================================
SUCCESS_NODE_CREATION_LOG = 'Successfully created new node: {}'
FAILED_NODE_CREATION_LOG = 'Failed to create new node: {}'

# ============================================================================
# ENVIRONMENT SETTINGS
# ============================================================================
ENVIRONMENTS = {
    'mainnet': 'Mainnet',
    'testnet': 'Testnet',
    'devnet': 'Devnet'
}

DAPP_URLS = {
    'mainnet': 'https://app.ratio1.ai/',
    'testnet': 'https://testnet-app.ratio1.ai/',
    'devnet': 'https://devnet-app.ratio1.ai/'
}

DEFAULT_ENVIRONMENT = 'testnet'

# ============================================================================
# TEMPLATES
# ============================================================================
ENV_TEMPLATE = '''
# LOCAL FILE TEMPLATE

# admin
EE_ID={}
EE_SUPERVISOR=false
EE_DEVICE=cuda:0


# MinIO / S3
EE_MINIO_ENDPOINT=endpoint
EE_MINIO_ACCESS_KEY=access_key
EE_MINIO_SECRET_KEY=secret_key
EE_MINIO_SECURE=false
EE_MINIO_UPLOAD_BUCKET=bucket


# MQTT
EE_MQTT_PORT=8883
EE_MQTT_SUBTOPIC=address
EE_MQTT_CERT=

EE_NGROK_AUTH_TOKEN=ngrok-auth-token
EE_NGROK_EDGE_LABEL=ngrok-edge-label

# Misc
EE_GITVER=token_for_accessing_private_repositories
EE_OPENAI=token_for_accessing_openai_api
EE_HF_TOKEN=token_for_accessing_huggingface_api
'''

# ============================================================================
# STYLESHEETS
# ============================================================================

# Color definitions for dark theme
DARK_COLORS = {
    "text_color": "white",
    "bg_color": "#2b2b2b",
    "border_color": "#555555",
    "hover_color": "#3b3b3b",
    "button_bg": "#1E90FF",
    "button_border": "#87CEEB",
    "button_hover": "#104E8B",
    "progress_border": "#1E90FF",
    "progress_chunk": "#1E90FF",
    "widget_bg": "#0D1F2D",
    "text_edit_bg": "#0D1F2D",
    "text_edit_border": "#1E90FF",
    "plot_bg": "#243447",
    "plot_border": "#87CEEB"
}

# Color definitions for light theme
LIGHT_COLORS = {
    "text_color": "black",
    "bg_color": "white",
    "border_color": "#cccccc",
    "hover_color": "#f5f5f5",
    "button_bg": "#00FF00",  # Green for buttons
    "button_border": "#6185f7",
    "button_hover": "#A9A9A9",  # Red hover color
    "progress_border": "#D3D3D3",
    "progress_chunk": "#D3D3D3",
    "widget_bg": "#F0F0F0",
    "text_edit_bg": "#FFFFFF",
    "text_edit_border": "#D3D3D3",
    "plot_bg": "#FFFFFF",
    "plot_border": "#A9A9A9"
}

# Checkbox style template
CHECKBOX_STYLE_TEMPLATE = """
    QCheckBox {{
        color: {text_color};
    }}
"""

DARK_STYLESHEET = """
  QWidget {
    background-color: #0D1F2D;
  }
  
  QPushButton {
    background-color: #00FF00; 
    color: white; 
    border: 2px solid #87CEEB; 
    padding: 10px 20px; 
    font-size: 16px; 
    margin: 4px 2px;
    border-radius: 15px;
  }
  QPushButton:hover {
    background-color: #104E8B;
  }
  QLabel {
    font-size: 14px;
    color: white;
  }
  QProgressBar {
    border: 2px solid #1E90FF;
    border-radius: 5px;
    text-align: center;
    height: 30px;
    color: white;
  }
  QProgressBar::chunk {
    background-color: #1E90FF;
  }
  QDialog, QWidget {
    background-color: #0D1F2D;
  }
  QTextEdit {
    background-color: #0D1F2D;
    color: white;
    font-size: 14px;
    border: 1px solid #1E90FF;
    border-radius: 5px;
  }
  
  PlotWidget {
    background-color: #243447;
    border: 1px solid #87CEEB;
    color: white;  
  }

  PlotWidget LabelItem {
    color: white;
  }
  
  QComboBox {
    color: white;
    background-color: #2b2b2b;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px;
    min-width: 100px;
  }
  QComboBox:hover {
    background-color: #3b3b3b;
    border: 1px solid #4CAF50;
  }
  QComboBox::drop-down {
    border: none;
    width: 20px;
  }
  QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid white;
    margin-right: 8px;
  }
  QComboBox QAbstractItemView {
    color: white;
    background-color: #2b2b2b;
    selection-background-color: #3b3b3b;
    selection-color: white;
  }
  
  QCheckBox {
    color: white;
  }
"""

LIGHT_STYLESHEET = """
  QWidget {
    background-color: #F0F0F0;
  }
  
  QPushButton {
    background-color: #D3D3D3;
    color: black;
    border: 2px solid #A9A9A9;
    padding: 10px 20px;
    font-size: 16px;
    margin: 4px 2px;
    border-radius: 15px;
  }
  QPushButton:hover {
    background-color: #A9A9A9;
  }
  QLabel {
    font-size: 14px;
    color: black;
  }
  QProgressBar {
    border: 2px solid #D3D3D3;
    border-radius: 5px;
    text-align: center;
    height: 30px;
    color: black;
  }
  QProgressBar::chunk {
    background-color: #D3D3D3;
  }
  QDialog, QWidget {
    background-color: #F0F0F0;
  }
  QTextEdit {
    background-color: #FFFFFF;
    color: black;
    font-size: 14px;
    border: 1px solid #D3D3D3;
    border-radius: 5px;
  }
  
  PlotWidget {
    background-color: #FFFFFF;
    border: 1px solid #A9A9A9;
  }

  PlotWidget LabelItem {
    color: black;
  }

  PlotWidget .axis {
    color: black;
  }

  QComboBox {
    color: black;
    background-color: white;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 4px;
    min-width: 100px;
  }
  QComboBox:hover {
    background-color: #f5f5f5;
    border: 1px solid #4CAF50;
  }
  QComboBox::drop-down {
    border: none;
    width: 20px;
  }
  QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid black;
    margin-right: 8px;
  }
  QComboBox QAbstractItemView {
    color: black;
    background-color: white;
    selection-background-color: #f5f5f5;
    selection-color: black;
  }
  
  QCheckBox {
    color: black;
  }
"""

# Notification messages
NOTIFICATION_TITLE_STRINGS_ENUM = {
    'success': 'Success',
    'error': 'Error',
    'warning': 'Warning',
    'info': 'Information'
}
NOTIFICATION_ADDRESS_COPIED = "Address {address} copied to clipboard"
NOTIFICATION_ADDRESS_COPY_FAILED = "No address available to copy. Try again after launching the Edge Node."

