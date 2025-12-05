"""
TCP Client - Bağlanan oyuncu için
"""
import socket
import threading
from network.messages import parse_message

class GameClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.receive_thread = None
        self.message_callback = None
        
    def connect(self, host, port, message_callback):
        """Servera bağlan"""
        self.message_callback = message_callback
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((host, port))
            self.socket.settimeout(1.0)
            
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            if self.message_callback:
                self.message_callback("connected", {})
            
            return True
        except Exception as e:
            print(f"Bağlantı hatası: {e}")
            return False
    
    def disconnect(self):
        """Bağlantıyı kes"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
    
    def _receive_messages(self):
        """Mesajları al"""
        buffer = ""
        while self.running and self.socket:
            try:
                data = self.socket.recv(4096).decode()
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
        if self.socket:
            try:
                self.socket.sendall((message + "\n").encode())
                return True
            except:
                return False
        return False
    
    def is_connected(self):
        """Bağlı mı?"""
        return self.socket is not None and self.running
