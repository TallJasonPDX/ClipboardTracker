"""
Clipboard History Manager
Main entry point for the application
Cross-platform implementation
"""
import sys
import os
import platform
import signal
import time

# Set platform plugin for headless environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Import Qt components
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer

# Import application modules
from clipboard_monitor import ClipboardMonitor
from storage_manager import StorageManager
from ui.system_tray import SystemTrayIcon

def print_startup_message():
    """Print a welcome message in the console"""
    print("=" * 50)
    print("Clipboard History Manager")
    print("Cross-platform clipboard history tracking application")
    print("=" * 50)
    print("Application is running in headless mode.")
    print("The clipboard history is being recorded.")
    print("\nPress Ctrl+C to exit")
    print("=" * 50)

def handle_interrupt(signum, frame):
    """Handle interrupt signal (Ctrl+C)"""
    print("\nClipboard Manager shutting down...")
    QApplication.quit()
    sys.exit(0)

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
    
    # Print startup message
    print_startup_message()
    
    # Set up signal handling for Ctrl+C
    signal.signal(signal.SIGINT, handle_interrupt)
    
    # Check if we're in a headless environment
    is_headless = os.environ.get("QT_QPA_PLATFORM") == "offscreen"
    
    if is_headless:
        # In headless mode, we don't show the system tray, 
        # just start monitoring and notify in console
        clipboard_monitor.start_monitoring()
        
        # Set up clipboard change handler for console output
        def on_clipboard_change(item):
            item_type = item.get('type', 'unknown')
            if item_type == 'text':
                content = item.get('content', '')
                if len(content) > 50:
                    content = content[:47] + "..."
                print(f"\nClipboard changed: Text copied - '{content}'")
            elif item_type == 'image':
                dimensions = f"{item.get('width', 0)}x{item.get('height', 0)}"
                print(f"\nClipboard changed: Image copied - {dimensions}")
            else:
                print(f"\nClipboard changed: Unknown content copied")
        
        # Connect signal
        clipboard_monitor.clipboard_changed.connect(on_clipboard_change)
        
        # Print history stats
        history = storage_manager.get_history()
        print(f"Loaded {len(history)} items from clipboard history.")
    else:
        # In normal mode, create the system tray icon
        icon = QIcon("assets/app_icon.svg")
        tray_icon = SystemTrayIcon(icon, clipboard_monitor, storage_manager)
        tray_icon.show()
        clipboard_monitor.start_monitoring()
    
    # Start the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
