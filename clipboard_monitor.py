"""
Clipboard Monitor Module
Monitors the system clipboard for changes and captures content with source information
Cross-platform implementation
"""
import time
import io
import platform
import psutil
import os
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QBuffer, QByteArray
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
        try:
            clipboard_item = self.get_clipboard_content()
            
            # Skip processing if clipboard_item is None
            if clipboard_item is None:
                return
                
            # Add a processing lock to prevent duplicate events
            if hasattr(self, '_processing'):
                return
            self._processing = True
            
            try:
                # Check if content actually changed
                if self.content_changed(clipboard_item):
                    self.last_content = clipboard_item.copy()  # Make a copy to prevent reference issues
                    
                    # Add source information
                    clipboard_item['source'] = self.source_tracker.get_source_info()
                    clipboard_item['timestamp'] = time.time()
                    
                    # Save to storage
                    self.storage_manager.add_clipboard_item(clipboard_item)
                    
                    # Immediately save history to disk
                    try:
                        self.storage_manager.save_history()
                    except Exception as e:
                        print(f"Error saving clipboard history: {e}")
                    
                    # Emit signal
                    self.clipboard_changed.emit(clipboard_item)
            finally:
                delattr(self, '_processing')
        except Exception as e:
            print(f"Error processing clipboard: {e}")
            if hasattr(self, '_processing'):
                delattr(self, '_processing')
    
    def get_clipboard_content(self):
        """Capture the current clipboard content"""
        try:
            mime_data = self.clipboard.mimeData()
            if mime_data is None:
                print("Warning: Could not access clipboard content (mime_data is None)")
                return None
                
            clipboard_item = {"type": "unknown", "content": None}
            
            # Check for text content
            if mime_data.hasText():
                text = mime_data.text()
                if text:
                    # Check if the text is actually a base64 image
                    if text.startswith('data:image/'):
                        try:
                            # Extract the base64 data after the comma
                            import base64
                            header, b64data = text.split(',', 1)
                            image_data = base64.b64decode(b64data)
                            
                            # Create QImage from the decoded data
                            image = QImage()
                            image.loadFromData(image_data)
                            
                            if not image.isNull():
                                # Use QBuffer to save image data
                                byte_array = QByteArray()
                                buffer = QBuffer(byte_array)
                                buffer.open(QBuffer.WriteOnly)
                                image.save(buffer, "PNG")
                                buffer.close()
                                
                                clipboard_item["type"] = "image"
                                clipboard_item["content"] = bytes(byte_array.data())
                                clipboard_item["width"] = image.width()
                                clipboard_item["height"] = image.height()
                            else:
                                clipboard_item["type"] = "text"
                                clipboard_item["content"] = text
                        except Exception as e:
                            print(f"Error processing base64 image: {e}")
                            # If any error occurs during base64 processing, treat as text
                            clipboard_item["type"] = "text"
                            clipboard_item["content"] = text
                    else:
                        clipboard_item["type"] = "text"
                        clipboard_item["content"] = text
            
            # Check for image content if we haven't already found a base64 image
            elif mime_data.hasImage():
                image = QImage(mime_data.imageData())
                if not image.isNull():
                    # Use QBuffer to save image data
                    byte_array = QByteArray()
                    buffer = QBuffer(byte_array)
                    buffer.open(QBuffer.WriteOnly)
                    image.save(buffer, "PNG")
                    buffer.close()
                    
                    clipboard_item["type"] = "image"
                    clipboard_item["content"] = bytes(byte_array.data())
                    clipboard_item["width"] = image.width()
                    clipboard_item["height"] = image.height()
                    
            # Return None if no valid content
            if clipboard_item["content"] is None:
                return None
                
            return clipboard_item
        except Exception as e:
            print(f"Error accessing clipboard: {e}")
            return None
    
    def content_changed(self, clipboard_item):
        """Check if the clipboard content has changed"""
        try:
            # If there's no previous content, then it has changed
            if self.last_content is None:
                return True
                
            # Make sure the clipboard_item has all required fields
            if not isinstance(clipboard_item, dict) or "type" not in clipboard_item or "content" not in clipboard_item:
                return True
                
            # If types are different, content has changed
            if clipboard_item["type"] != self.last_content["type"]:
                return True
                
            # Compare based on content type
            if clipboard_item["type"] == "text":
                return clipboard_item["content"] != self.last_content["content"]
            elif clipboard_item["type"] == "image":
                # For images, compare the raw image data bytes
                current_bytes = bytes(clipboard_item["content"])
                last_bytes = bytes(self.last_content["content"])
                return current_bytes != last_bytes
                
            # Default: assume it changed
            return True
            
        except Exception as e:
            print(f"Error comparing clipboard content: {e}")
            return True  # Assume it changed when there's an error
    
    def copy_to_clipboard(self, clipboard_item):
        """Copy an item from history back to clipboard"""
        try:
            if not clipboard_item or not isinstance(clipboard_item, dict):
                print("Cannot copy: Invalid clipboard item")
                return False
                
            if "type" not in clipboard_item or "content" not in clipboard_item:
                print("Cannot copy: Missing required fields in clipboard item")
                return False
                
            clipboard = QGuiApplication.clipboard()
            
            if clipboard_item["type"] == "text":
                clipboard.setText(clipboard_item["content"])
                return True
            elif clipboard_item["type"] == "image":
                try:
                    # Get image path from the storage manager's images directory
                    image_path = os.path.join(self.storage_manager.images_dir, clipboard_item["content"])
                    if not os.path.exists(image_path):
                        print("Image file not found")
                        return False
                        
                    # Load image from file
                    image = QImage(image_path)
                    if image.isNull():
                        print("Failed to load image")
                        return False
                        
                    clipboard.setImage(image)
                    return True
                except Exception as e:
                    print(f"Error copying image to clipboard: {e}")
                    return False
            else:
                print(f"Unsupported clipboard item type: {clipboard_item['type']}")
                return False
                
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return False
