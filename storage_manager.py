"""
Storage Manager Module
Handles saving and loading clipboard history from JSON file
"""
import os
import json
import time
from datetime import datetime
import base64

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
        
        # Initialize history
        self.clipboard_history = []
        
        # Load existing history
        self.load_history()
    
    def load_history(self):
        """Load clipboard history from the JSON file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Process the loaded data
                    for item in data:
                        # Convert image data from base64 if needed
                        if item.get('type') == 'image' and isinstance(item.get('content'), str):
                            try:
                                item['content'] = base64.b64decode(item['content'])
                            except Exception:
                                # If decoding fails, skip this item
                                continue
                    
                    self.clipboard_history = data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading clipboard history: {e}")
            # If file is corrupted, start with empty history
            self.clipboard_history = []
    
    def save_history(self):
        """Save clipboard history to the JSON file"""
        try:
            # Prepare data for saving
            save_data = []
            
            for item in self.clipboard_history:
                # Create a copy to avoid modifying the original
                save_item = item.copy()
                
                # Convert binary image data to base64 for storage
                if item.get('type') == 'image' and isinstance(item.get('content'), bytes):
                    save_item['content'] = base64.b64encode(item['content']).decode('utf-8')
                
                save_data.append(save_item)
            
            # Write to file
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
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
        
        # Add to history
        self.clipboard_history.insert(0, item)  # Add to beginning
        
        # Limit history size (e.g., 100 items)
        max_items = 100
        if len(self.clipboard_history) > max_items:
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
        self.clipboard_history = []
        self.save_history()
    
    def delete_item(self, item_id):
        """Delete a specific item from history"""
        self.clipboard_history = [item for item in self.clipboard_history if item['id'] != item_id]
        self.save_history()
