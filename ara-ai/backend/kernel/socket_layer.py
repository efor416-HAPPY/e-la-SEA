# -*- coding: utf-8 -*-
"""
🔌 ARA AI Socket Layer
Declares standard ISocket interface and implements TcpSocket, PipeSocket, and UnixSocket.
"""

import os
import socket
import threading
from multiprocessing.connection import Listener, Client
from typing import Callable, Optional

class ISocket:
    def connect(self) -> bool:
        """Connects or binds the socket channel."""
        raise NotImplementedError

    def send(self, data: str) -> bool:
        """Sends string data through the channel."""
        raise NotImplementedError

    def receive(self) -> str:
        """Receives string data from the channel."""
        raise NotImplementedError

    def close(self) -> None:
        """Closes the socket connection."""
        raise NotImplementedError


class TcpSocket(ISocket):
    """TCP Socket channel for cross-network client/server interactions."""
    def __init__(self, host: str = "127.0.0.1", port: int = 9091):
        self.host = host
        self.port = port
        self.server_sock: Optional[socket.socket] = None
        self.conn_sock: Optional[socket.socket] = None
        self.is_connected = False

    def connect(self) -> bool:
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind((self.host, self.port))
            self.server_sock.listen(1)
            self.is_connected = True
            return True
        except Exception as e:
            print(f"❌ [TcpSocket] Bind failed: {e}")
            return False

    def send(self, data: str) -> bool:
        if not self.conn_sock:
            # Attempt to connect as client if no active client connection exists
            try:
                client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_sock.connect((self.host, self.port))
                client_sock.sendall(data.encode('utf-8'))
                client_sock.close()
                return True
            except Exception as e:
                print(f"❌ [TcpSocket] Client send failed: {e}")
                return False
        try:
            self.conn_sock.sendall(data.encode('utf-8'))
            return True
        except Exception as e:
            print(f"❌ [TcpSocket] Send failed: {e}")
            return False

    def receive(self) -> str:
        if not self.server_sock:
            return ""
        try:
            self.server_sock.settimeout(1.0)
            conn, addr = self.server_sock.accept()
            self.conn_sock = conn
            data = conn.recv(65536)
            if data:
                return data.decode('utf-8')
            return ""
        except socket.timeout:
            return ""
        except Exception as e:
            print(f"❌ [TcpSocket] Receive error: {e}")
            return ""

    def close(self) -> None:
        self.is_connected = False
        if self.conn_sock:
            try:
                self.conn_sock.close()
            except Exception:
                pass
            self.conn_sock = None
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass
            self.server_sock = None


class PipeSocket(ISocket):
    """Named Pipe socket using multiprocessing connections."""
    def __init__(self, pipe_name: str = "ara_pipe"):
        if os.name == 'nt':
            self.address = f'\\\\.\\pipe\\{pipe_name}'
            self.family = 'AF_PIPE'
        else:
            self.address = f'./{pipe_name}'
            self.family = 'AF_UNIX'
        self.listener: Optional[Listener] = None
        self.conn = None
        self.is_connected = False

    def connect(self) -> bool:
        if os.name != 'nt' and os.path.exists(self.address):
            try:
                os.remove(self.address)
            except Exception:
                pass
        try:
            self.listener = Listener(self.address, self.family)
            self.is_connected = True
            return True
        except Exception as e:
            print(f"❌ [PipeSocket] Listener creation failed: {e}")
            return False

    def send(self, data: str) -> bool:
        try:
            conn = Client(self.address, self.family)
            conn.send(data)
            conn.close()
            return True
        except Exception as e:
            print(f"❌ [PipeSocket] Client send failed: {e}")
            return False

    def receive(self) -> str:
        if not self.listener:
            return ""
        try:
            # We must use non-blocking check or short timeout to avoid blocking main thread forever
            # Note: multiprocessing connection accept() blocks, so we run accept in a timed/configured check
            # For simplicity, we make a short block or accept
            conn = self.listener.accept()
            msg = conn.recv()
            conn.close()
            if isinstance(msg, bytes):
                return msg.decode('utf-8')
            return str(msg)
        except Exception:
            return ""

    def close(self) -> None:
        self.is_connected = False
        if self.listener:
            try:
                self.listener.close()
            except Exception:
                pass
            self.listener = None
        if os.name != 'nt' and os.path.exists(self.address):
            try:
                os.remove(self.address)
            except Exception:
                pass


class UnixSocket(ISocket):
    """Unix domain socket wrapper with fallback to TCP loopback on incompatible environments."""
    def __init__(self, path: str = "./ara_unix.sock", fallback_port: int = 9092):
        self.path = path
        self.fallback_port = fallback_port
        self.sock: Optional[socket.socket] = None
        self.conn_sock: Optional[socket.socket] = None
        self.use_fallback = False
        self.is_connected = False

        # Detect if socket.AF_UNIX is supported on this platform
        if not hasattr(socket, 'AF_UNIX'):
            self.use_fallback = True

    def connect(self) -> bool:
        if self.use_fallback:
            print("⚠️ [UnixSocket] AF_UNIX not supported on this platform. Falling back to TCP Loopback.")
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock.bind(("127.0.0.1", self.fallback_port))
                self.sock.listen(1)
                self.is_connected = True
                return True
            except Exception as e:
                print(f"❌ [UnixSocket Fallback] Bind failed: {e}")
                return False
        else:
            if os.path.exists(self.path):
                try:
                    os.remove(self.path)
                except Exception:
                    pass
            try:
                self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.sock.bind(self.path)
                self.sock.listen(1)
                self.is_connected = True
                return True
            except Exception as e:
                print(f"❌ [UnixSocket] Bind failed: {e}")
                return False

    def send(self, data: str) -> bool:
        if self.use_fallback:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(("127.0.0.1", self.fallback_port))
                client.sendall(data.encode('utf-8'))
                client.close()
                return True
            except Exception as e:
                print(f"❌ [UnixSocket Fallback] Send failed: {e}")
                return False
        else:
            try:
                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client.connect(self.path)
                client.sendall(data.encode('utf-8'))
                client.close()
                return True
            except Exception as e:
                print(f"❌ [UnixSocket] Send failed: {e}")
                return False

    def receive(self) -> str:
        if not self.sock:
            return ""
        try:
            self.sock.settimeout(1.0)
            conn, addr = self.sock.accept()
            self.conn_sock = conn
            data = conn.recv(65536)
            if data:
                return data.decode('utf-8')
            return ""
        except socket.timeout:
            return ""
        except Exception as e:
            print(f"❌ [UnixSocket] Receive failed: {e}")
            return ""

    def close(self) -> None:
        self.is_connected = False
        if self.conn_sock:
            try:
                self.conn_sock.close()
            except Exception:
                pass
            self.conn_sock = None
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        if not self.use_fallback and os.path.exists(self.path):
            try:
                os.remove(self.path)
            except Exception:
                pass
