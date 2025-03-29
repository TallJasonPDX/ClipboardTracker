"""
Clipboard History Manager
Main entry point for the application
"""
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from clipboard_monitor import ClipboardMonitor
from storage_manager import StorageManager
from ui.system_tray import SystemTrayIcon

def main():
    # Enable High DPI display
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
    # Create the application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Allow app to run in background
    app.setApplicationName("Clipboard History Manager")
    
    # Create storage manager
    storage_manager = StorageManager()
    
    # Initialize clipboard monitor
    clipboard_monitor = ClipboardMonitor(storage_manager)
    clipboard_monitor.start_monitoring()
    
    # Create and show the system tray icon
    icon = QIcon("assets/app_icon.svg")
    tray_icon = SystemTrayIcon(icon, clipboard_monitor, storage_manager)
    tray_icon.show()
    
    # Start the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
