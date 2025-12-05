"""
UDP Broadcast ile oyuncu keşfi (discovery)
"""
import socket
import threading
import time
from network.messages import discover_message, announce_message, parse_message, MessageType

DISCOVERY_PORT = 37020
BROADCAST_INTERVAL = 2  # Her 2 saniyede bir broadcast

class PlayerDiscovery:
    def __init__(self, player_name, tcp_port):
        self.player_name = player_name
        self.tcp_port = tcp_port
        self.running = False
        self.discovered_players = {}  # {ip: {"name": name, "tcp_port": port, "last_seen": time}}
        self.sock = None
        self.broadcast_thread = None
        self.listen_thread = None
        
    def start(self):
        """Discovery başlat"""
        self.running = True
        
        # UDP soket oluştur
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', DISCOVERY_PORT))
        self.sock.settimeout(1.0)
        
        # Thread'leri başlat
        self.broadcast_thread = threading.Thread(target=self._broadcast_presence, daemon=True)
        self.listen_thread = threading.Thread(target=self._listen_for_players, daemon=True)
        
        self.broadcast_thread.start()
        self.listen_thread.start()
        
    def stop(self):
        """Discovery durdur"""
        self.running = False
        if self.sock:
            self.sock.close()
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=2)
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
    
    def _broadcast_presence(self):
        """Varlığını broadcast et"""
        while self.running:
            try:
                msg = announce_message(self.player_name, self.tcp_port)
                self.sock.sendto(msg.encode(), ('<broadcast>', DISCOVERY_PORT))
                time.sleep(BROADCAST_INTERVAL)
            except:
                pass
    
    def _listen_for_players(self):
        """Diğer oyuncuları dinle"""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                ip = addr[0]
                
                # Kendi IP'mizi görmezden gel
                if self._is_own_ip(ip):
                    continue
                
                msg_type, msg_data = parse_message(data.decode())
                
                if msg_type == MessageType.ANNOUNCE:
                    self.discovered_players[ip] = {
                        "name": msg_data.get("name", "Unknown"),
                        "tcp_port": msg_data.get("tcp_port", 0),
                        "last_seen": time.time()
                    }
            except socket.timeout:
                continue
            except:
                pass
        
        # Eski oyuncuları temizle
        self._cleanup_old_players()
    
    def _cleanup_old_players(self):
        """5 saniyeden eski oyuncuları listeden çıkar"""
        current_time = time.time()
        to_remove = []
        for ip, info in self.discovered_players.items():
            if current_time - info["last_seen"] > 5:
                to_remove.append(ip)
        for ip in to_remove:
            del self.discovered_players[ip]
    
    def _is_own_ip(self, ip):
        """IP bizim mi kontrol et"""
        try:
            hostname = socket.gethostname()
            local_ips = socket.gethostbyname_ex(hostname)[2]
            return ip in local_ips or ip == '127.0.0.1'
        except:
            return False
    
    def get_players(self):
        """Keşfedilen oyuncuları döndür"""
        self._cleanup_old_players()
        return dict(self.discovered_players)
