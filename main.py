import sys
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables should be done before any other in-app imports
# in order to access env variables in the app.
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

from PyQt5.QtWidgets import QApplication
from app_forms.frm_main import EdgeNodeLauncher

# Set the working directory to the location of the executable
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
  app = QApplication(sys.argv)
  manager = EdgeNodeLauncher()
  manager.show()
  sys.exit(app.exec_())

