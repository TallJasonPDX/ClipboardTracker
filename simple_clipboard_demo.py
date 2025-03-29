"""
Simple Clipboard History Manager Demo
Command-line version for headless environments
"""
import json
import time
import os
import datetime
from pathlib import Path

# Setup storage path
STORAGE_FILE = Path.home() / ".clipboard_history.json"

class SimpleStorageManager:
    """Simple version of the storage manager for command-line demo"""
    
    def __init__(self, storage_file=None):
        self.storage_file = storage_file or STORAGE_FILE
        self.history = []
        self.load_history()
    
    def load_history(self):
        """Load clipboard history from the JSON file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    self.history = json.load(f)
                print(f"Loaded {len(self.history)} items from history.")
            else:
                print("No history file found. Starting with empty history.")
                self.history = []
        except Exception as e:
            print(f"Error loading history: {e}")
            self.history = []
    
    def save_history(self):
        """Save clipboard history to the JSON file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_clipboard_item(self, item):
        """Add a new clipboard item to history"""
        # Add unique ID
        item['id'] = str(time.time())
        
        # Add to history (at the beginning)
        self.history.insert(0, item)
        
        # Limit history size
        if len(self.history) > 100:
            self.history = self.history[:100]
        
        # Save to file
        self.save_history()
    
    def get_history(self, limit=None, search=None):
        """Get clipboard history, optionally filtered"""
        result = self.history
        
        # Apply search filter if provided
        if search:
            search = search.lower()
            result = []
            for item in self.history:
                if item['type'] == 'text' and search in item['content'].lower():
                    result.append(item)
        
        # Apply limit if provided
        if limit and limit > 0:
            result = result[:limit]
            
        return result
    
    def clear_history(self):
        """Clear the clipboard history"""
        self.history = []
        self.save_history()
        print("Clipboard history cleared.")
    
    def delete_item(self, item_id):
        """Delete a specific item from history"""
        self.history = [i for i in self.history if i.get('id') != item_id]
        self.save_history()
        print(f"Deleted item {item_id} from history.")

def display_menu():
    """Display the main menu"""
    print("\n=== Clipboard History Manager Demo ===")
    print("1. View clipboard history")
    print("2. Add text to clipboard")
    print("3. Search history")
    print("4. Clear history")
    print("5. Exit")
    return input("Enter option (1-5): ")

def format_timestamp(timestamp):
    """Format a timestamp for display"""
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Unknown time"

def display_clipboard_items(items):
    """Display clipboard items in the console"""
    if not items:
        print("No items in clipboard history.")
        return
    
    print(f"\nFound {len(items)} items in clipboard history:")
    print("-" * 50)
    
    for i, item in enumerate(items, 1):
        item_id = item.get('id', 'unknown')
        timestamp = item.get('timestamp', 0)
        formatted_time = format_timestamp(timestamp)
        
        # Get application info if available
        source_info = ""
        if 'source' in item:
            app_info = item['source'].get('application', {})
            app_name = app_info.get('name', 'Unknown')
            
            if app_info.get('type') == 'browser':
                domain = item['source'].get('website', {}).get('domain', '')
                if domain:
                    source_info = f"from {domain} ({app_info.get('browser', '')})"
                else:
                    source_info = f"from {app_info.get('browser', '')}"
            else:
                window_title = app_info.get('window_title', '')
                if window_title:
                    source_info = f"from {window_title} ({app_name})"
                else:
                    source_info = f"from {app_name}"
        
        print(f"Item {i} ({formatted_time}) {source_info}")
        print(f"ID: {item_id}")
        
        if item['type'] == 'text':
            # Truncate text if it's too long
            content = item['content']
            if len(content) > 100:
                content = content[:97] + "..."
            print(f"Text: {content}")
        elif item['type'] == 'image':
            width = item.get('width', 0)
            height = item.get('height', 0)
            print(f"Image: {width}x{height}")
        else:
            print(f"Type: {item['type']}")
        
        print("-" * 50)

def add_demo_text():
    """Add demo text to clipboard history"""
    storage_manager = SimpleStorageManager()
    
    text = input("Enter text to add to clipboard: ")
    
    # Create a clipboard item
    clipboard_item = {
        "type": "text",
        "content": text,
        "timestamp": time.time(),
        "source": {
            "application": {
                "name": "simple_clipboard_demo.py",
                "type": "desktop",
                "window_title": "Command Line Demo"
            },
            "timestamp": datetime.datetime.now().isoformat()
        }
    }
    
    # Add to history
    storage_manager.add_clipboard_item(clipboard_item)
    print(f"Added '{text}' to clipboard history.")

def search_history():
    """Search through clipboard history"""
    storage_manager = SimpleStorageManager()
    
    search_term = input("Enter search term: ")
    results = storage_manager.get_history(search=search_term)
    
    display_clipboard_items(results)

def main():
    """Main function for the command-line demo"""
    print("=" * 50)
    print("Clipboard History Manager Demo")
    print("Command-line version for demonstration")
    print("=" * 50)
    
    storage_manager = SimpleStorageManager()
    
    while True:
        option = display_menu()
        
        if option == '1':
            # View clipboard history
            items = storage_manager.get_history()
            display_clipboard_items(items)
        
        elif option == '2':
            # Add text to clipboard
            add_demo_text()
        
        elif option == '3':
            # Search history
            search_history()
        
        elif option == '4':
            # Clear history
            confirm = input("Are you sure you want to clear the clipboard history? (y/n): ")
            if confirm.lower() == 'y':
                storage_manager.clear_history()
        
        elif option == '5':
            # Exit
            print("Exiting Clipboard History Manager Demo. Goodbye!")
            break
        
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()