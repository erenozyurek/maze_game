"""
Lobby ekranı - Oyuncu listesi ve davet sistemi
"""
import pygame
import socket
from network.discovery import PlayerDiscovery
from network.server import GameServer
from network.client import GameClient
from network.messages import *


class Lobby:
    def __init__(self, screen, player_name="Player", on_game_start=None,
                 override_mode=None, override_port=None, tcp_server_port=None):
        """
        override_mode: "host" veya "join"
        override_port: discovery port (int)
        tcp_server_port: TCP server port (int)
        """
        self.screen = screen
        self.player_name = player_name
        self.on_game_start = on_game_start

        # DISCOVERY PORT override
        self.discovery_port = override_port if override_port else 37020
        self.tcp_port = tcp_server_port if tcp_server_port else 37021

        # Discovery başlat
        self.discovery = PlayerDiscovery(
            player_name,
            tcp_port=self.tcp_port,
            discovery_port=self.discovery_port
        )

        # Mode override
        self.override_mode = override_mode
        self.is_host = (override_mode == "host")

        # Server / Client
        self.server = None
        self.client = None

        # State
        self.players = {}
        self.pending_invite = None
        self.waiting_response = False
        self.countdown = None
        self.selected_map = 1

        # UI
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)

    def start(self):
        """Lobby başlat."""
        self.discovery.start()

        # Her oyuncu kendi server'ını açar (davet alabilmek için)
        self.server = GameServer(port=self.tcp_port)
        self.server.start(self._handle_server_message)
        print(f"[LOBBY] Server başlatıldı: port {self.tcp_port}")

    def reset_for_new_game(self):
        """Yeni oyun için lobby'yi sıfırla."""
        self.pending_invite = None
        self.waiting_response = False
        self.countdown = None

        if not self.discovery.running:
            self.discovery.start()

    def stop(self):
        self.discovery.stop()
        if self.server:
            self.server.stop()
        if self.client:
            self.client.disconnect()

    def update(self):
        self.players = self.discovery.get_players()

    def draw(self):
        self.screen.fill((30, 30, 40))

        title = self.font.render("LOBBY - Oyuncular", True, (255, 255, 255))
        self.screen.blit(title, (50, 30))

        # Oyuncu listesi
        y = 100
        player_rects = []

        if not self.players:
            no_players = self.font_small.render("Oyuncu bulunamadı...", True, (150, 150, 150))
            self.screen.blit(no_players, (50, y))
        else:
            for ip, info in self.players.items():
                rect = pygame.Rect(50, y, 600, 50)
                pygame.draw.rect(self.screen, (60, 60, 80), rect)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)

                name_text = self.font_small.render(info["name"], True, (255, 255, 255))
                self.screen.blit(name_text, (70, y + 12))

                if not self.waiting_response:
                    invite_rect = pygame.Rect(500, y + 10, 130, 30)
                    pygame.draw.rect(self.screen, (100, 150, 255), invite_rect)
                    pygame.draw.rect(self.screen, (255, 255, 255), invite_rect, 2)
                    invite_text = self.font_small.render("DAVET ET", True, (255, 255, 255))
                    self.screen.blit(invite_text, (510, y + 12))
                    player_rects.append((invite_rect, ip, info))

                y += 60

        # Map
        map_y = self.screen.get_height() - 150
        map_text = self.font_small.render(f"Harita: Map {self.selected_map}", True, (255, 255, 255))
        self.screen.blit(map_text, (50, map_y))

        prev_btn = pygame.Rect(250, map_y - 5, 40, 40)
        next_btn = pygame.Rect(300, map_y - 5, 40, 40)

        for btn in [prev_btn, next_btn]:
            pygame.draw.rect(self.screen, (80, 80, 100), btn)
            pygame.draw.rect(self.screen, (255, 255, 255), btn, 2)

        self.screen.blit(self.font.render("<", True, (255, 255, 255)), (260, map_y))
        self.screen.blit(self.font.render(">", True, (255, 255, 255)), (310, map_y))

        # Back
        back_btn = pygame.Rect(50, self.screen.get_height() - 70, 150, 50)
        pygame.draw.rect(self.screen, (200, 50, 50), back_btn)
        pygame.draw.rect(self.screen, (255, 255, 255), back_btn, 2)
        self.screen.blit(self.font_small.render("GERİ DÖN", True, (255, 255, 255)),
                         (70, self.screen.get_height() - 58))

        # Invite popup
        accept_btn = None
        reject_btn = None
        if self.pending_invite:
            accept_btn, reject_btn = self._draw_invite_popup()

        # Bekleme
        if self.waiting_response:
            waiting_text = self.font.render("Yanıt bekleniyor...", True, (255, 255, 0))
            self.screen.blit(waiting_text, (50, self.screen.get_height() - 80))

        # Countdown
        if self.countdown is not None:
            self._draw_countdown()

        return player_rects, prev_btn, next_btn, accept_btn, reject_btn, back_btn

    def _draw_invite_popup(self):
        popup_width = 500
        popup_height = 250
        popup_x = (self.screen.get_width() - popup_width) // 2
        popup_y = (self.screen.get_height() - popup_height) // 2

        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen, (50, 50, 70), (popup_x, popup_y, popup_width, popup_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (popup_x, popup_y, popup_width, popup_height), 3)

        invite_text = self.font.render("OYUN DAVETİ", True, (255, 255, 255))
        from_text = self.font_small.render(
            f"{self.pending_invite['from']} seni oyuna davet ediyor!",
            True,
            (200, 200, 200)
        )

        self.screen.blit(invite_text, (popup_x + 120, popup_y + 40))
        self.screen.blit(from_text, (popup_x + 60, popup_y + 90))

        accept_btn = pygame.Rect(popup_x + 80, popup_y + 160, 150, 50)
        reject_btn = pygame.Rect(popup_x + 270, popup_y + 160, 150, 50)

        pygame.draw.rect(self.screen, (50, 200, 50), accept_btn)
        pygame.draw.rect(self.screen, (200, 50, 50), reject_btn)
        pygame.draw.rect(self.screen, (255, 255, 255), accept_btn, 2)
        pygame.draw.rect(self.screen, (255, 255, 255), reject_btn, 2)

        self.screen.blit(self.font_small.render("KABUL ET", True, (255, 255, 255)),
                         (accept_btn.x + 20, accept_btn.y + 12))
        self.screen.blit(self.font_small.render("REDDET", True, (255, 255, 255)),
                         (reject_btn.x + 30, reject_btn.y + 12))

        return accept_btn, reject_btn

    def _draw_countdown(self):
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        countdown_font = pygame.font.Font(None, 200)
        countdown_text = countdown_font.render(str(self.countdown), True, (255, 255, 0))
        countdown_rect = countdown_text.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() // 2)
        )
        self.screen.blit(countdown_text, countdown_rect)

    def handle_click(self, pos, player_rects, prev_btn, next_btn, accept_btn, reject_btn, back_btn):
        if self.pending_invite and accept_btn and reject_btn:
            if accept_btn.collidepoint(pos):
                self._accept_invite()
                return False
            elif reject_btn.collidepoint(pos):
                self._reject_invite()
                return False

        if back_btn.collidepoint(pos):
            return True

        if prev_btn.collidepoint(pos):
            self.selected_map = max(1, self.selected_map - 1)
        elif next_btn.collidepoint(pos):
            self.selected_map = min(3, self.selected_map + 1)

        for rect, ip, info in player_rects:
            if rect.collidepoint(pos):
                self._send_invite(ip, info)
                break

        return False

    def _send_invite(self, target_ip, target_info):
        if self.waiting_response:
            return

        print(f"[LOBBY] Davet gönderiliyor: {target_ip}:{target_info['tcp_port']}")
        
        temp_client = GameClient()
        if temp_client.connect(target_ip, target_info["tcp_port"], lambda t, d: None):
            my_ip = socket.gethostbyname(socket.gethostname())
            msg = invite_message(self.player_name, my_ip, self.selected_map, self.tcp_port)
            temp_client.send_message(msg)
            temp_client.disconnect()

            self.waiting_response = True
            print(f"[LOBBY] Davet gönderildi: {target_info['name']}")
        else:
            print(f"[LOBBY] Davet gönderilemedi: {target_ip}:{target_info['tcp_port']}")

    def _accept_invite(self):
        if not self.pending_invite:
            return

        target_ip = self.pending_invite["from_ip"]
        target_port = self.pending_invite.get("from_tcp_port", 37021)
        
        print(f"[LOBBY] Daveti kabul ediyorum: {target_ip}:{target_port}")
        
        self.client = GameClient()
        if self.client.connect(target_ip, target_port, self._handle_client_message):
            msg = invite_response_message(True, self.player_name)
            self.client.send_message(msg)
            self.is_host = False

            map_id = self.pending_invite["map_id"]
            self.pending_invite = None
            self._start_countdown(map_id)
        else:
            print(f"[LOBBY] Bağlantı başarısız: {target_ip}:{target_port}")
            self.pending_invite = None

    def _reject_invite(self):
        self.pending_invite = None

    def _start_countdown(self, map_id=None):
        import threading

        if map_id is None:
            map_id = self.selected_map

        def countdown_thread():
            for i in range(3, 0, -1):
                self.countdown = i
                pygame.time.wait(1000)

            self.countdown = None

            if self.on_game_start:
                self.on_game_start(
                    selected_map=map_id,
                    is_host=self.is_host,
                    network_handler=self.server if self.is_host else self.client
                )

        threading.Thread(target=countdown_thread, daemon=True).start()

    def _handle_server_message(self, msg_type, msg_data):
        print(f"[LOBBY-SERVER] Mesaj alındı: {msg_type}")
        
        if msg_type == MessageType.INVITE_ACCEPT:
            self.waiting_response = False
            self.is_host = True
            self._start_countdown()
            print("[LOBBY-SERVER] Davet kabul edildi, oyun başlıyor")

        elif msg_type == MessageType.INVITE_REJECT:
            self.waiting_response = False
            print("[LOBBY-SERVER] Davet reddedildi")

        elif msg_type == MessageType.INVITE:
            print(f"[LOBBY-SERVER] Davet geldi: {msg_data}")
            self.pending_invite = {
                "from": msg_data.get("from"),
                "from_ip": msg_data.get("from_ip"),
                "from_tcp_port": msg_data.get("from_tcp_port", 37021),
                "map_id": msg_data.get("map_id", 1)
            }

    def _handle_client_message(self, msg_type, msg_data):
        print(f"[LOBBY-CLIENT] Mesaj alındı: {msg_type}")
        
        if msg_type == MessageType.INVITE:
            print(f"[LOBBY-CLIENT] Davet geldi: {msg_data}")
            self.pending_invite = {
                "from": msg_data.get("from"),
                "from_ip": msg_data.get("from_ip"),
                "from_tcp_port": msg_data.get("from_tcp_port", 37021),
                "map_id": msg_data.get("map_id", 1)
            }
        elif msg_type == MessageType.GAME_START:
            print("[LOBBY-CLIENT] Oyun başlıyor")
        elif msg_type == "disconnected":
            print("[LOBBY-CLIENT] Bağlantı kesildi")
