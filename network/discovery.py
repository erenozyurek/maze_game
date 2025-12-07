"""
UDP Broadcast ile oyuncu keşfi (discovery)
"""

import socket
import threading
import time
from network.messages import discover_message, announce_message, parse_message, MessageType

DISCOVERY_PORT = 37020
BROADCAST_INTERVAL = 2  # Her 2 saniyede bir yayın

class PlayerDiscovery:
    def __init__(self, player_name, tcp_port, discovery_port=37020):
        self.player_name = player_name
        self.tcp_port = tcp_port
        self.discovery_port = discovery_port
        self.running = False
        self.discovered_players = {}  # {ip: {"name": name, "tcp_port": port, "last_seen": time}}
        self.sock = None
        self.broadcast_thread = None
        self.listen_thread = None

        # Lokal IP'yi belirle (kendini tespit için)
        self.local_ips = self._get_local_ips()

    def _get_local_ips(self):
        """Makinenin tüm IP adreslerini al"""
        ips = set()

        try:
            hostname = socket.gethostname()
            ips.update(socket.gethostbyname_ex(hostname)[2])
        except:
            pass

        # MacOS için ek IP bulma
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            ips.add(local_ip)
            s.close()
        except:
            pass

        print(f"[DISCOVERY] Local IPs: {ips}")
        return ips

    def _is_own_ip(self, ip):
        """Gelen IP bize mi ait kontrol et"""
        return ip in self.local_ips

    def start(self):
        """Discovery başlat"""
        self.running = True

        # UDP soketi aç
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # macOS için SO_REUSEPORT ekle (birden fazla program aynı portu dinleyebilsin)
        if hasattr(socket, 'SO_REUSEPORT'):
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        
        self.sock.bind(("", self.discovery_port))
        self.sock.settimeout(1.0)

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
            self.broadcast_thread.join(timeout=1)
        if self.listen_thread:
            self.listen_thread.join(timeout=1)

    def _broadcast_presence(self):
        """Kendi varlığını duyur"""
        while self.running:
            try:
                msg = announce_message(self.player_name, self.tcp_port)
                self.sock.sendto(msg.encode(), ("<broadcast>", self.discovery_port))
                print(f"[DISCOVERY] Broadcasting: {self.player_name} on port {self.tcp_port}")
                time.sleep(BROADCAST_INTERVAL)
            except Exception as e:
                print(f"[DISCOVERY] Broadcast error: {e}")
                pass

    def _listen_for_players(self):
        """Diğer oyuncuları dinle"""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                ip = addr[0]

                msg_type, msg_data = parse_message(data.decode())

                if msg_type == MessageType.ANNOUNCE:
                    player_name = msg_data.get("name", "Unknown")
                    tcp_port = msg_data.get("tcp_port", 0)
                    
                    # Kendimizi filtreleme: aynı TCP porta sahipse atla
                    if tcp_port == self.tcp_port:
                        continue
                    
                    print(f"[DISCOVERY] Found player: {player_name} at {ip}:{tcp_port}")
                    
                    self.discovered_players[ip] = {
                        "name": player_name,
                        "tcp_port": tcp_port,
                        "last_seen": time.time()
                    }

            except socket.timeout:
                continue
            except Exception as e:
                print(f"[DISCOVERY] Listen error: {e}")
                pass

        self._cleanup_old_players()

    def _cleanup_old_players(self):
        """5 saniyeden eski girişleri sil"""
        now = time.time()
        remove = []

        for ip, info in self.discovered_players.items():
            if now - info["last_seen"] > 5:
                remove.append(ip)

        for ip in remove:
            del self.discovered_players[ip]

    def get_players(self):
        """Anlık oyuncu listesini döndür"""
        self._cleanup_old_players()
        return dict(self.discovered_players)
