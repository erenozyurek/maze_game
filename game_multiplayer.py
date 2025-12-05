"""
Multiplayer oyun modu - İki oyuncunun senkronize edildiği oyun
"""
import pygame
import copy
from engine.map import find_value, get_map
from network.messages import *

class MultiplayerGame:
    def __init__(self, screen, selected_map, is_host, network_handler):
        self.screen = screen
        self.selected_map = selected_map
        self.is_host = is_host
        self.network = network_handler
        
        # Map ve oyun durumu
        self.maze = get_map(selected_map)
        self.ROWS = len(self.maze)
        self.COLS = len(self.maze[0])
        self.CELL = 50
        
        # Oyuncular
        player_x, player_y = find_value(2, self.maze)
        
        if is_host:
            # Host = Player 1 (sol üst)
            self.my_player_id = 1
            self.my_row = player_y
            self.my_col = player_x
            
            # Player 2 pozisyonunu bul (peynirin yanı)
            cheese_x, cheese_y = find_value(3, self.maze)
            # Peynirin solundaki boş yere yerleştir
            p2_col = cheese_x - 1
            p2_row = cheese_y
            while self.maze[p2_row][p2_col] != 0:
                p2_col -= 1
            
            self.opponent_row = p2_row
            self.opponent_col = p2_col
            self.maze[p2_row][p2_col] = 4  # 4 = player 2
        else:
            # Client = Player 2
            self.my_player_id = 2
            # Host pozisyonları gönderecek, şimdilik varsayılan
            self.my_row = player_y
            self.my_col = player_x
            self.opponent_row = player_y
            self.opponent_col = player_x
        
        # Oyun durumu
        self.move_count = 0
        self.game_over = False
        self.winner = None
        
        # Sprite'lar
        self.mouse_img = pygame.image.load("assets/images/mouse.png")
        self.mouse_size = int(self.CELL * 0.8)
        self.mouse_img = pygame.transform.scale(self.mouse_img, (self.mouse_size, self.mouse_size))
        
        # Player 2 için farklı renk
        self.mouse2_img = pygame.transform.rotozoom(self.mouse_img, 0, 1.0)
        self.mouse2_img.fill((100, 200, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
        
        self.cheese_img = pygame.image.load("assets/images/cheese.png")
        self.cheese_size = int(self.CELL * 0.8)
        self.cheese_img = pygame.transform.scale(self.cheese_img, (self.cheese_size, self.cheese_size))
        
        # Renkler
        self.WALL_COLOR = (40, 40, 40)
        self.PATH_COLOR = (200, 200, 200)
        
        # Network callback
        if self.network:
            if hasattr(self.network, 'message_callback'):
                old_callback = self.network.message_callback
                self.network.message_callback = lambda t, d: self._handle_network_message(t, d, old_callback)
            else:
                # GameServer için
                self.network.message_callback = self._handle_network_message
        
        # Font
        self.font = pygame.font.Font(None, 36)
    
    def _handle_network_message(self, msg_type, msg_data, old_callback=None):
        """Network mesajlarını işle"""
        if msg_type == MessageType.PLAYER_MOVE:
            # Rakip hareketi
            if msg_data.get("player_id") != self.my_player_id:
                old_row = self.opponent_row
                old_col = self.opponent_col
                
                # Eski pozisyonu temizle
                if self.maze[old_row][old_col] == 4:
                    self.maze[old_row][old_col] = 0
                
                # Yeni pozisyon
                self.opponent_row = msg_data.get("row")
                self.opponent_col = msg_data.get("col")
                
                # Peynir kontrolü
                if self.maze[self.opponent_row][self.opponent_col] == 3:
                    self.game_over = True
                    self.winner = 2 if self.my_player_id == 1 else 1
                    self.maze[self.opponent_row][self.opponent_col] = 4
                elif self.maze[self.opponent_row][self.opponent_col] == 0:
                    self.maze[self.opponent_row][self.opponent_col] = 4
        
        elif msg_type == MessageType.GAME_END:
            self.game_over = True
            self.winner = msg_data.get("winner_id")
        
        # Eski callback varsa çağır
        if old_callback:
            old_callback(msg_type, msg_data)
    
    def handle_input(self, event):
        """Klavye girişi"""
        if self.game_over:
            return
        
        # Çarpı butonu kontrolü
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            close_btn = pygame.Rect(10, 10, 40, 40)
            if close_btn.collidepoint(mouse_pos):
                return "exit"  # Ana menüye dön sinyali
        
        if event.type == pygame.KEYDOWN:
            new_row = self.my_row
            new_col = self.my_col
            
            if event.key == pygame.K_RIGHT:
                new_col += 1
            elif event.key == pygame.K_LEFT:
                new_col -= 1
            elif event.key == pygame.K_DOWN:
                new_row += 1
            elif event.key == pygame.K_UP:
                new_row -= 1
            else:
                return
            
            # Hareket geçerli mi?
            if 0 <= new_row < self.ROWS and 0 <= new_col < self.COLS:
                target_value = self.maze[new_row][new_col]
                
                if target_value == 0 or target_value == 3:
                    # Eski pozisyonu temizle
                    self.maze[self.my_row][self.my_col] = 0
                    
                    # Yeni pozisyon
                    self.my_row = new_row
                    self.my_col = new_col
                    self.move_count += 1
                    
                    # Peynir kontrolü
                    if target_value == 3:
                        self.game_over = True
                        self.winner = self.my_player_id
                        self.maze[self.my_row][self.my_col] = 2
                        
                        # Kazandığını bildir
                        if self.network:
                            msg = game_end_message(self.my_player_id, self.move_count)
                            self.network.send_message(msg)
                    else:
                        self.maze[self.my_row][self.my_col] = 2
                    
                    # Hareketi gönder
                    if self.network:
                        msg = player_move_message(self.my_player_id, self.my_row, self.my_col, self.move_count)
                        self.network.send_message(msg)
    
    def update(self):
        """Oyun güncelleme"""
        pass
    
    def draw(self):
        """Oyunu çiz"""
        self.screen.fill((20, 20, 20))
        
        # Haritayı çiz
        for y in range(self.ROWS):
            for x in range(self.COLS):
                value = self.maze[y][x]
                
                # Zemin
                if value == 1:
                    color = self.WALL_COLOR
                else:
                    color = self.PATH_COLOR
                
                pygame.draw.rect(self.screen, color, (x * self.CELL, y * self.CELL, self.CELL, self.CELL))
                
                # Peynir
                if value == 3:
                    offset = (self.CELL - self.cheese_size) // 2
                    self.screen.blit(self.cheese_img, (x * self.CELL + offset, y * self.CELL + offset))
                
                # Player 1
                if value == 2:
                    offset = (self.CELL - self.mouse_size) // 2
                    self.screen.blit(self.mouse_img, (x * self.CELL + offset, y * self.CELL + offset))
                
                # Player 2
                if value == 4:
                    offset = (self.CELL - self.mouse_size) // 2
                    self.screen.blit(self.mouse2_img, (x * self.CELL + offset, y * self.CELL + offset))
        
        # Çarpı butonu (sol üst) - oyun devam ediyorsa
        if not self.game_over:
            close_btn = pygame.Rect(10, 10, 40, 40)
            pygame.draw.rect(self.screen, (200, 50, 50), close_btn)
            pygame.draw.rect(self.screen, (255, 255, 255), close_btn, 2)
            
            # X çiz
            pygame.draw.line(self.screen, (255, 255, 255), (15, 15), (45, 45), 3)
            pygame.draw.line(self.screen, (255, 255, 255), (45, 15), (15, 45), 3)
        
        # HUD
        player_text = self.font.render(f"Siz: Player {self.my_player_id}  |  Hamle: {self.move_count}", True, (255, 255, 255))
        self.screen.blit(player_text, (60, 10))
        
        # Game Over
        if self.game_over:
            self._draw_game_over()
    
    def _draw_game_over(self):
        """Oyun sonu ekranı"""
        overlay = pygame.Surface((self.COLS * self.CELL, self.ROWS * self.CELL))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        font_big = pygame.font.Font(None, 74)
        
        if self.winner == self.my_player_id:
            text = font_big.render(f"KAZANDINIZ!", True, (50, 255, 50))
        else:
            text = font_big.render(f"Player {self.winner} Kazandi!", True, (255, 50, 50))
        
        text2 = self.font.render(f"{self.move_count} hamlede tamamlandi", True, (255, 255, 255))
        
        text_rect = text.get_rect(center=(self.COLS * self.CELL // 2, self.ROWS * self.CELL // 2 - 40))
        text2_rect = text2.get_rect(center=(self.COLS * self.CELL // 2, self.ROWS * self.CELL // 2 + 40))
        
        self.screen.blit(text, text_rect)
        self.screen.blit(text2, text2_rect)
        
        # Ana menü butonu
        btn_width = 300
        btn_height = 60
        btn_x = (self.COLS * self.CELL - btn_width) // 2
        btn_y = self.ROWS * self.CELL // 2 + 120
        
        btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.screen, (100, 150, 255), btn_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 3)
        
        btn_text = self.font.render("ANA MENU", True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=(btn_x + btn_width // 2, btn_y + btn_height // 2))
        self.screen.blit(btn_text, btn_text_rect)
        
        return btn_rect
    
    def handle_game_over_click(self, pos):
        """Game over ekranında tıklama"""
        if self.game_over:
            btn_rect = self._draw_game_over()
            if btn_rect.collidepoint(pos):
                return True  # Ana menüye dön
        return False
