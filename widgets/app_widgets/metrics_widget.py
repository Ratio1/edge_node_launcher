from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox
from PyQt5.QtCore import pyqtSignal
import pyqtgraph as pg
from models.NodeHistory import NodeHistory
from datetime import datetime
import numpy as np

class MetricsWidget(QWidget):
    """
    Widget for displaying node metrics charts
    """
    # Signals
    refresh_requested = pyqtSignal()  # Emitted when refresh button is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize UI components
        self.btn_refresh = QPushButton("Refresh Metrics")
        
        # Create plot widgets
        self.plot_cpu = pg.PlotWidget()
        self.plot_memory = pg.PlotWidget()
        self.plot_disk = pg.PlotWidget()
        self.plot_network = pg.PlotWidget()
        
        # Configure plots
        self._configure_plots()
        
        # Setup UI layout
        self.init_ui()
        
        # Connect signals
        self.connect_signals()
    
    def _configure_plots(self):
        """Configure plot widgets appearance and behavior"""
        # Set background to transparent
        for plot in [self.plot_cpu, self.plot_memory, self.plot_disk, self.plot_network]:
            plot.setBackground(None)
            plot.showGrid(x=True, y=True, alpha=0.3)
        
        # Set titles and labels
        self.plot_cpu.setTitle("CPU Usage")
        self.plot_memory.setTitle("Memory Usage")
        self.plot_disk.setTitle("Disk Usage")
        self.plot_network.setTitle("Network Traffic")
        
        # Set Y axis ranges
        self.plot_cpu.setYRange(0, 100)
        self.plot_memory.setYRange(0, 100)
        self.plot_disk.setYRange(0, 100)
        # Network range will be set dynamically
    
    def init_ui(self):
        """Initialize the UI components and layout"""
        # Main layout
        layout = QVBoxLayout()
        
        # Create metrics group box
        metrics_group = QGroupBox("Node Metrics")
        metrics_layout = QVBoxLayout()
        
        # Add plot widgets to layout - organize in a grid
        row1_layout = QHBoxLayout()
        row1_layout.addWidget(self.plot_cpu)
        row1_layout.addWidget(self.plot_memory)
        
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(self.plot_disk)
        row2_layout.addWidget(self.plot_network)
        
        metrics_layout.addLayout(row1_layout)
        metrics_layout.addLayout(row2_layout)
        
        # Set metrics group layout
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Add refresh button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_refresh)
        layout.addLayout(button_layout)
        
        # Set layout
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connect widget signals to slots"""
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
    
    def update_metrics(self, history: NodeHistory = None, limit: int = 100):
        """
        Update the displayed metrics charts
        
        Args:
            history: NodeHistory object containing metrics data
            limit: Maximum number of data points to display
        """
        if not history or not history.cpu or not history.memory or not history.disk or not history.network:
            self._clear_plots()
            return
        
        # Convert timestamps to datetime objects
        try:
            timestamps = [datetime.fromtimestamp(ts) for ts in history.timestamps[-limit:]]
        except (ValueError, TypeError):
            self._clear_plots()
            return
        
        # Get data arrays
        cpu_data = history.cpu[-limit:]
        memory_data = history.memory[-limit:]
        disk_data = history.disk[-limit:]
        network_rx = history.network_rx[-limit:] if history.network_rx else []
        network_tx = history.network_tx[-limit:] if history.network_tx else []
        
        # Clear existing plots
        self._clear_plots()
        
        # Update plots
        self._update_plot(self.plot_cpu, timestamps, cpu_data, "CPU %", "blue")
        self._update_plot(self.plot_memory, timestamps, memory_data, "Memory %", "green")
        self._update_plot(self.plot_disk, timestamps, disk_data, "Disk %", "red")
        
        # Update network plot with both rx and tx
        if network_rx and network_tx:
            dates_as_numbers = [(timestamp - timestamps[0]).total_seconds() for timestamp in timestamps]
            self.plot_network.plot(dates_as_numbers, network_rx, pen="blue", name="RX KB/s")
            self.plot_network.plot(dates_as_numbers, network_tx, pen="red", name="TX KB/s")
            
            # Add legend to network plot
            self.plot_network.addLegend()
    
    def _update_plot(self, plot_widget, timestamps, data, name, color):
        """
        Update a single plot with new data
        
        Args:
            plot_widget: PyQtGraph plot widget to update
            timestamps: List of datetime objects for X axis
            data: List of values for Y axis
            name: Name of the data series
            color: Color to use for the plot line
        """
        if not timestamps or not data or len(timestamps) != len(data):
            return
        
        # Convert timestamps to seconds since first timestamp for X axis
        dates_as_numbers = [(timestamp - timestamps[0]).total_seconds() for timestamp in timestamps]
        
        # Plot the data
        plot_widget.plot(dates_as_numbers, data, pen=color, name=name)
    
    def _clear_plots(self):
        """Clear all plot widgets"""
        self.plot_cpu.clear()
        self.plot_memory.clear()
        self.plot_disk.clear()
        self.plot_network.clear() 