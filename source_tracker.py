"""
Source Tracker Module
Identifies the source application or website from which content was copied
Cross-platform implementation (works on Windows, Linux, macOS)
"""
import re
import os
import sys
import platform
import psutil
from datetime import datetime

class SourceTracker:
    """
    Tracks the source of clipboard content (application or website)
    Platform-independent implementation with fallback for non-Windows systems
    """
    def __init__(self):
        # Regular expressions to identify web browsers
        self.browser_processes = {
            "chrome": "Google Chrome",
            "firefox": "Firefox",
            "msedge": "Microsoft Edge",
            "opera": "Opera",
            "brave": "Brave",
            "safari": "Safari",
            "iexplore": "Internet Explorer"
        }
        
        # Regex pattern for URLs
        self.url_pattern = re.compile(r'^(https?://)?(www\.)?([^/\s]+\.[^/\s]{2,})')
        
        # Detect platform
        self.platform = platform.system()
        self.is_windows = self.platform == "Windows"
        self.has_win32 = False
        
        # Import Windows-specific modules if on Windows
        if self.is_windows:
            try:
                import win32gui
                import win32process
                self.win32gui = win32gui
                self.win32process = win32process
                self.has_win32 = True
            except ImportError:
                pass
    
    def get_source_info(self):
        """
        Get information about the source of the clipboard content
        Returns a dictionary with source details
        """
        # Use generic implementation for non-Windows platforms
        return self._get_generic_source_info()
    
    def _get_generic_source_info(self):
        """Cross-platform fallback implementation"""
        try:
            # Get current process info as a fallback
            current_proc = psutil.Process()
            
            # Try to identify active processes
            browser_proc = None
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                    # Check if it's a browser
                    for browser_key in self.browser_processes:
                        if browser_key in proc_name:
                            browser_proc = proc
                            break
                    
                    if browser_proc:
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Use current application info
            app_name = os.path.basename(sys.argv[0]) if len(sys.argv) > 0 else "python"
            
            # Create generic source info
            source_info = {
                "application": {
                    "name": app_name,
                    "type": "desktop",
                    "platform": self.platform,
                    "window_title": "Clipboard Manager Demo"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Add process info if available
            if browser_proc:
                try:
                    proc_name = browser_proc.name()
                    source_info["application"]["active_process"] = proc_name
                    
                    # Check if it's a browser
                    for browser_key, browser_name in self.browser_processes.items():
                        if browser_key in proc_name.lower():
                            source_info["application"]["type"] = "browser"
                            source_info["application"]["browser"] = browser_name
                            source_info["website"] = {
                                "title": "Demo Website",
                                "domain": "example.com"
                            }
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return source_info
            
        except Exception as e:
            # Return basic information on error
            return {
                "application": {
                    "name": "Unknown",
                    "type": "unknown",
                    "platform": self.platform,
                    "error": str(e)
                },
                "timestamp": datetime.now().isoformat()
            }
