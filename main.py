import sys
import os
from PyQt5.QtWidgets import QApplication
from app_forms.frm_main import EdgeNodeLauncher
from dotenv import load_dotenv
from pathlib import Path

# Set the working directory to the location of the executable
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

def load_env():
    """Load environment variables from the .env file."""
    dotenv_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=dotenv_path)


if __name__ == '__main__':
  app = QApplication(sys.argv)
  manager = EdgeNodeLauncher()
  manager.show()
  sys.exit(app.exec_())

