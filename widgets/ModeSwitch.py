from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from app_forms.frm_utils import ToggleButton1

class ModeSwitch(QWidget):
    mode_changed = pyqtSignal(bool)  # True for pro mode, False for simple mode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Simple mode label
        self.simple_label = QLabel("Simple")
        self.simple_label.setFont(QFont("Courier New", 10))
        layout.addWidget(self.simple_label)

        # Toggle button
        self.toggle = ToggleButton1()
        # Default colors for light theme
        self.toggle.setBackgroundColor("#cccccc")  # Gray when off
        self.toggle.setCircleColor("#ffffff")  # White circle
        self.toggle.toggled.connect(self._on_toggle)
        layout.addWidget(self.toggle)

        # Pro mode label
        self.pro_label = QLabel("Pro")
        self.pro_label.setFont(QFont("Courier New", 10))
        layout.addWidget(self.pro_label)

        layout.addStretch()
        self.setLayout(layout)
        self._update_labels()

    def _on_toggle(self, checked):
        # Emit signal first so UI can update before visual changes
        self.mode_changed.emit(checked)
        self._update_labels()

    def _update_labels(self):
        is_pro = self.toggle.isChecked()
        # Colors will be updated properly in apply_stylesheet
        self.toggle.setBackgroundColor("#4CAF50" if is_pro else "#cccccc")  # Green when on, gray when off

    def is_pro_mode(self):
        return self.toggle.isChecked()

    def set_pro_mode(self, enabled):
        if self.toggle.isChecked() != enabled:
            self.toggle.setChecked(enabled)
            self._update_labels()

    def apply_stylesheet(self, is_dark_theme):
        """Apply the appropriate stylesheet based on the theme"""
        # Text colors
        light_color = "#FFFFFF" if is_dark_theme else "#000000"
        dim_color = "#999999" if is_dark_theme else "#666666"
        
        is_pro = self.toggle.isChecked()
        
        # Update text colors
        self.simple_label.setStyleSheet(f"color: {dim_color if is_pro else light_color};")
        self.pro_label.setStyleSheet(f"color: {light_color if is_pro else dim_color};")
        
        # Update toggle colors
        if is_dark_theme:
            self.toggle.setBackgroundColor("#4CAF50" if is_pro else "#555555")  # Green when on, dark gray when off
            self.toggle.setCircleColor("#FFFFFF")  # White circle
        else:
            self.toggle.setBackgroundColor("#4CAF50" if is_pro else "#cccccc")  # Green when on, light gray when off
            self.toggle.setCircleColor("#FFFFFF")  # White circle 