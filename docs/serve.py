import http.server
import socketserver
import os
import sys

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def log_message(self, format, *args):
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), format % args))
        sys.stdout.flush()

def find_free_port(start=8080, max_attempts=50):
    for port in range(start, start + max_attempts):
        try:
            with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as test:
                return port
        except OSError:
            continue
    return start

if __name__ == '__main__':
    port = find_free_port(PORT)
    handler = CORSHTTPRequestHandler

    with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
        local_ip = None
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "localhost"

        print("")
        print("  ============================================")
        print("    美股情绪监测 - 手机版开发服务器")
        print("  ============================================")
        print("")
        print("  本地访问:  http://localhost:%d" % port)
        if local_ip:
            print("  手机访问:  http://%s:%d" % (local_ip, port))
        print("")
        print("  请确保手机与电脑连接在同一个 WiFi 网络")
        print("  Ctrl+C 停止服务器")
        print("  ============================================")
        print("")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")