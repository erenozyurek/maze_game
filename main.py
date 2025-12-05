import pygame
import sys
import copy

from engine.map import ROWS, COLS, CELL, find_value, get_map
from lobby import Lobby
from game_multiplayer import MultiplayerGame

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY  = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
LIGHT_BLUE = (100, 150, 255)

WALL_COLOR   = (40, 40, 40)        # 1 = duvar
PATH_COLOR   = (200, 200, 200)     # 0 = yol
CHEESE_COLOR = (255, 220, 0)       # 3 = peynir

pygame.init()

screen = pygame.display.set_mode((COLS * CELL, ROWS * CELL))
pygame.display.set_caption("Maze Game")

# Oyun durumları
STATE_MENU_MODE = "menu_mode"      # 1 kişi, 2 kişi, bot seçimi
STATE_MENU_MAP = "menu_map"        # Map seçimi (tek oyuncu)
STATE_LOBBY = "lobby"              # Multiplayer lobby
STATE_GAME = "game"                # Tek oyuncu oyun
STATE_GAME_MULTI = "game_multi"    # Multiplayer oyun
STATE_WIN = "win"                  # Kazanma ekranı

# Oyun değişkenleri
game_state = STATE_MENU_MODE
selected_mode = None  # "1player", "2player", "bot"
selected_map = None   # 1, 2, 3
maze = None
mouse_row = None
mouse_col = None
move_count = 0
game_won = False
mouse_img = None
cheese_img = None
mouse_size = 0
cheese_size = 0

# Multiplayer
lobby_instance = None
multiplayer_game = None

def draw_button(text, x, y, width, height, color, text_color=WHITE):
    """Buton çiz ve tıklandı mı kontrol et"""
    pygame.draw.rect(screen, color, (x, y, width, height))
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 3)
    
    font = pygame.font.Font(None, 48)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surf, text_rect)
    
    return pygame.Rect(x, y, width, height)

def init_game():
    """Oyunu başlat"""
    global maze, mouse_row, mouse_col, move_count, game_won
    global mouse_img, cheese_img, mouse_size, cheese_size
    
    maze = get_map(selected_map)
    player_x, player_y = find_value(2, maze)
    mouse_row = player_y
    mouse_col = player_x
    move_count = 0
    game_won = False
    
    # Sprite'ları yükle
    mouse_img = pygame.image.load("assets/images/mouse.png")
    mouse_size = int(CELL * 0.8)
    mouse_img = pygame.transform.scale(mouse_img, (mouse_size, mouse_size))
    
    cheese_img = pygame.image.load("assets/images/cheese.png")
    cheese_size = int(CELL * 0.8)
    cheese_img = pygame.transform.scale(cheese_img, (cheese_size, cheese_size))

def reset_game():
    """Oyunu sıfırla"""
    global game_state, selected_mode, selected_map, lobby_instance, multiplayer_game
    
    # Lobby ve multiplayer temizle
    if lobby_instance:
        lobby_instance.stop()
        lobby_instance = None
    if multiplayer_game:
        multiplayer_game = None
    
    game_state = STATE_MENU_MODE
    selected_mode = None
    selected_map = None

def on_multiplayer_start(selected_map, is_host, network_handler):
    """Multiplayer oyun başladığında çağrılır"""
    global game_state, multiplayer_game, lobby_instance
    
    multiplayer_game = MultiplayerGame(screen, selected_map, is_host, network_handler)
    game_state = STATE_GAME_MULTI
    
    # Lobby'yi durdur ama bağlantıyı koru
    if lobby_instance:
        lobby_instance.discovery.stop()

# Ana oyun döngüsü
clock = pygame.time.Clock()

while True:
    screen.fill(BLACK)
    
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            if lobby_instance:
                lobby_instance.stop()
            pygame.quit()
            sys.exit()
        
        # MOD SEÇME MENÜSÜ
        if game_state == STATE_MENU_MODE:
            if e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Buton koordinatları
                btn_width = 400
                btn_height = 80
                start_x = (COLS * CELL - btn_width) // 2
                start_y = 200
                spacing = 100
                
                btn1 = pygame.Rect(start_x, start_y, btn_width, btn_height)
                btn2 = pygame.Rect(start_x, start_y + spacing, btn_width, btn_height)
                btn3 = pygame.Rect(start_x, start_y + spacing * 2, btn_width, btn_height)
                
                if btn1.collidepoint(mouse_pos):
                    selected_mode = "1player"
                    game_state = STATE_MENU_MAP
                elif btn2.collidepoint(mouse_pos):
                    selected_mode = "2player"
                    # Lobby'ye geç
                    lobby_instance = Lobby(screen, player_name="Player", on_game_start=on_multiplayer_start)
                    lobby_instance.start()
                    game_state = STATE_LOBBY
                elif btn3.collidepoint(mouse_pos):
                    selected_mode = "bot"
                    game_state = STATE_MENU_MAP
        
        # MAP SEÇME MENÜSÜ
        elif game_state == STATE_MENU_MAP:
            if e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                btn_width = 400
                btn_height = 80
                start_x = (COLS * CELL - btn_width) // 2
                start_y = 250
                spacing = 100
                
                btn1 = pygame.Rect(start_x, start_y, btn_width, btn_height)
                btn2 = pygame.Rect(start_x, start_y + spacing, btn_width, btn_height)
                btn3 = pygame.Rect(start_x, start_y + spacing * 2, btn_width, btn_height)
                
                # Geri dön butonu
                back_btn = pygame.Rect(50, ROWS * CELL - 100, 150, 50)
                
                if back_btn.collidepoint(mouse_pos):
                    game_state = STATE_MENU_MODE
                    selected_mode = None
                elif btn1.collidepoint(mouse_pos):
                    selected_map = 1
                    init_game()
                    game_state = STATE_GAME
                elif btn2.collidepoint(mouse_pos):
                    selected_map = 2
                    init_game()
                    game_state = STATE_GAME
                elif btn3.collidepoint(mouse_pos):
                    selected_map = 3
                    init_game()
                    game_state = STATE_GAME
        
        # OYUN
        elif game_state == STATE_GAME and not game_won:
            # Çarpı butonu (sol üst)
            if e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                close_btn = pygame.Rect(10, 10, 40, 40)
                if close_btn.collidepoint(mouse_pos):
                    reset_game()
                    continue
            
            if e.type == pygame.KEYDOWN:
                new_row = mouse_row
                new_col = mouse_col
                
                # Yön tuşlarına göre yeni pozisyon hesapla
                if e.key == pygame.K_RIGHT:
                    new_col += 1
                elif e.key == pygame.K_LEFT:
                    new_col -= 1
                elif e.key == pygame.K_DOWN:
                    new_row += 1
                elif e.key == pygame.K_UP:
                    new_row -= 1
                
                # Yeni pozisyonu kontrol et
                rows = len(maze)
                cols = len(maze[0])
                if 0 <= new_row < rows and 0 <= new_col < cols:
                    target_value = maze[new_row][new_col]
                    
                    # Peynir bulundu mu?
                    if target_value == 3:
                        move_count += 1
                        game_won = True
                        game_state = STATE_WIN
                        # Eski konumdaki fareyi temizle
                        maze[mouse_row][mouse_col] = 0
                        # Yeni konuma fareyi yerleştir
                        mouse_row = new_row
                        mouse_col = new_col
                        maze[mouse_row][mouse_col] = 2
                    
                    # Yol mu? (0 = yol)
                    elif target_value == 0:
                        move_count += 1
                        # Eski konumdaki fareyi temizle
                        maze[mouse_row][mouse_col] = 0
                        # Yeni konuma fareyi yerleştir
                        mouse_row = new_row
                        mouse_col = new_col
                        maze[mouse_row][mouse_col] = 2
        
        # KAZANMA EKRANI (tek oyuncu)
        elif game_state == STATE_WIN:
            if e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                btn_width = 300
                btn_height = 80
                btn_x = (COLS * CELL - btn_width) // 2
                btn_y = ROWS * CELL // 2 + 100
                
                continue_btn = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
                
                if continue_btn.collidepoint(mouse_pos):
                    reset_game()
        
        # LOBBY
        elif game_state == STATE_LOBBY:
            if e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if lobby_instance:
                    player_rects, prev_btn, next_btn, accept_btn, reject_btn, back_btn = lobby_instance.draw()
                    should_exit = lobby_instance.handle_click(mouse_pos, player_rects, prev_btn, next_btn, accept_btn, reject_btn, back_btn)
                    if should_exit:
                        reset_game()
        
        # MULTIPLAYER OYUN
        elif game_state == STATE_GAME_MULTI:
            if multiplayer_game:
                result = multiplayer_game.handle_input(e)
                
                # Çarpı butonuna basıldı
                if result == "exit":
                    reset_game()
                    continue
                
                if e.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if multiplayer_game.handle_game_over_click(mouse_pos):
                        reset_game()
    
    # EKRAN ÇİZİMLERİ
    if game_state == STATE_MENU_MODE:
        # Başlık
        font_title = pygame.font.Font(None, 96)
        title = font_title.render("MAZE GAME", True, WHITE)
        title_rect = title.get_rect(center=(COLS * CELL // 2, 100))
        screen.blit(title, title_rect)
        
        # Butonlar
        btn_width = 400
        btn_height = 80
        start_x = (COLS * CELL - btn_width) // 2
        start_y = 200
        spacing = 100
        
        draw_button("1 Kisi", start_x, start_y, btn_width, btn_height, DARK_GRAY)
        draw_button("2 Kisi", start_x, start_y + spacing, btn_width, btn_height, DARK_GRAY)
        draw_button("Bot", start_x, start_y + spacing * 2, btn_width, btn_height, DARK_GRAY)
    
    elif game_state == STATE_MENU_MAP:
        # Başlık
        font_title = pygame.font.Font(None, 96)
        title = font_title.render("HARITA SEC", True, WHITE)
        title_rect = title.get_rect(center=(COLS * CELL // 2, 120))
        screen.blit(title, title_rect)
        
        # Butonlar
        btn_width = 400
        btn_height = 80
        start_x = (COLS * CELL - btn_width) // 2
        start_y = 250
        spacing = 100
        
        draw_button("Map 1", start_x, start_y, btn_width, btn_height, LIGHT_BLUE)
        draw_button("Map 2", start_x, start_y + spacing, btn_width, btn_height, LIGHT_BLUE)
        draw_button("Map 3", start_x, start_y + spacing * 2, btn_width, btn_height, LIGHT_BLUE)
        
        # Geri dön butonu
        back_btn = pygame.Rect(50, ROWS * CELL - 100, 150, 50)
        pygame.draw.rect(screen, (200, 50, 50), back_btn)
        pygame.draw.rect(screen, WHITE, back_btn, 2)
        back_text = pygame.font.Font(None, 32).render("GERI DON", True, WHITE)
        screen.blit(back_text, (70, ROWS * CELL - 88))
    
    elif game_state == STATE_LOBBY:
        # Lobby ekranı
        if lobby_instance:
            lobby_instance.update()
            lobby_instance.draw()
    
    elif game_state == STATE_GAME_MULTI:
        # Multiplayer oyun
        if multiplayer_game:
            multiplayer_game.update()
            multiplayer_game.draw()
    
    elif game_state == STATE_GAME or game_state == STATE_WIN:
        # Haritayı çiz
        rows = len(maze)
        cols = len(maze[0])
        for y in range(rows):
            for x in range(cols):
                value = maze[y][x]

                # Önce zemini çiz
                if value == 1:
                    color = WALL_COLOR
                else:
                    color = PATH_COLOR

                pygame.draw.rect(
                    screen,
                    color,
                    (x * CELL, y * CELL, CELL, CELL)
                )

                # Peynir varsa
                if value == 3:
                    # Peyniri hücrenin tam ortasına yerleştir
                    offset = (CELL - cheese_size) // 2
                    screen.blit(cheese_img, (x * CELL + offset, y * CELL + offset))

                # FARE (sprite)
                if value == 2 or (y == mouse_row and x == mouse_col):
                    # Fareyi hücrenin tam ortasına yerleştir
                    offset = (CELL - mouse_size) // 2
                    screen.blit(mouse_img, (x * CELL + offset, y * CELL + offset))
        
        # Çarpı butonu (sol üst) - oyun devam ediyorsa
        if game_state == STATE_GAME and not game_won:
            close_btn = pygame.Rect(10, 10, 40, 40)
            pygame.draw.rect(screen, (200, 50, 50), close_btn)
            pygame.draw.rect(screen, WHITE, close_btn, 2)
            
            # X çiz
            pygame.draw.line(screen, WHITE, (15, 15), (45, 45), 3)
            pygame.draw.line(screen, WHITE, (45, 15), (15, 45), 3)
        
        # Kazanma ekranı göster
        if game_state == STATE_WIN:
            font = pygame.font.Font(None, 74)
            text = font.render(f"Tebrikler! {move_count} hamlede", True, WHITE)
            text2 = font.render("peyniri buldunuz!", True, WHITE)
            
            # Yarı saydam siyah arka plan
            overlay = pygame.Surface((COLS * CELL, ROWS * CELL))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Metni ortala
            text_rect = text.get_rect(center=(COLS * CELL // 2, ROWS * CELL // 2 - 60))
            text2_rect = text2.get_rect(center=(COLS * CELL // 2, ROWS * CELL // 2))
            screen.blit(text, text_rect)
            screen.blit(text2, text2_rect)
            
            # Devam butonu
            btn_width = 300
            btn_height = 80
            btn_x = (COLS * CELL - btn_width) // 2
            btn_y = ROWS * CELL // 2 + 100
            draw_button("DEVAM", btn_x, btn_y, btn_width, btn_height, LIGHT_BLUE)

    pygame.display.flip()
    clock.tick(60)  # 60 FPS
