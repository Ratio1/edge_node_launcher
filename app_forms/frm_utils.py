import sys
import base64
import traceback
from datetime import datetime
import random
import subprocess
import math

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QAbstractButton, QCheckBox, QRadioButton, QLabel
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QTimer, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QColor, QBrush, QPen
from pyqtgraph import AxisItem

# List of adjectives and nouns for generating container names
ADJECTIVES = [
    "swift", "bright", "calm", "wise", "bold", 
    "quick", "keen", "brave", "agile", "noble"
]

NOUNS = [
    "falcon", "tiger", "eagle", "wolf", "bear",
    "hawk", "lion", "puma", "lynx", "fox"
]

def generate_container_name(prefix="r1node"):
    """Generate a sequential container name.
    
    First container is named just "r1node" (no number),
    subsequent containers are "r1node1", "r1node2", etc.
    """
    # Get list of existing containers with the prefix
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', '{{.Names}}', '--filter', f'name={prefix}'],
            capture_output=True, text=True
        )
        
        # Parse existing container names and find the highest index
        existing_containers = result.stdout.strip().split('\n')
        existing_containers = [c for c in existing_containers if c]  # Remove empty strings
        
        highest_index = -1  # Start from -1 so first container will be r1node0
        for container in existing_containers:
            if container.startswith(prefix):
                try:
                    # Extract the number after the prefix
                    index_str = container[len(prefix):]
                    if index_str.isdigit():
                        index = int(index_str)
                        highest_index = max(highest_index, index)
                except (ValueError, IndexError):
                    continue
        
        # Return next available index
        return f"{prefix}{highest_index + 1}"
        
    except Exception as e:
        # In case of any error, start from 0
        return f"{prefix}0"

def get_volume_name(container_name):
    """Get volume name from container name"""
    # For legacy container names
    if "edge_node_container" in container_name:
        return container_name.replace("container", "volume")
    
    # For new r1node naming convention
    if container_name == "r1node":
        return "r1vol"  # First container gets simple volume name
    
    # For r1node with sequential numbers
    if container_name.startswith("r1node"):
        # Extract the number part
        try:
            # Get the numeric part after "r1node"
            number_part = container_name[6:]
            if number_part.isdigit():
                return f"r1vol{number_part}"
        except (ValueError, IndexError):
            pass
    
    # Fallback
    return f"volume_{container_name}"

def get_icon_from_base64(base64_str):
  icon_data = base64.b64decode(base64_str)
  pixmap = QPixmap()
  pixmap.loadFromData(icon_data)
  return QIcon(pixmap)

class DateAxisItem_OLD(AxisItem):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.setLabel(text='Time')
    return

  def tickStrings(self, values, scale, spacing):
    ticks = [datetime.fromtimestamp(value).strftime("%H:%M:%S") for value in values]      
    return ticks


class DateAxisItem(AxisItem):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.setLabel(text='Time')  # Custom label without scientific notation
    self.timestamps = None  # Store actual timestamps from the data
    self.parent = None  # Store the parent widget for debugging
    return

  def setTimestamps(self, timestamps, parent):
    """Store the actual timestamps from the data to map axis values."""
    self.parent = parent
    if isinstance(timestamps[0], str):
      self.timestamps = [datetime.fromisoformat(ts).timestamp() for ts in timestamps]
    else:
      self.timestamps = timestamps
    return

  def tickStrings(self, values, scale, spacing):
    if not self.timestamps or len(self.timestamps) == 0:
      return [""] * len(values)  # Return empty labels if no timestamps available

    # Get the range of actual timestamps
    start_time = self.timestamps[0]
    end_time = self.timestamps[-1]
    time_range = end_time - start_time

    # Map the axis values to actual timestamps
    ticks = []
    for value in values:
      try:
        # Scale the value if it's in the range of the timestamp indices
        if start_time <= value <= end_time:
          ticks.append(datetime.fromtimestamp(value).strftime("%H:%M:%S"))
        else:
          ticks.append("")  # Ignore out-of-range values
      except Exception as e:
        ticks.append("")  # Handle exceptions gracefully    
    # print(f"Ticks for {self.parent}: {ticks}")
    return ticks

  
      
class ToggleButton1(QAbstractButton):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setCheckable(True)
    self._background_color = QColor(255, 0, 0)
    self._circle_color = QColor(255, 255, 255)
    self._circle_position = 3  # Start position

    self.anim = QPropertyAnimation(self, b"circle_position", self)
    self.anim.setDuration(200)
    self.anim.finished.connect(self.update)  # Ensure we update after animation

    self.setFixedSize(50, 25)

  def paintEvent(self, event):
    rect = self.rect()
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw background
    painter.setBrush(QBrush(self._background_color))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(0, 0, rect.width(), rect.height(), rect.height() // 2, rect.height() // 2)
    
    # Draw circle - position based on checked state if not animating
    if not self.anim.state():
      self._circle_position = self.width() - self.height() + 3 if self.isChecked() else 3
    
    # Draw the circle
    painter.setBrush(QBrush(self._circle_color))
    painter.drawEllipse(self._circle_position, 3, rect.height() - 6, rect.height() - 6)

  def mouseReleaseEvent(self, event):
    if self.rect().contains(event.pos()):
      checked = not self.isChecked()
      self.setChecked(checked)
      
      # Animate the circle
      start_pos = self._circle_position
      end_pos = self.width() - self.height() + 3 if checked else 3
      
      self.anim.setStartValue(start_pos)
      self.anim.setEndValue(end_pos)
      self.anim.start()

  def setBackgroundColor(self, color):
    self._background_color = QColor(color)
    self.update()

  def setCircleColor(self, color):
    self._circle_color = QColor(color)
    self.update()

  def get_circle_position(self):
    return self._circle_position

  def set_circle_position(self, pos):
    self._circle_position = pos
    self.update()

  circle_position = property(get_circle_position, set_circle_position)

class LoadingIndicator(QLabel):
    def __init__(self, parent=None, size=40):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(QSize(size, size))
        self._size = size
        self._color = QColor("#4CAF50")  # Default green color
        
    def start(self):
        """Start the loading animation."""
        self.show()
        self.timer.start(50)  # Update every 50ms
        
    def stop(self):
        """Stop the loading animation."""
        self.timer.stop()
        self.hide()
        
    def rotate(self):
        """Rotate the spinner by 30 degrees."""
        self.angle = (self.angle + 30) % 360
        self.update()
        
    def setColor(self, color):
        """Set the color of the spinner."""
        self._color = QColor(color)
        self.update()
        
    def paintEvent(self, event):
        """Paint the spinning indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate center and radius
        center = self.rect().center()
        radius = (min(self.width(), self.height()) - 4) / 2
        
        # Set up the pen for drawing
        pen = QPen(self._color)
        pen.setWidth(3)
        painter.setPen(pen)
        
        # Draw 8 lines with varying opacity
        for i in range(8):
            # Calculate opacity based on position
            opacity = 1.0 - (i * 0.1)
            self._color.setAlphaF(opacity)
            pen.setColor(self._color)
            painter.setPen(pen)
            
            # Calculate line position
            angle_rad = math.radians(self.angle + (i * 45))
            start_x = center.x() + (radius * 0.5 * math.cos(angle_rad))
            start_y = center.y() + (radius * 0.5 * math.sin(angle_rad))
            end_x = center.x() + (radius * math.cos(angle_rad))
            end_y = center.y() + (radius * math.sin(angle_rad))
            
            # Draw the line
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

