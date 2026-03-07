"""
Shared LogWindow for displaying signal logs in manual tests

Provides a reusable window component for visual debugging of Qt signals
and other test output across the testing suite.
"""
# from datetime import datetime

from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel, QTextEdit


class LogWindow(QWidget):
    """Separate window to display signal logs and test output"""
    
    # Standard color list for source names
    SOURCE_COLORS = [
        "#0066CC",  # Blue
        "#CC0000",  # Red  
        "#FF8800",  # Orange
        "#00AA00",  # Green
        "#8800CC",  # Purple
        "#CC6600",  # Brown
        "#006666",  # Teal
        "#CC0066",  # Pink
    ]
    
    def __init__(self, title: str = "Signal Logs", width: int = 400, height: int = 300):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(850, 200, width, height)
        
        # Track sources for color assignment
        self.source_colors = {}
        self.next_color_index = 0
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Log Output:")
        layout.addWidget(header)
        
        # Text area for logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
        
    def add_log(self, message: str, source: str = None):
        """
        Add a log message with optional colored source name
        
        Args:
            message: The log message to display
            source: Optional source name like 'File Panel' or 'File Presenter'
        """
        if source:
            # Get or assign color for this source
            if source not in self.source_colors:
                color = self.SOURCE_COLORS[self.next_color_index % len(self.SOURCE_COLORS)]
                self.source_colors[source] = color
                self.next_color_index += 1
            
            source_color = self.source_colors[source]
            formatted_message = f'<span style="color: {source_color}; font-weight: bold;">[{source}]</span> {message}'
        else:
            # Default test label with no explicit color (uses default text color)
            formatted_message = f'[Test] {message}'
        
        log_entry = formatted_message
        
        self.log_text.append(log_entry)
        
    def clear_logs(self):
        """Clear all log messages"""
        self.log_text.clear()
