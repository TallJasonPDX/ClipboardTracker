"""
Source Tracker Module
Identifies the source application or website from which content was copied
"""
import win32gui
import win32process
import psutil
import re
import os
from datetime import datetime

class SourceTracker:
    """
    Tracks the source of clipboard content (application or website)
    """
    def __init__(self):
        # Regular expressions to identify web browsers
        self.browser_processes = {
            "chrome.exe": "Google Chrome",
            "firefox.exe": "Firefox",
            "msedge.exe": "Microsoft Edge",
            "opera.exe": "Opera",
            "brave.exe": "Brave",
            "safari.exe": "Safari",
            "iexplore.exe": "Internet Explorer"
        }
        
        # Regex pattern for URLs
        self.url_pattern = re.compile(r'^(https?://)?(www\.)?([^/\s]+\.[^/\s]{2,})')
    
    def get_source_info(self):
        """
        Get information about the source of the clipboard content
        Returns a dictionary with source details
        """
        try:
            # Get foreground window handle
            foreground_window = win32gui.GetForegroundWindow()
            
            # Get window title
            window_title = win32gui.GetWindowText(foreground_window)
            
            # Get process ID
            _, process_id = win32process.GetWindowThreadProcessId(foreground_window)
            
            # Get process name
            process = psutil.Process(process_id)
            process_name = process.name()
            
            # Get executable path
            try:
                exe_path = process.exe()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                exe_path = ""
            
            # Determine if it's a browser
            is_browser = False
            browser_name = ""
            for browser_exe, name in self.browser_processes.items():
                if process_name.lower() == browser_exe.lower():
                    is_browser = True
                    browser_name = name
                    break
            
            # Extract domain if it's a browser
            domain = ""
            if is_browser and window_title:
                # Try to extract domain from window title
                match = self.url_pattern.search(window_title)
                if match:
                    domain = match.group(3)
                else:
                    # Common browser title formats
                    # Format: Page Title - Browser Name
                    parts = window_title.split(" - ")
                    if len(parts) > 1 and parts[-1] in self.browser_processes.values():
                        title = " - ".join(parts[:-1])
                        domain = title.strip()
                    else:
                        domain = window_title
            
            # Create source info
            source_info = {
                "application": {
                    "name": process_name,
                    "path": exe_path,
                    "window_title": window_title
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Add browser and website info if applicable
            if is_browser:
                source_info["application"]["type"] = "browser"
                source_info["application"]["browser"] = browser_name
                
                if domain:
                    source_info["website"] = {
                        "title": window_title,
                        "domain": domain
                    }
            else:
                source_info["application"]["type"] = "desktop"
            
            return source_info
            
        except Exception as e:
            # Return basic information on error
            return {
                "application": {
                    "name": "Unknown",
                    "type": "unknown",
                    "error": str(e)
                },
                "timestamp": datetime.now().isoformat()
            }
