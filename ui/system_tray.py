"""
System Tray Module
Implements the system tray icon and menu for the application
"""
from PyQt5.QtWidgets import (QSystemTrayIcon, QMenu, QAction, 
                           QApplication, QStyle, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

from ui.main_window import MainWindow

class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon with menu for the clipboard manager"""
    
    def __init__(self, icon, clipboard_monitor, storage_manager, parent=None):
        super().__init__(icon, parent)
        
        self.clipboard_monitor = clipboard_monitor
        self.storage_manager = storage_manager
        
        # Create main window
        self.main_window = MainWindow(clipboard_monitor, storage_manager)
        
        self.init_menu()
        self.set_connections()
    
    def init_menu(self):
        """Initialize the tray icon menu"""
        menu = QMenu()
        
        # Open main window action
        self.show_action = QAction("Show Clipboard History", self)
        self.show_action.triggered.connect(self.show_main_window)
        menu.addAction(self.show_action)
        
        # Toggle monitoring
        self.toggle_monitoring_action = QAction("Pause Monitoring", self)
        self.toggle_monitoring_action.triggered.connect(self.toggle_monitoring)
        menu.addAction(self.toggle_monitoring_action)
        
        # Clear history action
        clear_action = QAction("Clear History", self)
        clear_action.triggered.connect(self.clear_history)
        menu.addAction(clear_action)
        
        menu.addSeparator()
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        
        # Set the menu
        self.setContextMenu(menu)
    
    def set_connections(self):
        """Set up signal connections"""
        # Connect activated signal (icon click)
        self.activated.connect(self.on_tray_icon_activated)
        
        # Connect clipboard changed signal
        self.clipboard_monitor.clipboard_changed.connect(self.on_clipboard_changed)
    
    def show_main_window(self):
        """Show the main application window"""
        # Show, raise and activate window
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        # If window is minimized, restore it
        if self.main_window.isMinimized():
            self.main_window.setWindowState(self.main_window.windowState() & ~Qt.WindowMinimized)
    
    def toggle_monitoring(self):
        """Toggle clipboard monitoring on/off"""
        if self.toggle_monitoring_action.text() == "Pause Monitoring":
            self.clipboard_monitor.stop_monitoring()
            self.toggle_monitoring_action.setText("Resume Monitoring")
            self.showMessage("Clipboard Manager", "Clipboard monitoring paused")
        else:
            self.clipboard_monitor.start_monitoring()
            self.toggle_monitoring_action.setText("Pause Monitoring")
            self.showMessage("Clipboard Manager", "Clipboard monitoring resumed")
    
    def clear_history(self):
        """Clear clipboard history"""
        self.storage_manager.clear_history()
        if self.main_window.isVisible():
            self.main_window.refresh_history()
        self.showMessage("Clipboard Manager", "Clipboard history cleared")
    
    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger or reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()
    
    def on_clipboard_changed(self, item):
        """Handle clipboard content changes"""
        # Get source information
        source = "Unknown source"
        url = ""
        if 'source' in item:
            app_info = item['source'].get('application', {})
            app_name = app_info.get('name', 'Unknown')
            
            if app_info.get('type') == 'browser':
                website_info = item['source'].get('website', {})
                url = website_info.get('url', '')
                domain = website_info.get('domain', '')
                title = website_info.get('title', '')
                
                if url:
                    source = f"{title}\n{url}"
                elif domain:
                    source = f"{domain} ({app_info.get('browser', app_name)})"
                else:
                    source = app_info.get('browser', app_name)
            else:
                window_title = app_info.get('window_title', '')
                if window_title:
                    source = f"{window_title} ({app_name})"
                else:
                    source = app_name
        
        # Show notification for new content
        title = "New Clipboard Content"
        if item['type'] == 'text':
            # Truncate text for notification
            text = item['content']
            if len(text) > 50:
                text = text[:47] + "..."
            message = f"Text: {text}\nFrom: {source}"
        elif item['type'] == 'image':
            message = f"Image copied\nFrom: {source}"
        else:
            message = f"Unknown content copied\nFrom: {source}"
        
        # Use system tray notification
        self.showMessage(title, message, QSystemTrayIcon.Information, 3000)
    
    def show_about(self):
        """Show about information"""
        title = "About Clipboard History Manager"
        message = """
        Clipboard History Manager
        
        A Windows clipboard history manager that
        tracks and stores copied content along
        with its source application or website.
        
        Version 1.0
        """
        
        self.showMessage(title, message, QSystemTrayIcon.Information, 5000)
