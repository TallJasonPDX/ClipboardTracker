"""
Clipboard Monitor Module
Monitors the system clipboard for changes and captures content with source information
Cross-platform implementation
"""
import time
import io
import platform
import psutil
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtGui import QGuiApplication, QImage
from source_tracker import SourceTracker

class ClipboardMonitor(QObject):
    """
    Monitors the clipboard for changes and captures the content
    along with source information
    """
    clipboard_changed = pyqtSignal(dict)
    
    def __init__(self, storage_manager):
        super().__init__()
        self.storage_manager = storage_manager
        self.clipboard = QGuiApplication.clipboard()
        self.last_content = None
        self.timer = QTimer(self)
        self.source_tracker = SourceTracker()
        
    def start_monitoring(self):
        """Start the clipboard monitoring process"""
        # Connect to clipboard dataChanged signal
        self.clipboard.dataChanged.connect(self.on_clipboard_change)
        
        # Also set a timer as a fallback mechanism
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(500)  # Check every 500ms
        
    def stop_monitoring(self):
        """Stop the clipboard monitoring process"""
        self.clipboard.dataChanged.disconnect(self.on_clipboard_change)
        self.timer.stop()
        
    def on_clipboard_change(self):
        """Triggered when clipboard content changes"""
        self.process_clipboard()
    
    def check_clipboard(self):
        """Periodically check clipboard as a fallback mechanism"""
        # This helps catch changes that might not trigger dataChanged signal
        self.process_clipboard()
    
    def process_clipboard(self):
        """Process and store the clipboard content"""
        clipboard_item = self.get_clipboard_content()
        
        # Check if content actually changed and is not None
        if clipboard_item and self.content_changed(clipboard_item):
            self.last_content = clipboard_item
            
            # Add source information
            clipboard_item['source'] = self.source_tracker.get_source_info()
            clipboard_item['timestamp'] = time.time()
            
            # Save to storage
            self.storage_manager.add_clipboard_item(clipboard_item)
            
            # Emit signal
            self.clipboard_changed.emit(clipboard_item)
    
    def get_clipboard_content(self):
        """Capture the current clipboard content"""
        mime_data = self.clipboard.mimeData()
        clipboard_item = {"type": "unknown", "content": None}
        
        # Check for text content
        if mime_data.hasText():
            text = mime_data.text()
            if text:
                clipboard_item["type"] = "text"
                clipboard_item["content"] = text
        
        # Check for image content
        elif mime_data.hasImage():
            image = QImage(mime_data.imageData())
            if not image.isNull():
                # Convert QImage to bytes
                buffer = io.BytesIO()
                image.save(buffer, "PNG")
                image_data = buffer.getvalue()
                
                clipboard_item["type"] = "image"
                clipboard_item["content"] = image_data
                clipboard_item["width"] = image.width()
                clipboard_item["height"] = image.height()
                
        # Return None if no valid content
        if clipboard_item["content"] is None:
            return None
            
        return clipboard_item
    
    def content_changed(self, clipboard_item):
        """Check if the clipboard content has changed"""
        if self.last_content is None:
            return True
            
        if clipboard_item["type"] != self.last_content["type"]:
            return True
            
        if clipboard_item["type"] == "text":
            return clipboard_item["content"] != self.last_content["content"]
        elif clipboard_item["type"] == "image":
            # For images, compare the raw image data
            return clipboard_item["content"] != self.last_content["content"]
            
        return True
    
    def copy_to_clipboard(self, clipboard_item):
        """Copy an item from history back to clipboard"""
        clipboard = QGuiApplication.clipboard()
        
        if clipboard_item["type"] == "text":
            clipboard.setText(clipboard_item["content"])
        elif clipboard_item["type"] == "image":
            # Convert bytes to QImage
            image_data = clipboard_item["content"]
            image = QImage()
            image.loadFromData(image_data)
            clipboard.setImage(image)
