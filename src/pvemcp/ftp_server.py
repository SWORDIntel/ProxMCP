from __future__ import annotations

import socket
import threading
import time
from pathlib import Path
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer


class TemporaryFTPServer:
    """A short-lived FTP server for file transfers between host and guest."""

    def __init__(self, root_dir: str | Path, host: str = "0.0.0.0", port: int = 0):
        self.root_dir = Path(root_dir).absolute()
        self.host = host
        self.requested_port = port
        self.port = port
        self.server: FTPServer | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def __enter__(self) -> TemporaryFTPServer:
        authorizer = DummyAuthorizer()
        # Allow anonymous read/write in the temporary directory
        authorizer.add_anonymous(str(self.root_dir), perm="elradfmw")
        
        handler = FTPHandler
        handler.authorizer = authorizer
        # Disable logging to stderr to keep MCP output clean
        handler.log_prefix = ""
        import logging
        logging.getLogger("pyftpdlib").setLevel(logging.ERROR)

        self.server = FTPServer((self.host, self.requested_port), handler)
        self.port = self.server.address[1]
        
        self._thread = threading.Thread(target=self.server.serve_forever, kwargs={"timeout": 1})
        self._thread.daemon = True
        self._thread.start()
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.server:
            self.server.close_all()
        if self._thread:
            self._thread.join(timeout=2)

    def get_reachable_ip(self) -> str:
        """Attempt to find an IP address reachable by the guest."""
        # Common strategy: get the default gateway's interface IP
        try:
            # This doesn't actually send data, just opens a socket to find the local IP used to reach '8.8.8.8'
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            # Fallback to hostname-based detection
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"
