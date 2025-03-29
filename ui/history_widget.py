"""
History Widget Module
Displays the clipboard history with source information
"""
import io
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QScrollArea, QFrame, QSizePolicy,
                           QMenu, QAction, QToolButton)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon, QCursor

class ClipboardItemWidget(QFrame):
    """Widget representing a single clipboard item"""
    
    def __init__(self, item, clipboard_monitor, parent=None):
        super().__init__(parent)
        self.item = item
        self.clipboard_monitor = clipboard_monitor
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI for this clipboard item"""
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        self.setMidLineWidth(0)
        
        # Set mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header with source info and timestamp
        header_layout = QHBoxLayout()
        
        # Source info
        source_info = self.format_source_info()
        source_label = QLabel(source_info)
        source_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        
        # Timestamp
        time_label = QLabel(self.item.get('datetime', ''))
        time_label.setAlignment(Qt.AlignRight)
        time_label.setStyleSheet("color: #666666;")
        
        header_layout.addWidget(source_label)
        header_layout.addWidget(time_label)
        
        # Add header to main layout
        layout.addLayout(header_layout)
        
        # Content depends on item type
        if self.item['type'] == 'text':
            self.add_text_content(layout)
        elif self.item['type'] == 'image':
            self.add_image_content(layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        # Copy button
        copy_button = QPushButton("Copy")
        copy_button.setIcon(QIcon.fromTheme("edit-copy"))
        copy_button.clicked.connect(self.copy_to_clipboard)
        
        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setIcon(QIcon.fromTheme("edit-delete"))
        delete_button.clicked.connect(self.delete_item)
        
        button_layout.addWidget(copy_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def format_source_info(self):
        """Format source information for display"""
        source = self.item.get('source', {})
        app_info = source.get('application', {})
        
        app_name = app_info.get('name', 'Unknown')
        app_type = app_info.get('type', 'unknown')
        
        if app_type == 'browser':
            browser_name = app_info.get('browser', app_name)
            website_info = source.get('website', {})
            domain = website_info.get('domain', '')
            
            if domain:
                return f"Copied from {domain} ({browser_name})"
            else:
                return f"Copied from {browser_name}"
        else:
            window_title = app_info.get('window_title', '')
            if window_title:
                return f"Copied from {window_title} ({app_name})"
            else:
                return f"Copied from {app_name}"
    
    def add_text_content(self, layout):
        """Add text content to the widget"""
        content = self.item.get('content', '')
        
        # Limit displayed text length
        max_display_length = 500
        display_text = content
        
        if len(content) > max_display_length:
            display_text = content[:max_display_length] + "..."
        
        text_label = QLabel(display_text)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_label.setStyleSheet("background-color: #f9f9f9; padding: 8px; border-radius: 4px;")
        
        layout.addWidget(text_label)
    
    def add_image_content(self, layout):
        """Add image content to the widget"""
        image_data = self.item.get('content')
        width = self.item.get('width', 200)
        height = self.item.get('height', 200)
        
        if image_data:
            # Create QImage from binary data
            qimage = QImage()
            qimage.loadFromData(image_data)
            
            # Create pixmap
            pixmap = QPixmap.fromImage(qimage)
            
            # Resize if too large
            max_preview_size = 300
            if pixmap.width() > max_preview_size or pixmap.height() > max_preview_size:
                pixmap = pixmap.scaled(
                    max_preview_size, 
                    max_preview_size, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
            
            # Create image label
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            
            # Add size info
            size_label = QLabel(f"Image: {width}x{height}")
            size_label.setAlignment(Qt.AlignCenter)
            
            layout.addWidget(image_label)
            layout.addWidget(size_label)
    
    def copy_to_clipboard(self):
        """Copy this item back to the clipboard"""
        self.clipboard_monitor.copy_to_clipboard(self.item)
    
    def delete_item(self):
        """Delete this item from history"""
        if 'id' in self.item:
            # Find the parent history widget
            parent = self.parent()
            while parent and not isinstance(parent, HistoryWidget):
                parent = parent.parent()
            
            if parent:
                parent.delete_item(self.item['id'])
    
    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.setStyleSheet("background-color: #f0f7ff;")
        
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.setStyleSheet("")
        
    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.RightButton:
            self.show_context_menu(event.pos())
        else:
            super().mousePressEvent(event)
    
    def show_context_menu(self, position):
        """Show context menu with options"""
        context_menu = QMenu(self)
        
        copy_action = QAction("Copy to Clipboard", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_item)
        
        context_menu.addAction(copy_action)
        context_menu.addAction(delete_action)
        
        context_menu.exec_(self.mapToGlobal(position))


class HistoryWidget(QScrollArea):
    """Widget that displays clipboard history"""
    
    def __init__(self, clipboard_monitor, storage_manager, filter_type=None, parent=None):
        super().__init__(parent)
        
        self.clipboard_monitor = clipboard_monitor
        self.storage_manager = storage_manager
        self.filter_type = filter_type
        
        self.init_ui()
        self.update_history()
    
    def init_ui(self):
        """Initialize the UI"""
        # Setup scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create container widget
        self.container = QWidget()
        self.setWidget(self.container)
        
        # Create layout
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignTop)
    
    def update_history(self, search=None):
        """Update the displayed history items"""
        # Clear current items
        self.clear_layout()
        
        # Get history from storage manager
        history = self.storage_manager.get_history(search=search)
        
        # Filter by type if specified
        if self.filter_type:
            history = [item for item in history if item.get('type') == self.filter_type]
        
        # Add items to layout
        if history:
            for item in history:
                item_widget = ClipboardItemWidget(item, self.clipboard_monitor)
                self.layout.addWidget(item_widget)
        else:
            # Show empty state
            empty_label = QLabel("No clipboard history found")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
            self.layout.addWidget(empty_label)
    
    def clear_layout(self):
        """Clear all widgets from layout"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def delete_item(self, item_id):
        """Delete an item and update the display"""
        self.storage_manager.delete_item(item_id)
        self.update_history()
