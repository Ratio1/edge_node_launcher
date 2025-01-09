import sys
import os
from PyQt5.QtWidgets import QApplication
from app_forms.frm_main import EdgeNodeLauncher

# Set the working directory to the location of the executable
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
  app = QApplication(sys.argv)
  manager = EdgeNodeLauncher()
  manager.show()
  sys.exit(app.exec_())

