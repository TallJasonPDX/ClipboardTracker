"""
Main Window Module
Implements the main application window
"""
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QLineEdit, QTabWidget,
                            QSplitter, QApplication, QShortcut, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QKeySequence

from ui.history_widget import HistoryWidget
from ui.search_widget import SearchWidget

class MainWindow(QMainWindow):
    """Main application window with clipboard history and search"""
    
    def __init__(self, clipboard_monitor, storage_manager):
        super().__init__()
        
        self.clipboard_monitor = clipboard_monitor
        self.storage_manager = storage_manager
        
        self.init_ui()
        self.setup_shortcuts()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Clipboard History Manager")
        self.setMinimumSize(300, 400)  # Reduced minimum width to 300px
        
        # Main widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins for smaller screens
        
        # Create search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clipboard history...")
        self.search_input.textChanged.connect(self.search_history)
        
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.confirm_clear_history)
        clear_button.setMaximumWidth(60)  # Make clear button smaller
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(clear_button)
        
        # Add search layout to main layout
        main_layout.addLayout(search_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)  # Modern tab style
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTabBar::tab {
                padding: 6px 12px;
                margin: 2px;
            }
            @media (max-width: 400px) {
                QTabBar::tab {
                    padding: 4px 8px;
                    margin: 1px;
                }
            }
        """)
        
        # All items tab
        self.history_widget = HistoryWidget(self.clipboard_monitor, self.storage_manager)
        self.tab_widget.addTab(self.history_widget, "All Items")
        
        # Text only tab
        self.text_widget = HistoryWidget(self.clipboard_monitor, self.storage_manager, filter_type="text")
        self.tab_widget.addTab(self.text_widget, "Text")
        
        # Images only tab
        self.image_widget = HistoryWidget(self.clipboard_monitor, self.storage_manager, filter_type="image")
        self.tab_widget.addTab(self.image_widget, "Images")
        
        # Pinned items tab (moved to last position)
        self.pinned_widget = HistoryWidget(self.clipboard_monitor, self.storage_manager)
        self.pinned_widget.pinned_only = True  # Add this flag to identify pinned tab
        self.tab_widget.addTab(self.pinned_widget, "Pinned")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Status bar with responsive font size
        self.statusBar().setStyleSheet("""
            QStatusBar {
                font-size: 12px;
            }
            @media (max-width: 400px) {
                QStatusBar {
                    font-size: 10px;
                }
            }
        """)
        self.statusBar().showMessage("Ready")
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Connect clipboard changed signal
        self.clipboard_monitor.clipboard_changed.connect(self.on_clipboard_changed)
        
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        # Search shortcut (Ctrl+F)
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(lambda: self.search_input.setFocus())
        
        # Refresh shortcut (F5)
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.refresh_history)
    
    def search_history(self):
        """Search through clipboard history"""
        search_text = self.search_input.text()
        
        # Update all tabs with search results
        self.pinned_widget.update_history(search=search_text)
        self.history_widget.update_history(search=search_text)
        self.text_widget.update_history(search=search_text)
        self.image_widget.update_history(search=search_text)
    
    def refresh_history(self):
        """Refresh the clipboard history display"""
        self.pinned_widget.update_history()
        self.history_widget.update_history()
        self.text_widget.update_history()
        self.image_widget.update_history()
        self.statusBar().showMessage("History refreshed", 3000)
    
    def on_clipboard_changed(self, item):
        """Handle clipboard content changes"""
        # Update the history widgets
        self.pinned_widget.update_history()
        self.history_widget.update_history()
        
        if item['type'] == 'text':
            self.text_widget.update_history()
        elif item['type'] == 'image':
            self.image_widget.update_history()
        
        # Update status bar
        source = item.get('source', {}).get('application', {}).get('name', 'Unknown')
        self.statusBar().showMessage(f"Copied {item['type']} from {source}", 3000)
    
    def confirm_clear_history(self):
        """Show confirmation dialog before clearing history"""
        confirm = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all clipboard history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.storage_manager.clear_history()
            self.refresh_history()
            self.statusBar().showMessage("Clipboard history cleared", 3000)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Hide the window instead of closing the application
        event.ignore()
        self.hide()
