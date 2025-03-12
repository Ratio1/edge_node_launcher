from ver import __VER__

FULL_DEBUG = True

# ============================================================================
# DIRECTORY AND FILE CONSTANTS
# ============================================================================
HOME_SUBFOLDER = ".ratio1"
CONFIG_DIR = ".ratio1/edge_node_launcher"
E2_PEM_FILE = 'e2.pem'

# ============================================================================
# DOCKER CONSTANTS
# ============================================================================
DOCKER_VOLUME = 'ratio1_vol'
DOCKER_IMAGE = 'ratio1/edge_node'
DOCKER_TAG = 'testnet'
DOCKER_CONTAINER_NAME = 'r1node'
DOCKER_VOLUME_PATH = '/edge_node/_local_cache'

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================
REFRESH_TIME = 20_000
MAX_HISTORY_QUEUE = 5 * 60 // 10  # 5 minutes @ 10 seconds each hb
AUTO_UPDATE_CHECK_INTERVAL = 60
DOCKER_IMAGE_AUTO_UPDATE_CHECK_INTERVAL = 300  # 5 minutes
MAX_ALIAS_LENGTH = 15  # Maximum length for aliases (node name and authorized addresses)

# ============================================================================
# UI TEXT CONSTANTS
# ============================================================================
# Window and titles
WINDOW_TITLE = f'Edge Node Manager v{__VER__}'

# Button texts
LAUNCH_CONTAINER_BUTTON_TEXT = 'Start Edge Node'
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

# Common style properties that don't depend on theme
COMMON_STYLES = {
    "font_size": "14px",
    "border_radius": "15px",
    "progress_height": "30px",
    "button_padding": "10px 20px",
    "button_font_size": "16px",
    "button_margin": "4px 2px",
    "button_border_radius": "15px",
    "combo_border_radius": "15px",
    "combo_padding": "4px",
    "combo_min_width": "100px",
    "combo_dropdown_width": "20px",
    "text_align_center": "center"
}

COMMON_COLORS = {
    "start_button_bg": "#00FF00",
    "stop_button_bg": "#F44336",
}

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
    
    # Log view specific colors
    "log_view_bg": "#0D1F2D",
    "log_view_text": "white",
    "log_view_border": "#1E90FF",
    
    # Info box specific colors
    "info_box_bg": "#0D1F2D",
    "info_box_text": "white",
    "info_box_border": "#1E90FF",
    
    # Graph specific colors
    "graph_bg": "#243447",
    "graph_border": "#87CEEB",
    "graph_text": "white",
    "graph_cpu_color": "#1E90FF",
    "graph_memory_color": "#4CAF50",
    "graph_gpu_color": "#FFD700",
    "graph_gpu_memory_color": "#FF6B6B",
    
    "text_edit_bg": "#0D1F2D",
    "text_edit_border": "#1E90FF",
    "plot_bg": "#243447",
    "plot_border": "#87CEEB",
    "combo_bg": "#2A3440",
    "combo_border": "#4A5561",
    "combo_hover_bg": "#3A4450",
    "combo_hover_border": "#5A6571",
    "combo_arrow_color": "#B0B9C6",
    "combo_dropdown_bg": "#2A3440",
    "combo_dropdown_select_bg": "#3A4450",
    "combo_dropdown_select_color": "white",
    "green_highlight": "#4CAF50",
    "button_copy_address_bg": "transparent",
    "add_node_button_bg": "#1E90FF",
    "add_node_button_border": "#87CEEB",
    "add_node_button_hover": "#104E8B",
    "confirm_button_bg": "#4CAF50",
    "confirm_button_border": "#45A049",
    "confirm_button_hover": "#45A049",
    "cancel_button_bg": "#F44336",
    "cancel_button_border": "#D32F2F",
    "cancel_button_hover": "#D32F2F",
    
    # Toggle button states
    "toggle_button_start_bg": "#4CAF50",
    "toggle_button_start_hover": "#45A049",
    "toggle_button_stop_bg": "#F44336",
    "toggle_button_stop_hover": "#D32F2F",
    "toggle_button_disabled_bg": "gray",
    "toggle_button_disabled_hover": "darkgray"
}

# Color definitions for light theme
LIGHT_COLORS = {
    "text_color": "black",
    "bg_color": "white",
    "border_color": "#cccccc",
    "hover_color": "#f5f5f5",
    "button_bg": "#D3D3D3",
    "button_border": "#A9A9A9",
    "button_hover": "#A9A9A9",
    "progress_border": "#D3D3D3",
    "progress_chunk": "#D3D3D3",
    "widget_bg": "#F0F0F0",
    
    # Log view specific colors
    "log_view_bg": "#FFFFFF",
    "log_view_text": "black",
    "log_view_border": "#D3D3D3",
    
    # Info box specific colors
    "info_box_bg": "#FFFFFF",
    "info_box_text": "black",
    "info_box_border": "#D3D3D3",
    
    # Graph specific colors
    "graph_bg": "#FFFFFF",
    "graph_border": "#D3D3D3",
    "graph_text": "black",
    "graph_cpu_color": "#0066CC",
    "graph_memory_color": "#2E8B57",
    "graph_gpu_color": "#DAA520",
    "graph_gpu_memory_color": "#CD5C5C",
    
    "text_edit_bg": "#FFFFFF",
    "text_edit_border": "#D3D3D3",
    "plot_bg": "#FFFFFF",
    "plot_border": "#A9A9A9",
    "combo_bg": "#FFFFFF",
    "combo_border": "#CCCCCC",
    "combo_hover_bg": "#F5F5F5", 
    "combo_hover_border": "#4CAF50",
    "combo_arrow_color": "#666666",
    "combo_dropdown_bg": "#FFFFFF",
    "combo_dropdown_select_bg": "#F5F5F5",
    "combo_dropdown_select_color": "black",
    "green_highlight": "#4CAF50",
    "button_copy_address_bg": "transparent",
    "add_node_button_bg": "#D3D3D3",
    "add_node_button_border": "#A9A9A9",
    "add_node_button_hover": "#A9A9A9",
    "confirm_button_bg": "#4CAF50",
    "confirm_button_border": "#45A049",
    "confirm_button_hover": "#45A049",
    "cancel_button_bg": "#F44336",
    "cancel_button_border": "#D32F2F",
    "cancel_button_hover": "#D32F2F",
    
    # Toggle button states
    "toggle_button_start_bg": "#4CAF50",
    "toggle_button_start_hover": "#45A049",
    "toggle_button_stop_bg": "#F44336",
    "toggle_button_stop_hover": "#D32F2F",
    "toggle_button_disabled_bg": "gray",
    "toggle_button_disabled_hover": "darkgray"
}

# Merge common styles with theme-specific colors
DARK_THEME = {**COMMON_STYLES, **DARK_COLORS}
LIGHT_THEME = {**COMMON_STYLES, **LIGHT_COLORS}

# Checkbox style template
CHECKBOX_STYLE_TEMPLATE = """
    QCheckBox {{
        color: {text_color};
    }}
"""

# Common stylesheet template with placeholders for theme-specific values
COMMON_STYLESHEET_TEMPLATE = """
  QLabel {{
    font-size: {font_size};
    color: {text_color};
  }}
  QProgressBar {{
    border: 2px solid {progress_border};
    border-radius: {border_radius};
    text-align: {text_align_center};
    height: {progress_height};
    color: {text_color};
  }}
  QProgressBar::chunk {{
    background-color: {progress_chunk};
  }}
  QDialog, QWidget {{
    background-color: {widget_bg};
  }}
  QTextEdit {{
    background-color: {log_view_bg};
    color: {log_view_text};
    font-size: {font_size};
    border: 1px solid {log_view_border};
    border-radius: {border_radius};
    padding: 8px;
    margin-bottom: 4px;
  }}
  PlotWidget, QWidget[class="plot-container"] {{
    background-color: {graph_bg};
    border: 1px solid {graph_border};
    border-radius: {border_radius};
    padding: 8px;
  }}
  PlotWidget > * {{
    background-color: transparent;
  }}
  PlotWidget LabelItem {{
    color: {graph_text};
  }}
  QComboBox {{
    color: {text_color};
    background-color: {combo_bg};
    border: 1px solid {combo_border};
    border-radius: {combo_border_radius};
    padding: 5px 10px;
    min-width: {combo_min_width};
    min-height: 32px;
    max-height: 32px;
    font-family: "Courier New";
    font-size: 10pt;
  }}
  QComboBox:hover {{
    background-color: {combo_hover_bg};
    border: 1px solid {combo_hover_border};
  }}
  QComboBox:focus {{
    border: 1px solid {combo_hover_border};
  }}
  QComboBox::drop-down {{
    border: none;
    width: 30px;
  }}
  QComboBox::down-arrow {{
    image: none;
    border: none;
  }}
  QComboBox QAbstractItemView {{
    background-color: {combo_dropdown_bg};
    color: {text_color};
    selection-background-color: {combo_dropdown_select_bg};
    selection-color: {combo_dropdown_select_color};
    border: 1px solid {combo_border};
    border-radius: {border_radius};
    padding: 5px;
  }}
  QComboBox QAbstractItemView::item {{
    min-height: 24px;
    padding: 3px 5px;
    text-align:center;
  }}
  QComboBox QAbstractItemView::item:hover {{
    background-color: {combo_hover_bg};
  }}
  QComboBox QAbstractItemView::item:selected {{
    background-color: {combo_dropdown_select_bg};
  }}
  QCheckBox {{
    color: {text_color};
  }}
  QPushButton {{
    background-color: {button_bg}; 
    color: {text_color}; 
    border: 2px solid {button_border}; 
    padding: {button_padding}; 
    font-size: {button_font_size}; 
    margin: {button_margin};
    border-radius: {button_border_radius};
  }}
  QPushButton:hover {{
    background-color: {button_hover};
  }}
  QPushButton[type="confirm"] {{
    background-color: {confirm_button_bg};
    border: 2px solid {confirm_button_border};
  }}
  QPushButton[type="confirm"]:hover {{
    background-color: {confirm_button_hover};
  }}
  QPushButton[type="cancel"] {{
    background-color: {cancel_button_bg};
    border: 2px solid {cancel_button_border};
  }}
  QPushButton[type="cancel"]:hover {{
    background-color: {cancel_button_hover};
  }}
  #copyAddrButton, #copyEthButton {{
    background-color: {button_copy_address_bg};
    border: none;
    padding: 0px;
    margin: 0px;
  }}
  #startNodeButton {{
    min-height: 40px;
  }}
  #addNodeButton {{
    background-color: {add_node_button_bg};
    color: {text_color};
    border: 2px solid {add_node_button_border};
    padding: 5px 10px;
    border-radius: {border_radius};
    min-height: 32px;
    max-height: 32px;
  }}
  #addNodeButton:hover {{
    background-color: {add_node_button_hover};
  }}
  #toggleContainerButton {{
    min-height: 40px;
    max-height: 40px;
    font-weight: bold;
  }}
  #infoBox {{
    background-color: {info_box_bg};
    border: 1px solid {info_box_border};
    border-radius: {border_radius};
    margin: 6px;
    padding: 8px;
    color: {info_box_text};
  }}
  #infoBox QLabel {{
    color: {info_box_text};
    font-family: "Courier New";
    font-size: 10pt;
    margin: 2px;
  }}
  #infoBox QPushButton {{
    background-color: {button_copy_address_bg};
    border: none;
    padding: 0px;
    margin: 0px;
    color: {text_color};
  }}
  #infoBoxText QLabel {{
    color: {info_box_text};
  }}
  #myComboPopup {{
    background-color: #2e2e2e; 
    border: none; 
}}

"""

# Apply the common template with dark theme values
DARK_STYLESHEET = COMMON_STYLESHEET_TEMPLATE.format(**DARK_THEME)

# Apply the common template with light theme values, with additional light-specific styles
LIGHT_STYLESHEET = COMMON_STYLESHEET_TEMPLATE.format(**LIGHT_THEME) + """
  PlotWidget .axis {
    color: black;
  }

  PlotWidget .plotLabel {
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

