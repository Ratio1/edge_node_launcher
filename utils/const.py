from ver import __VER__

FULL_DEBUG = True


# ============================================================================
# URLs
# ============================================================================
# GITHUB_API_URL = 'https://api.github.com/repos/Ratio1/edge_node_launcher/releases/latest' #FIXME
GITHUB_API_URL = 'https://api.github.com/repos/vitalii-t12/edge_node_launcher_private/releases/latest'

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
DOCKER_TAG = 'mainnet'
DOCKER_CONTAINER_NAME = 'r1node'
DOCKER_VOLUME_PATH = '/edge_node/_local_cache'

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================
REFRESH_TIME = 20_000
MAX_HISTORY_QUEUE = 5 * 60 // 10  # 5 minutes @ 10 seconds each hb
AUTO_UPDATE_CHECK_INTERVAL = 3600 # 1 hour
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

DEFAULT_ENVIRONMENT = 'mainnet'

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
    "button_margin": "4px 5px",
    "button_border_radius": "15px",
    "combo_border_radius": "15px",
    "combo_padding": "4px",
    "combo_min_width": "100px",
    "combo_dropdown_width": "20px",
    "text_align_center": "center",
    "font_weight_normal": "normal",
    "font_weight_bold": "bold",
    "button_font_weight": "normal",
    "info_box_font_weight": "normal"
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
    "button_bg": "#0071EA",
    "button_border": "transparent",
    "button_hover": "#0679F3",
    "progress_border": "#1E90FF",
    "progress_chunk": "#1E90FF",
    "widget_bg": "#000C29",
    "debug_checkbox_color": "white",  # Orange for dark theme debug checkbox
    
    # Log view specific colors
    "log_view_bg": "#04254F",
    "log_view_text": "white",
    "log_view_border": "#1E90FF",
    
    # Info box specific colors
    "info_box_bg": "#04254F",
    "info_box_text": "white",
    "info_box_border": "#1E90FF",
    
    # Graph specific colors
    "graph_bg": "#001A3A",
    "graph_border": "#10386A",
    "graph_text": "white",
    "graph_cpu_color": "#1E90FF",
    "graph_memory_color": "#4CAF50",
    "graph_gpu_color": "#FFD700",
    "graph_gpu_memory_color": "#FF6B6B",
    
    "text_edit_bg": "#FFFFFF",
    "text_edit_border": "#D3D3D3",
    "plot_bg": "#FFFFFF",
    "plot_border": "#A9A9A9",
    "green_highlight": "red",
    "button_copy_address_bg": "transparent",
    "add_node_button_bg": "#0071EA",
    "add_node_button_border": "transparent",
    "add_node_button_hover": "#0679F3",
    "add_node_button_hover_text": "#FFFFFF",
    "confirm_button_bg": "#1B47F7",
    "confirm_button_border": "#45A049",
    "confirm_button_hover": "#45A049",
    "cancel_button_bg": "#F44336",
    "cancel_button_border": "#D32F2F",
    "cancel_button_hover": "#D32F2F",
    
    # Toggle button states
    "toggle_button_start_bg": "#1B47F7",
    "toggle_button_start_hover": "#4458FF",
    "toggle_button_start_border": "transparent",
    "toggle_button_start_text": "white",
    "toggle_button_stop_bg": "#FADC33",
    "toggle_button_stop_hover": "#FFE138",
    "toggle_button_stop_border": "transparent",
    "toggle_button_stop_text": "#C4AC26",
    "toggle_button_disabled_bg": "gray",
    "toggle_button_disabled_hover": "darkgray",
    "toggle_button_disabled_border": "darkgray",
    "toggle_button_disabled_text": "black",
    "toggle_button_border": "#87CEEB",

    # ComboBox popup specific colors
    "combo_bg": "#F9F9F9",
    "combo_border": "#10386A",
    "combo_hover_bg": "#F0F7FF",
    "combo_hover_border": "#0071EA",
    "combo_arrow_color": "transparent",
    "combo_dropdown_bg": "#FFFFFF",
    "combo_dropdown_select_bg": "red",
    "combo_dropdown_select_color": "black",
    "combobox_popup_border_color": "#1E90FF",
    "combobox_popup_bg_color": "#04254F",
    "combobox_popup_item_hover_bg": "transparent",
    "combobox_popup_item_selected_bg": "#1B47F7",
    "combobox_popup_item_selected_text": "white",
    "combobox_text_color": "#333333",
    "combo_rectangle_text_color": "white",
}

# Color definitions for light theme
LIGHT_COLORS = {
    "text_color": "white",
    "bg_color": "white",
    "border_color": "#cccccc",
    "hover_color": "#f5f5f5",
    "button_bg": "#0071EA",
    "button_border": "transparent",
    "button_hover": "#0679F3",
    "progress_border": "#D3D3D3",
    "progress_chunk": "#D3D3D3",
    "widget_bg": "#E6E6EA",
    "debug_checkbox_color": "black",  # Blue for light theme debug checkbox
    
    # Log view specific colors
    "log_view_bg": "#FFFFFF",
    "log_view_text": "black",
    "log_view_border": "#D3D3D3",
    
    # Info box specific colors
    "info_box_bg": "#FFFFFF",
    "info_box_text": "black",
    "info_box_border": "#D3D3D3",
    
    # Graph specific colors
    "graph_bg": "#F4F4F8",
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
    "green_highlight": "red",
    "button_copy_address_bg": "transparent",
    "add_node_button_bg": "#0071EA",
    "add_node_button_border": "transparent",
    "add_node_button_hover": "#0679F3",
    "add_node_button_hover_text": "#FFFFFF",
    "confirm_button_bg": "#1B47F7",
    "confirm_button_border": "#45A049",
    "confirm_button_hover": "#45A049",
    "cancel_button_bg": "#F44336",
    "cancel_button_border": "#D32F2F",
    "cancel_button_hover": "#D32F2F",
    
    # Toggle button states
    "toggle_button_start_bg": "#1B47F7",
    "toggle_button_start_hover": "#4458FF",
    "toggle_button_start_border": "transparent",
    "toggle_button_start_text": "white",
    "toggle_button_stop_bg": "#FADC33",
    "toggle_button_stop_hover": "#FFE138",
    "toggle_button_stop_border": "transparent",
    "toggle_button_stop_text": "#C4AC26",
    "toggle_button_disabled_bg": "gray",
    "toggle_button_disabled_hover": "darkgray",
    "toggle_button_disabled_border": "darkgray",
    "toggle_button_disabled_text": "black",
    "toggle_button_border": "#87CEEB",

    # ComboBox popup specific colors
    "combo_bg": "#F9F9F9",
    "combo_border": "#D0D0D0",
    "combo_hover_bg": "#F0F7FF",
    "combo_hover_border": "#1B47F7",
    "combo_arrow_color": "transparent",
    "combo_dropdown_bg": "#FFFFFF",
    "combo_dropdown_select_bg": "red",
    "combo_dropdown_select_color": "black",
    "combobox_popup_border_color": "#D0D0D0",
    "combobox_popup_bg_color": "#F4F4F8",
    "combobox_popup_item_hover_bg": "transparent",
    "combobox_popup_item_selected_bg": "#1B47F7",
    "combobox_popup_item_selected_text": "white",
    "combobox_text_color": "#333333",
    "combo_rectangle_text_color": "#1B47F7",
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

# Debug checkbox style template
DEBUG_CHECKBOX_STYLE_TEMPLATE = """
    QCheckBox {{
        color: {debug_checkbox_color};
        font-weight: bold;
    }}
"""

# Detailed checkbox styling with theme-specific customization
DETAILED_CHECKBOX_STYLE = """
    QCheckBox {{
        margin-top: 4px;
        spacing: 8px;
        padding: 4px;
        color: {debug_checkbox_color};
        font-weight: bold;
    }}
    
    QCheckBox:hover {{
        background-color: transparent;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 15px;
        border: 1px solid #666;
    }}
    
    QCheckBox::indicator:unchecked {{
        background-color: transparent;
    }}
    
    QCheckBox::indicator:checked {{
        background-color: #4CAF50;
        border-color: #4CAF50;
        image: url(:/icons/check.png);
    }}
    
    QCheckBox::indicator:checked:hover {{
        background-color: #45a049;
        border-color: #45a049;
    }}
    
    /* Dark theme specific */
    .dark QCheckBox {{
        color: {debug_checkbox_color};
    }}
    
    .dark QCheckBox::indicator:unchecked {{
        border-color: #888;
        background-color: #333;
    }}
    
    /* Light theme specific */
    .light QCheckBox {{
        color: {debug_checkbox_color};
    }}
    
    .light QCheckBox::indicator:unchecked {{
        border-color: #666;
        background-color: #ffffff;
    }}
"""

# Common stylesheet template with placeholders for theme-specific values
COMMON_STYLESHEET_TEMPLATE = """
  QLabel {{
    font-size: {font_size};
    color: {text_color};
  }}
  QProgressBar {{
    border: 1px solid {progress_border};
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
    margin-bottom: 6px;
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
    padding: 0px;
    margin-left: 6px;
    margin-right: 6px;
    min-width: {combo_min_width};
    min-height: 32px;
    max-height: 32px;
    font-family: "Courier New";
    font-size: 10pt;
    text-align: center;
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
    width: 0px;
  }}
  QComboBox::down-arrow {{
    image: none;
    border: none;
    width: 0px;
    height: 0px;
  }}
  QComboBox QAbstractItemView {{
    background-color: {combo_dropdown_bg};
    color: {text_color};
    selection-background-color: {combo_dropdown_select_bg};
    selection-color: {combo_dropdown_select_color};
    border: 1px solid {combo_border};
    border-radius: {border_radius};
    padding: 5px;
    min-width: 190px;
  }}
  QComboBox QAbstractItemView::item {{
    min-height: 24px;
    padding: 3px 5px;
    text-align: center;
  }}
  QComboBox QAbstractItemView::item:hover {{
    background-color: {combo_hover_bg};
  }}
  QComboBox QAbstractItemView::item:selected {{
    background-color: {combo_dropdown_select_bg};
  }}
  QPushButton {{
    background-color: {button_bg}; 
    color: {text_color}; 
    border: 1px solid {button_border}; 
    padding: {button_padding}; 
    font-size: {button_font_size};
    font-weight: {button_font_weight}; 
    margin: {button_margin};
    margin-left: 6px;
    margin-right: 6px;
    border-radius: {button_border_radius};
  }}
  QPushButton:hover {{
    background-color: {button_hover};
  }}
  QPushButton[type="confirm"] {{
    background-color: {confirm_button_bg};
    border: 1px solid {confirm_button_border};
  }}
  QPushButton[type="confirm"]:hover {{
    background-color: {confirm_button_hover};
  }}
  QPushButton[type="cancel"] {{
    background-color: {cancel_button_bg};
    border: 1px solid {cancel_button_border};
  }}
  QPushButton[type="cancel"]:hover {{
    background-color: {cancel_button_hover};
  }}
  #copyAddrButton, #copyEthButton {{
    background-color: {button_copy_address_bg};
    border: none;
    padding: 2px;
    margin: 2px;
    margin-left: 2px;
    margin-right: 2px;
    icon-size: 20px;
    min-width: 28px;
    min-height: 28px;
  }}
  #copyAddrButton:hover, #copyEthButton:hover {{
    background-color: rgba(128, 128, 128, 0.2);
    border-radius: 4px;
  }}
  #startNodeButton {{
    min-height: 40px;
  }}
  #addNodeButton {{
    background-color: {add_node_button_bg};
    color: {text_color};
    border: 1px solid {add_node_button_border};
    padding: 5px 10px;
    border-radius: {border_radius};
    min-height: 32px;
    max-height: 32px;
  }}
  #addNodeButton:hover {{
    background-color: {add_node_button_hover};
    color: {add_node_button_hover_text};
  }}
  #toggleContainerButton {{
    min-height: 40px;
    max-height: 40px;
  }}
  #infoBox {{
    background-color: {info_box_bg};
    border: 1px solid {info_box_border};
    border-radius: {border_radius};
    margin: 6px;
    margin-left: 5px;
    margin-right: 5px;
    padding: 8px;
    color: {info_box_text};
  }}
  #infoBox QLabel {{
    color: {info_box_text};
    font-family: "Courier New";
    font-size: 10pt;
    font-weight: {info_box_font_weight};
    margin: 2px;
    background-color: transparent;
  }}
  #infoBox QPushButton {{
    background-color: {button_copy_address_bg};
    border: none;
    padding: 0px;
    margin: 0px;
    margin-left: 0px;
    margin-right: 0px;
    color: {text_color};
  }}
  #infoBoxText QLabel {{
    color: {info_box_text};
    background-color: transparent;
    font-weight: {info_box_font_weight};
  }}
  #myComboPopup {{
    background-color: #2e2e2e; 
    border: none; 
}}

"""

# Additional custom styles
ADDITIONAL_STYLES = """
  /* No additional styles needed anymore since we've set margins directly on layouts */
"""

# Apply the common template with dark theme values
DARK_STYLESHEET = COMMON_STYLESHEET_TEMPLATE.format(**DARK_THEME) + ADDITIONAL_STYLES + """
  QDialog QLabel {
    color: white;
  }
"""

# Apply the common template with light theme values, with additional light-specific styles
LIGHT_STYLESHEET = COMMON_STYLESHEET_TEMPLATE.format(**LIGHT_THEME) + ADDITIONAL_STYLES + """
  QDialog QLabel {
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

# Add specific button selectors with 5px left and right margins
#addNodeButton, #toggleContainerButton, #launchDAppButton, #explorerButton, #renameButton, #themeToggleButton {{
#    margin-left: 5px;
#    margin-right: 5px;
#}}
#
#infoBox {{
#    margin-left: 5px;
#    margin-right: 5px;
#}}

