"""
Storage Manager Module
Handles saving and loading clipboard history from JSON file
"""
import os
import json
import time
from datetime import datetime

class StorageManager:
    """
    Manages the storage and retrieval of clipboard history
    """
    def __init__(self, storage_file=None):
        # Default storage location is user's home directory
        if storage_file is None:
            home_dir = os.path.expanduser("~")
            self.storage_dir = os.path.join(home_dir, "ClipboardManager")
            self.storage_file = os.path.join(self.storage_dir, "clipboard_history.json")
        else:
            self.storage_file = storage_file
            self.storage_dir = os.path.dirname(storage_file)
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            
        # Create images directory if it doesn't exist
        self.images_dir = os.path.join(self.storage_dir, "images")
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        
        # Initialize history
        self.clipboard_history = []
        
        # Load existing history
        self.load_history()
    
    def load_history(self):
        """Load clipboard history from the JSON file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.clipboard_history = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading clipboard history: {e}")
            # If file is corrupted, start with empty history
            self.clipboard_history = []
    
    def save_history(self):
        """Save clipboard history to the JSON file"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.clipboard_history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving clipboard history: {e}")
    
    def add_clipboard_item(self, item):
        """Add a new clipboard item to history"""
        # Add unique ID based on timestamp
        item['id'] = str(int(time.time() * 1000))
        
        # Add human-readable timestamp
        if 'timestamp' not in item:
            item['timestamp'] = time.time()
        
        item['datetime'] = datetime.fromtimestamp(item['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        
        # Handle image content
        if item['type'] == 'image':
            image_filename = f"image_{item['id']}.png"
            image_path = os.path.join(self.images_dir, image_filename)
            
            # Save image to file
            try:
                with open(image_path, 'wb') as f:
                    f.write(item['content'])
                # Replace binary content with filename reference
                item['content'] = image_filename
            except IOError as e:
                print(f"Error saving image file: {e}")
                return None
        
        # Add to history
        self.clipboard_history.insert(0, item)  # Add to beginning
        
        # Limit history size (e.g., 100 items)
        max_items = 100
        if len(self.clipboard_history) > max_items:
            # Clean up old image files when removing history items
            for old_item in self.clipboard_history[max_items:]:
                if old_item['type'] == 'image':
                    old_image_path = os.path.join(self.images_dir, old_item['content'])
                    try:
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except OSError as e:
                        print(f"Error removing old image file: {e}")
            
            self.clipboard_history = self.clipboard_history[:max_items]
        
        # Save to file
        self.save_history()
        
        return item
    
    def get_history(self, limit=None, search=None):
        """
        Get clipboard history, optionally filtered
        
        Args:
            limit: Maximum number of items to return
            search: Search text to filter items
            
        Returns:
            List of clipboard items
        """
        results = self.clipboard_history
        
        # Apply search filter if provided
        if search and search.strip():
            search = search.lower()
            filtered_results = []
            
            for item in results:
                if item['type'] == 'text' and search in item['content'].lower():
                    filtered_results.append(item)
                elif 'source' in item:
                    # Search in source information
                    source = item['source']
                    window_title = source.get('application', {}).get('window_title', '').lower()
                    app_name = source.get('application', {}).get('name', '').lower()
                    domain = source.get('website', {}).get('domain', '').lower()
                    
                    if (search in window_title or 
                        search in app_name or 
                        search in domain):
                        filtered_results.append(item)
            
            results = filtered_results
        
        # Apply limit if provided
        if limit and limit > 0:
            results = results[:limit]
        
        return results
    
    def clear_history(self):
        """Clear the clipboard history"""
        # Delete all image files
        for item in self.clipboard_history:
            if item['type'] == 'image':
                image_path = os.path.join(self.images_dir, item['content'])
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except OSError as e:
                    print(f"Error removing image file: {e}")
        
        self.clipboard_history = []
        self.save_history()
    
    def delete_item(self, item_id):
        """Delete a specific item from history"""
        # Find and delete image file if it exists
        for item in self.clipboard_history:
            if item['id'] == item_id and item['type'] == 'image':
                image_path = os.path.join(self.images_dir, item['content'])
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except OSError as e:
                    print(f"Error removing image file: {e}")
        
        # Remove item from history
        self.clipboard_history = [item for item in self.clipboard_history if item['id'] != item_id]
        self.save_history()
