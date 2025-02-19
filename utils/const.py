from ver import __VER__

FULL_DEBUG = True


HOME_SUBFOLDER = ".naeural_launcher"

# Docker
DOCKER_VOLUME = 'naeural_vol'
DOCKER_IMAGE = 'naeural/edge_node'
DOCKER_TAG = 'develop'
DOCKER_CONTAINER_NAME = 'edge_node_container'

# Files names
E2_PEM_FILE = 'e2.pem'

# titles, buttons, labels, captions
WINDOW_TITLE = f'Edge Node Manager v{__VER__}'
EDIT_ENV_BUTTON_TEXT = 'Edit Startup Environment'
EDIT_AUTHORIZED_ADDRS = 'Edit Authorized Addresses'
VIEW_CONFIGS_BUTTON_TEXT = 'View Configs'
LAUNCH_CONTAINER_BUTTON_TEXT = 'Launch Edge Node'
STOP_CONTAINER_BUTTON_TEXT = 'Stop Edge Node'
DAPP_BUTTON_TEXT = 'Launch dApp'
EXPLORER_BUTTON_TEXT = 'Ratio1 Explorer'
DELETE_AND_RESTART_BUTTON_TEXT = 'Reset Node Address'
LOCAL_NODE_ADDRESS_LABEL_TEXT = 'Local Node Address'
REFRESH_LOCAL_ADDRESS_BUTTON_TEXT = 'Refresh Local Address'
COPY_ADDRESS_BUTTON_TEXT = 'Copy Address'
COPY_ETHEREUM_ADDRESS_BUTTON_TEXT = 'Copy Ethereum Address'
RENAME_NODE_BUTTON_TEXT = 'Change Node Alias'
LIGHT_DASHBOARD_BUTTON_TEXT = 'Switch to Light Theme'

UPTIME_LABEL = 'Up Time:'
EPOCH_LABEL = 'Epoch:'
EPOCH_AVAIL_LABEL = 'Epochs avail:'

REFRESH_TIME = 20_000
MAX_HISTORY_QUEUE = 5 * 60 // 10 # 5 minutes @ 10 seconds each hb

AUTO_UPDATE_CHECK_INTERVAL = 60

# Notification messages
NOTIFICATION_TITLE_STRINGS_ENUM = {
    'success': 'Success',
    'error': 'Error',
    'warning': 'Warning',
    'info': 'Information'
}

NOTIFICATION_ADDRESS_COPIED = "Address {address} copied to clipboard"
NOTIFICATION_ADDRESS_COPY_FAILED = "No address available to copy. Try again after launching the Edge Node."

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

DARK_STYLESHEET = """
  QPushButton {
    background-color: #1E90FF; 
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
"""

LIGHT_STYLESHEET = """
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

  PlotWidget .plotLabel {
    color: black;
  }
"""

# Environment settings
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

# Maximum length for aliases (node name and authorized addresses)
MAX_ALIAS_LENGTH = 15

