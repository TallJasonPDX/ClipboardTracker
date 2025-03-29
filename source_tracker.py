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
                import win32con
                self.win32gui = win32gui
                self.win32process = win32process
                self.win32con = win32con
                self.has_win32 = True
            except ImportError:
                pass
    
    def get_source_info(self):
        """
        Get information about the source of the clipboard content
        Returns a dictionary with source details
        """
        # Use Windows-specific implementation if available
        if self.is_windows and self.has_win32:
            return self._get_windows_source_info()
        # Use generic implementation for non-Windows platforms
        return self._get_generic_source_info()
    
    def _extract_url_from_title(self, title):
        """Try to extract full URL from window title"""
        # Common patterns for URLs in browser titles
        patterns = [
            # Full URL if present
            r'(?:https?://)?(?:www\.)?([^\s]+\.[^\s]+)',
            # Domain only patterns
            r'[•\-]\s*([^•\-\s]+\.[^•\-\s]+)\s*[\-•]',
            r'(?:www\.)?([^/\s]+\.[^/\s]{2,})',
        ]
        
        for pattern in patterns:
            matches = re.search(pattern, title, re.IGNORECASE)
            if matches:
                url = matches.group(1)
                # Clean up URL
                url = url.rstrip('.')
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                return url
        
        return ""

    def _get_windows_source_info(self):
        """Windows-specific implementation using win32gui"""
        try:
            # Get foreground window handle
            hwnd = self.win32gui.GetForegroundWindow()
            
            # Get process ID and thread ID
            _, pid = self.win32process.GetWindowThreadProcessId(hwnd)
            
            # Get window title
            window_title = self.win32gui.GetWindowText(hwnd)
            
            # Get process info
            try:
                process = psutil.Process(pid)
                proc_name = process.name()
                exe_path = process.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                proc_name = "Unknown"
                exe_path = ""
            
            # Create source info
            source_info = {
                "application": {
                    "name": proc_name,
                    "type": "desktop",
                    "platform": self.platform,
                    "window_title": window_title,
                    "active_process": proc_name,
                    "executable_path": exe_path
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Check if it's a browser
            proc_name_lower = proc_name.lower()
            for browser_key, browser_name in self.browser_processes.items():
                if browser_key in proc_name_lower:
                    source_info["application"]["type"] = "browser"
                    source_info["application"]["browser"] = browser_name
                    
                    # Try to get the full URL from the window title
                    url = self._extract_url_from_title(window_title)
                    
                    # Get page title by removing URL/domain and browser name from window title
                    page_title = window_title
                    if url:
                        # Clean up page title
                        page_title = window_title
                        for marker in [f" - {browser_name}", url, f" • {url}"]:
                            if marker in page_title:
                                page_title = page_title.split(marker)[0].strip()
                        
                        source_info["website"] = {
                            "title": page_title,
                            "domain": url.split('/')[2] if '://' in url else url.split('/')[0],
                            "url": url
                        }
                    
                    # Try to get URL directly from browser window if available
                    try:
                        # Look for URL bar child window
                        def callback(child_hwnd, url):
                            if not url[0]:  # if URL not found yet
                                class_name = self.win32gui.GetClassName(child_hwnd)
                                if class_name in ['Chrome_OmniboxView', 'Edit']:  # URL bar classes
                                    length = self.win32gui.SendMessage(child_hwnd, self.win32con.WM_GETTEXTLENGTH, 0, 0)
                                    if length > 0:
                                        buff = self.win32gui.PyMakeBuffer(length + 1)
                                        self.win32gui.SendMessage(child_hwnd, self.win32con.WM_GETTEXT, length + 1, buff)
                                        url[0] = buff.tobytes().decode('utf-16').strip('\x00')
                            return True
                        
                        url = ['']  # Use list to allow modification in callback
                        self.win32gui.EnumChildWindows(hwnd, callback, url)
                        
                        if url[0] and ('://' in url[0] or '.' in url[0]):
                            browser_url = url[0]
                            if not browser_url.startswith(('http://', 'https://')):
                                browser_url = 'https://' + browser_url
                            
                            source_info["website"] = {
                                "title": page_title,
                                "domain": browser_url.split('/')[2] if '://' in browser_url else browser_url.split('/')[0],
                                "url": browser_url
                            }
                    except Exception as e:
                        print(f"Error getting URL from browser window: {e}")
            
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
    
    def _get_generic_source_info(self):
        """Cross-platform fallback implementation"""
        try:
            # Get current process info
            current_proc = psutil.Process()
            
            # Get active window info from psutil
            source_info = {
                "application": {
                    "name": current_proc.name(),
                    "type": "desktop",
                    "platform": self.platform,
                    "window_title": "Unknown Window",
                    "active_process": current_proc.name(),
                    "executable_path": current_proc.exe() if hasattr(current_proc, 'exe') else ""
                },
                "timestamp": datetime.now().isoformat()
            }
            
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
