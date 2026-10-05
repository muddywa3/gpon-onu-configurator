import socket
import re
import time


class OLTTelnetClient:
    def __init__(self, host: str, port: int = 23, timeout: float = 5.0):
        self.host = host
        self.port = int(port)
        self.timeout = timeout
        self.sock = None

    def _strip_iac(self, data: bytes) -> bytes:
        """Strip Telnet IAC (Interpret As Command) control bytes (0xFF)."""
        clean = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 0xFF:
                if i + 1 < len(data) and data[i + 1] in (0xFA, 0xFB, 0xFC, 0xFD, 0xFE):
                    i += 3
                else:
                    i += 2
            else:
                clean.append(data[i])
                i += 1
        return bytes(clean)

    def connect(self):
        """Establish socket connection to the OLT."""
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(1.0)

    def read_until(self, pattern: str, timeout: float = 6.0) -> str:
        """Read buffer until regex pattern matches."""
        regex = re.compile(pattern.encode("utf-8"), re.IGNORECASE)
        buffer = bytearray()
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer.extend(self._strip_iac(chunk))
                if regex.search(buffer):
                    break
            except socket.timeout:
                time.sleep(0.1)
                continue

        return buffer.decode("utf-8", errors="ignore")

    def login(self, username, password, log_callback):
        """Authenticate with the OLT CLI."""
        log_callback(f"[+] Connecting to OLT at {self.host}:{self.port}...\n")
        self.connect()

        self.read_until(r"(?:user|login|username)[: ]*$")
        self.send(username)
        self.read_until(r"(?:password|pass)[: ]*$")
        self.send(password)

        prompt_res = self.read_until(r"[>#\$]\s*$")
        if "login invalid" in prompt_res.lower() or "incorrect" in prompt_res.lower():
            raise Exception("OLT Authentication Failed: Invalid Username or Password")
        log_callback("[+] Authenticated successfully to OLT.\n")

    def send(self, command: str):
        """Send command terminated with CRLF."""
        self.sock.sendall((command + "\r\n").encode("utf-8"))

    def exec_cmd(self, command: str, expected_prompt: str = r"[>#\$]\s*$", timeout: float = 6.0) -> str:
        """Send a CLI command and return output with better error handling."""
        try:
            self.send(command)
            response = self.read_until(expected_prompt, timeout=timeout)
            
            # Clean up the response by removing echo of the command
            lines = response.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Skip lines that are just the command echo or empty
                line_stripped = line.strip()
                if line_stripped and line_stripped != command.strip():
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass