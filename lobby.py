"""
Lobby ekranı - Oyuncu listesi ve davet sistemi
"""
import pygame
from network.discovery import PlayerDiscovery
from network.server import GameServer
from network.client import GameClient
from network.messages import *

class Lobby:
    def __init__(self, screen, player_name="Player", on_game_start=None):
        self.screen = screen
        self.player_name = player_name
        self.on_game_start = on_game_start
        
        # Network
        self.discovery = PlayerDiscovery(player_name, tcp_port=37021)
        self.server = None
        self.client = None
        self.is_host = False
        
        # State
        self.players = {}
        self.pending_invite = None  # {"from": name, "from_ip": ip, "map_id": id}
        self.waiting_response = False
        self.countdown = None
        self.selected_map = 1
        
        # UI
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)
        
    def start(self):
        """Lobby başlat"""
        self.discovery.start()
        
        # Server başlat (host olarak)
        self.server = GameServer()
        self.server.start(self._handle_server_message)
        self.is_host = True
        
    def stop(self):
        """Lobby durdur"""
        self.discovery.stop()
        if self.server:
            self.server.stop()
        if self.client:
            self.client.disconnect()
    
    def update(self):
        """Her frame çağrılır"""
        self.players = self.discovery.get_players()
    
    def draw(self):
        """Lobby ekranını çiz"""
        self.screen.fill((30, 30, 40))
        
        # Başlık
        title = self.font.render("LOBBY - Oyuncular", True, (255, 255, 255))
        self.screen.blit(title, (50, 30))
        
        # Oyuncu listesi
        y = 100
        player_rects = []
        
        if not self.players:
            no_players = self.font_small.render("Oyuncu bulunamadi...", True, (150, 150, 150))
            self.screen.blit(no_players, (50, y))
        else:
            for ip, info in self.players.items():
                # Oyuncu kutusu
                rect = pygame.Rect(50, y, 600, 50)
                pygame.draw.rect(self.screen, (60, 60, 80), rect)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
                
                # Oyuncu ismi
                name_text = self.font_small.render(info["name"], True, (255, 255, 255))
                self.screen.blit(name_text, (70, y + 12))
                
                # Davet butonu
                if not self.waiting_response:
                    invite_rect = pygame.Rect(500, y + 10, 130, 30)
                    pygame.draw.rect(self.screen, (100, 150, 255), invite_rect)
                    pygame.draw.rect(self.screen, (255, 255, 255), invite_rect, 2)
                    invite_text = self.font_small.render("DAVET ET", True, (255, 255, 255))
                    self.screen.blit(invite_text, (510, y + 12))
                    
                    player_rects.append((invite_rect, ip, info))
                
                y += 60
        
        # Map seçimi
        map_y = self.screen.get_height() - 150
        map_text = self.font_small.render(f"Harita: Map {self.selected_map}", True, (255, 255, 255))
        self.screen.blit(map_text, (50, map_y))
        
        # Map değiştirme butonları
        prev_btn = pygame.Rect(250, map_y - 5, 40, 40)
        next_btn = pygame.Rect(300, map_y - 5, 40, 40)
        pygame.draw.rect(self.screen, (80, 80, 100), prev_btn)
        pygame.draw.rect(self.screen, (80, 80, 100), next_btn)
        pygame.draw.rect(self.screen, (255, 255, 255), prev_btn, 2)
        pygame.draw.rect(self.screen, (255, 255, 255), next_btn, 2)
        
        prev_text = self.font.render("<", True, (255, 255, 255))
        next_text = self.font.render(">", True, (255, 255, 255))
        self.screen.blit(prev_text, (260, map_y))
        self.screen.blit(next_text, (310, map_y))
        
        # Geri dön butonu
        back_btn = pygame.Rect(50, self.screen.get_height() - 70, 150, 50)
        pygame.draw.rect(self.screen, (200, 50, 50), back_btn)
        pygame.draw.rect(self.screen, (255, 255, 255), back_btn, 2)
        back_text = self.font_small.render("GERI DON", True, (255, 255, 255))
        self.screen.blit(back_text, (70, self.screen.get_height() - 58))
        
        # Gelen davet - popup çizimi ve buton return'ü
        accept_btn = None
        reject_btn = None
        if self.pending_invite:
            accept_btn, reject_btn = self._draw_invite_popup()
        
        # Bekleme mesajı
        if self.waiting_response:
            waiting_text = self.font.render("Yanit bekleniyor...", True, (255, 255, 0))
            self.screen.blit(waiting_text, (50, self.screen.get_height() - 80))
        
        # Geri sayım
        if self.countdown is not None:
            self._draw_countdown()
        
        return player_rects, prev_btn, next_btn, accept_btn, reject_btn, back_btn
    
    def _draw_invite_popup(self):
        """Davet popup'ı çiz"""
        popup_width = 500
        popup_height = 250
        popup_x = (self.screen.get_width() - popup_width) // 2
        popup_y = (self.screen.get_height() - popup_height) // 2
        
        # Overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Popup
        pygame.draw.rect(self.screen, (50, 50, 70), (popup_x, popup_y, popup_width, popup_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (popup_x, popup_y, popup_width, popup_height), 3)
        
        # Mesaj
        invite_text = self.font.render("OYUN DAVETI", True, (255, 255, 255))
        from_text = self.font_small.render(f"{self.pending_invite['from']} seni oyuna davet ediyor!", True, (200, 200, 200))
        
        self.screen.blit(invite_text, (popup_x + 120, popup_y + 40))
        self.screen.blit(from_text, (popup_x + 60, popup_y + 90))
        
        # Butonlar
        accept_btn = pygame.Rect(popup_x + 80, popup_y + 160, 150, 50)
        reject_btn = pygame.Rect(popup_x + 270, popup_y + 160, 150, 50)
        
        pygame.draw.rect(self.screen, (50, 200, 50), accept_btn)
        pygame.draw.rect(self.screen, (200, 50, 50), reject_btn)
        pygame.draw.rect(self.screen, (255, 255, 255), accept_btn, 2)
        pygame.draw.rect(self.screen, (255, 255, 255), reject_btn, 2)
        
        accept_text = self.font_small.render("KABUL ET", True, (255, 255, 255))
        reject_text = self.font_small.render("REDDET", True, (255, 255, 255))
        
        self.screen.blit(accept_text, (accept_btn.x + 20, accept_btn.y + 12))
        self.screen.blit(reject_text, (reject_btn.x + 30, reject_btn.y + 12))
        
        return accept_btn, reject_btn
    
    def _draw_countdown(self):
        """Geri sayım çiz"""
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        countdown_font = pygame.font.Font(None, 200)
        countdown_text = countdown_font.render(str(self.countdown), True, (255, 255, 0))
        countdown_rect = countdown_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        self.screen.blit(countdown_text, countdown_rect)
    
    def handle_click(self, pos, player_rects, prev_btn, next_btn, accept_btn, reject_btn, back_btn):
        """Mouse tıklama"""
        # Davet popup'ı varsa
        if self.pending_invite and accept_btn and reject_btn:
            if accept_btn.collidepoint(pos):
                self._accept_invite()
                return False
            elif reject_btn.collidepoint(pos):
                self._reject_invite()
                return False
        
        # Geri dön butonu
        if back_btn.collidepoint(pos):
            return True  # Ana menüye dön
        
        # Map butonları
        if prev_btn.collidepoint(pos):
            self.selected_map = max(1, self.selected_map - 1)
        elif next_btn.collidepoint(pos):
            self.selected_map = min(3, self.selected_map + 1)
        
        # Oyuncu davet butonları
        for rect, ip, info in player_rects:
            if rect.collidepoint(pos):
                self._send_invite(ip, info)
                break
        
        return False
    
    def _send_invite(self, target_ip, target_info):
        """Davet gönder"""
        if self.waiting_response:
            return
        
        # Client oluştur ve bağlan
        self.client = GameClient()
        if self.client.connect(target_ip, target_info["tcp_port"], self._handle_client_message):
            # Davet mesajı gönder
            msg = invite_message(self.player_name, target_ip, self.selected_map)
            self.client.send_message(msg)
            self.waiting_response = True
    
    def _accept_invite(self):
        """Daveti kabul et"""
        if not self.pending_invite:
            return
        
        # Client oluştur ve bağlan
        self.client = GameClient()
        if self.client.connect(self.pending_invite["from_ip"], 37021, self._handle_client_message):
            # Kabul mesajı gönder
            msg = invite_response_message(True, self.player_name)
            self.client.send_message(msg)
            self.is_host = False
            self.pending_invite = None
            
            # Geri sayım başlat
            self._start_countdown()
    
    def _reject_invite(self):
        """Daveti reddet"""
        self.pending_invite = None
    
    def _start_countdown(self):
        """Geri sayım başlat"""
        import threading
        
        def countdown_thread():
            for i in range(3, 0, -1):
                self.countdown = i
                pygame.time.wait(1000)
            
            # Oyunu başlat
            map_id = self.pending_invite.get("map_id") if self.pending_invite else self.selected_map
            
            if self.on_game_start:
                self.on_game_start(
                    selected_map=map_id,
                    is_host=self.is_host,
                    network_handler=self.client if not self.is_host else self.server
                )
        
        threading.Thread(target=countdown_thread, daemon=True).start()
    
    def _handle_server_message(self, msg_type, msg_data):
        """Server mesajları (host)"""
        if msg_type == MessageType.INVITE_ACCEPT:
            self.waiting_response = False
            self._start_countdown()
        elif msg_type == MessageType.INVITE_REJECT:
            self.waiting_response = False
    
    def _handle_client_message(self, msg_type, msg_data):
        """Client mesajları"""
        if msg_type == MessageType.INVITE:
            self.pending_invite = {
                "from": msg_data.get("from"),
                "from_ip": msg_data.get("from_ip"),
                "map_id": msg_data.get("map_id")
            }
