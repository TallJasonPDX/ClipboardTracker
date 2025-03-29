"""
Search Widget Module
Implements the search functionality for clipboard history
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal

class SearchWidget(QWidget):
    """Widget for searching through clipboard history"""
    
    search_requested = pyqtSignal(str, str)  # search text, filter type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Search label
        search_label = QLabel("Search:")
        layout.addWidget(search_label)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clipboard history...")
        self.search_input.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_input, 1)  # 1 is the stretch factor
        
        # Filter dropdown
        filter_label = QLabel("Filter:")
        layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All", "")
        self.filter_combo.addItem("Text Only", "text")
        self.filter_combo.addItem("Images Only", "image")
        self.filter_combo.currentIndexChanged.connect(self.perform_search)
        layout.addWidget(self.filter_combo)
        
        # Search button
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.perform_search)
        layout.addWidget(search_button)
        
        # Clear button
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_search)
        layout.addWidget(clear_button)
    
    def perform_search(self):
        """Execute the search"""
        search_text = self.search_input.text()
        filter_type = self.filter_combo.currentData()
        
        self.search_requested.emit(search_text, filter_type)
    
    def clear_search(self):
        """Clear the search input and reset results"""
        self.search_input.clear()
        self.filter_combo.setCurrentIndex(0)
        self.perform_search()
    
    def set_search_text(self, text):
        """Set the search text programmatically"""
        self.search_input.setText(text)
        self.perform_search()
