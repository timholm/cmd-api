import http.server
import json
import subprocess
import socketserver
import paramiko

PORT = 3000

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Command API running.\nPOST /run - shell commands\nPOST /ssh - SSH remote commands\nPOST /claude - Claude Code prompts")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        
        try:
            data = json.loads(body)
        except:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        if self.path == "/run":
            cmd = data.get("cmd", "")
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
                response = {
                    "stdout": result.stdout.decode(),
                    "stderr": result.stderr.decode(),
                    "code": result.returncode
                }
            except Exception as e:
                response = {"error": str(e)}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        elif self.path == "/ssh":
            host = data.get("host", "")
            username = data.get("username", "")
            password = data.get("password", "")
            command = data.get("command", "")
            port = data.get("port", 22)

            if not all([host, username, password, command]):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "Missing host, username, password, or command"}')
                return

            print(f"[SSH] Connecting to {username}@{host}...")
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(host, port=port, username=username, password=password, timeout=10)
                stdin, stdout, stderr = client.exec_command(command, timeout=30)
                response = {
                    "stdout": stdout.read().decode(),
                    "stderr": stderr.read().decode(),
                    "code": stdout.channel.recv_exit_status()
                }
                client.close()
                print(f"[SSH] Command completed with code {response['code']}")
            except Exception as e:
                print(f"[SSH] Error: {e}")
                response = {"error": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        elif self.path == "/claude":
            prompt = data.get("prompt", "")
            if not prompt:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "Missing prompt"}')
                return

            print(f"[Claude] Received: {prompt[:100]}...")
            try:
                result = subprocess.run(
                    ["/Users/tim/.local/bin/claude", "-p", prompt, "--print"],
                    capture_output=True,
                    timeout=300,
                    env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": "/Users/tim"}
                )
                response = {
                    "response": result.stdout.decode(),
                    "stderr": result.stderr.decode(),
                    "code": result.returncode
                }
                print(f"[Claude] Completed with code {result.returncode}")
            except Exception as e:
                print(f"[Claude] Error: {e}")
                response = {"error": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with ReusableTCPServer(("", PORT), Handler) as httpd:
        print(f"Command API running on port {PORT}")
        httpd.serve_forever()
