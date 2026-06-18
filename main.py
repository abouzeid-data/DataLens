import webview
from api import Api
import sys
import os
import winreg
import html as html_lib
import json
import ctypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading
from pathlib import Path

ACTIVE_API = None
ACTIVE_WINDOW = None

def resource_path(relative_path):
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / relative_path)

def bring_datalens_to_front():
    if ACTIVE_WINDOW:
        for method_name in ("restore", "show"):
            method = getattr(ACTIVE_WINDOW, method_name, None)
            if method:
                try:
                    method()
                except Exception:
                    pass

        try:
            ACTIVE_WINDOW.evaluate_js("window.checkForResetToken && window.checkForResetToken()")
        except Exception:
            pass

    if os.name != "nt":
        return

    try:
        user32 = ctypes.windll.user32
        hwnds = []

        def enum_handler(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            title_buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buffer, length + 1)
            if title_buffer.value == "DataLens":
                hwnds.append(hwnd)
                return False
            return True

        enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(enum_handler)
        user32.EnumWindows(enum_proc, 0)

        if hwnds:
            hwnd = hwnds[0]
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)  # HWND_TOPMOST
            user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)  # HWND_NOTOPMOST
            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
    except Exception:
        pass

class RedirectHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logging

    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/reset":
            qs = parse_qs(parsed_url.query)
            token = qs.get("token", [""])[0]
            deep_link = f"datalens://reset-password?token={token}"
            escaped_deep_link = html_lib.escape(deep_link, quote=True)
            token_delivered = False
            if token and ACTIVE_API:
                ACTIVE_API.set_startup_token(token)
                bring_datalens_to_front()
                token_delivered = True
            
            if token_delivered:
                html_page = """
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center; color: #0f172a;">
                        <h2>DataLens is ready</h2>
                        <p>You can return to DataLens to choose your new password.</p>
                        <script>
                            setTimeout(() => window.close(), 1500);
                        </script>
                    </body>
                </html>
                """
            else:
                script_deep_link = json.dumps(deep_link)
                html_page = f"""
            <html>
                <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                    <h2>Opening DataLens...</h2>
                    <p>If the app does not open automatically, <a href="{escaped_deep_link}">click here</a>.</p>
                    <script>
                        window.location.href = {script_deep_link};
                        setTimeout(() => window.close(), 3000);
                    </script>
                </body>
            </html>
            """
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html_page.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def start_server():
    try:
        server = HTTPServer(('127.0.0.1', 5050), RedirectHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
    except Exception as e:
        print(f"Redirect server failed to start: {e}")

def get_protocol_executable():
    python_exe = sys.executable
    python_dir = os.path.dirname(python_exe)
    pythonw_exe = os.path.join(python_dir, "pythonw.exe")
    if os.path.basename(python_exe).lower() == "python.exe" and os.path.exists(pythonw_exe):
        return pythonw_exe
    return python_exe

def register_protocol():
    try:
        if getattr(sys, "frozen", False):
            app_exe = sys.executable
            command = f'"{app_exe}" "%1"'
            icon_path = app_exe
        else:
            python_exe = get_protocol_executable()
            script_path = os.path.abspath(__file__)
            command = f'"{python_exe}" "{script_path}" "%1"'
            icon_path = python_exe
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\datalens")
        winreg.SetValue(key, "", winreg.REG_SZ, "URL:DataLens Protocol")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        
        icon_key = winreg.CreateKey(key, "DefaultIcon")
        winreg.SetValue(icon_key, "", winreg.REG_SZ, f'"{icon_path}",0')
        
        cmd_key = winreg.CreateKey(key, r"shell\open\command")
        winreg.SetValue(cmd_key, "", winreg.REG_SZ, command)
    except Exception as e:
        print(f"Failed to register protocol: {e}")

def get_reset_token_from_args(args):
    for arg in args:
        if arg.startswith("datalens://"):
            parsed_url = urlparse(arg)
            if parsed_url.netloc == "reset-password" or parsed_url.path == "/reset-password":
                return parse_qs(parsed_url.query).get("token", [""])[0]
    return None

def main():
    register_protocol()
    
    startup_token = get_reset_token_from_args(sys.argv[1:])

    api = Api(startup_token=startup_token)
    global ACTIVE_API
    ACTIVE_API = api
    start_server()

    window = webview.create_window(
        'DataLens',
        resource_path('frontend/index.html'),
        width=1280,
        height=800,
        min_size=(1024, 600),
        js_api=api,
        text_select=True,
    )
    global ACTIVE_WINDOW
    ACTIVE_WINDOW = window
    webview.start(debug=False)

if __name__ == '__main__':
    main()
