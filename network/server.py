"""
TCP Server - Host oyuncu için
"""
import socket
import threading
from network.messages import parse_message, MessageType

class GameServer:
    def __init__(self, port=37021):
        self.port = port
        self.running = False
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.accept_thread = None
        self.receive_thread = None
        self.message_callback = None
        
    def start(self, message_callback):
        """Server başlat"""
        self.message_callback = message_callback
        self.running = True
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(1.0)
        
        self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        self.accept_thread.start()
        
    def stop(self):
        """Server durdur"""
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        if self.accept_thread:
            self.accept_thread.join(timeout=2)
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
    
    def _accept_connections(self):
        """Bağlantı kabul et"""
        while self.running:
            try:
                self.client_socket, self.client_address = self.server_socket.accept()
                self.client_socket.settimeout(1.0)
                
                # Mesaj dinlemeyi başlat
                self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
                self.receive_thread.start()
                
                if self.message_callback:
                    self.message_callback("connected", {"address": self.client_address})
                
                break  # Bir client yeterli
            except socket.timeout:
                continue
            except:
                break
    
    def _receive_messages(self):
        """Mesajları al"""
        buffer = ""
        while self.running and self.client_socket:
            try:
                data = self.client_socket.recv(4096).decode()
                if not data:
                    break
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line:
                        msg_type, msg_data = parse_message(line)
                        if msg_type and self.message_callback:
                            self.message_callback(msg_type, msg_data)
            except socket.timeout:
                continue
            except:
                break
        
        if self.message_callback:
            self.message_callback("disconnected", {})
    
    def send_message(self, message):
        """Mesaj gönder"""
        if self.client_socket:
            try:
                self.client_socket.sendall((message + "\n").encode())
                return True
            except:
                return False
        return False
    
    def is_connected(self):
        """Bağlı mı?"""
        return self.client_socket is not None
