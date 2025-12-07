import pygame
import sys
import copy

from engine.map import ROWS, COLS, find_value, get_map, calculate_cell_size
from engine.bot import MazeBot
from lobby import Lobby
from game_multiplayer import MultiplayerGame
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, required=True)
args = parser.parse_args()

TCP_PORT = args.port
DISCOVERY_PORT = 37020  # Discovery için sabit port - tüm oyuncular aynı portu dinler

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY  = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
LIGHT_BLUE = (100, 150, 255)

WALL_COLOR   = (40, 40, 40)        # 1 = duvar
PATH_COLOR   = (200, 200, 200)     # 0 = yol
CHEESE_COLOR = (255, 220, 0)       # 3 = peynir

pygame.init()

# Global değişkenler
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
ASPECT_RATIO = SCREEN_WIDTH / SCREEN_HEIGHT  # 1.5 (3:2 oran)
MIN_WIDTH = 800
MIN_HEIGHT = int(MIN_WIDTH / ASPECT_RATIO)
is_fullscreen = False
CELL = 40  # Başlangıç değeri, sonra hesaplanacak

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Maze Game")

# Dinamik CELL hesaplama
CELL = calculate_cell_size(SCREEN_WIDTH, SCREEN_HEIGHT, COLS, ROWS)

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
player_name = f"Player_{TCP_PORT}"
lobby_instance = None
multiplayer_game = None

# Bot
bot_instance = None
bot_move_timer = 0
BOT_MOVE_DELAY = 200  # milisaniye

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
    global mouse_img, cheese_img, mouse_size, cheese_size, CELL
    global COLS, ROWS, bot_instance, bot_move_timer
    
    maze = get_map(selected_map)
    
    # Harita boyutuna göre CELL'i yeniden hesapla
    ROWS = len(maze)
    COLS = len(maze[0])
    CELL = calculate_cell_size(SCREEN_WIDTH, SCREEN_HEIGHT, COLS, ROWS)
    
    player_x, player_y = find_value(2, maze)
    mouse_row = player_y
    mouse_col = player_x
    move_count = 0
    game_won = False
    bot_move_timer = 0
    
    # Bot modunda yolu hesapla
    if selected_mode == "bot":
        cheese_x, cheese_y = find_value(3, maze)
        bot_instance = MazeBot(maze, (player_y, player_x), (cheese_y, cheese_x))
        if bot_instance.find_path():
            print(f"[BOT] Başlangıç: ({player_y}, {player_x})")
            print(f"[BOT] Hedef: ({cheese_y}, {cheese_x})")
            print(f"[BOT] Yol uzunluğu: {len(bot_instance.get_path())} adım")
        else:
            print("[BOT] HATA: Yol bulunamadı!")
    
    # Sprite'ları yükle
    mouse_img = pygame.image.load("assets/images/mouse.png")
    mouse_size = int(CELL * 0.8)
    mouse_img = pygame.transform.scale(mouse_img, (mouse_size, mouse_size))
    
    cheese_img = pygame.image.load("assets/images/cheese.png")
    cheese_size = int(CELL * 0.8)
    cheese_img = pygame.transform.scale(cheese_img, (cheese_size, cheese_size))

def reset_game():
    """Oyunu sıfırla"""
    global game_state, selected_mode, selected_map, lobby_instance, multiplayer_game, bot_instance
    
    # Lobby ve multiplayer temizle
    if lobby_instance:
        lobby_instance.stop()
        lobby_instance = None
    if multiplayer_game:
        multiplayer_game = None
    
    # Bot temizle
    bot_instance = None
    
    game_state = STATE_MENU_MODE
    selected_mode = None
    selected_map = None

def on_multiplayer_start(selected_map, is_host, network_handler):
    """Multiplayer oyun başladığında çağrılır"""
    global game_state, multiplayer_game
    
    multiplayer_game = MultiplayerGame(screen, selected_map, is_host, network_handler)
    game_state = STATE_GAME_MULTI
    
    # Lobby discovery'sini durdur ama bağlantıyı koru
    if lobby_instance:
        lobby_instance.discovery.stop()
        lobby_instance.countdown = None
        lobby_instance.waiting_response = False

def return_to_lobby():
    """Oyun bittiğinde lobby'ye dön"""
    global game_state, multiplayer_game
    
    if multiplayer_game:
        multiplayer_game = None
    
    if lobby_instance:
        # Lobby'yi yeni oyun için sıfırla
        lobby_instance.reset_for_new_game()
        game_state = STATE_LOBBY

# Ana oyun döngüsü
clock = pygame.time.Clock()

def handle_window_resize(width, height):
    """Pencere boyutunu güncelle - aspect ratio korunur"""
    global SCREEN_WIDTH, SCREEN_HEIGHT, CELL, screen, COLS, ROWS
    
    # En-boy oranını koruyarak yeni boyutu hesapla
    new_width = max(MIN_WIDTH, width)
    new_height = int(new_width / ASPECT_RATIO)
    
    # Eğer hesaplanan yükseklik istenen yükseklikten küçükse, yüksekliğe göre hesapla
    if new_height < height:
        new_height = max(MIN_HEIGHT, height)
        new_width = int(new_height * ASPECT_RATIO)
    
    SCREEN_WIDTH = new_width
    SCREEN_HEIGHT = new_height
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    
    # Mevcut harita varsa CELL'i yeniden hesapla
    if maze is not None:
        ROWS = len(maze)
        COLS = len(maze[0])
    CELL = calculate_cell_size(SCREEN_WIDTH, SCREEN_HEIGHT, COLS, ROWS)

def toggle_fullscreen():
    """Tam ekran modunu değiştir"""
    global SCREEN_WIDTH, SCREEN_HEIGHT, CELL, screen, is_fullscreen, COLS, ROWS
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    else:
        SCREEN_WIDTH = 1200
        SCREEN_HEIGHT = 800
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    
    # Mevcut harita varsa CELL'i yeniden hesapla
    if maze is not None:
        ROWS = len(maze)
        COLS = len(maze[0])
    CELL = calculate_cell_size(SCREEN_WIDTH, SCREEN_HEIGHT, COLS, ROWS)

while True:
    screen.fill(BLACK)
    
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            if lobby_instance:
                lobby_instance.stop()
            pygame.quit()
            sys.exit()
        
        # F11 ile tam ekran toggle
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
            toggle_fullscreen()
        
        # Pencere yeniden boyutlandırma
        elif e.type == pygame.VIDEORESIZE:
            handle_window_resize(e.w, e.h)
        
        # MOD SEÇME MENÜSÜ
        if game_state == STATE_MENU_MODE:
            if e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Buton koordinatları
                btn_width = 400
                btn_height = 80
                start_x = (SCREEN_WIDTH - btn_width) // 2
                start_y = 200
                spacing = 100
                
                btn1 = pygame.Rect(start_x, start_y, btn_width, btn_height)
                btn2 = pygame.Rect(start_x, start_y + spacing, btn_width, btn_height)
                btn3 = pygame.Rect(start_x, start_y + spacing * 2, btn_width, btn_height)
                exit_btn = pygame.Rect(start_x, start_y + spacing * 3, btn_width, btn_height)
                
                if btn1.collidepoint(mouse_pos):
                    selected_mode = "1player"
                    game_state = STATE_MENU_MAP
                elif btn2.collidepoint(mouse_pos):
                    selected_mode = "2player"
                    # Lobby'ye geç (yalnızca daha önce oluşturulmamışsa)
                    if lobby_instance is None:
                        lobby_instance = Lobby(
                            screen, 
                            player_name=player_name, 
                            on_game_start=on_multiplayer_start,
                            override_port=DISCOVERY_PORT,
                            tcp_server_port=TCP_PORT
                        )
                        lobby_instance.start()
                    game_state = STATE_LOBBY
                elif btn3.collidepoint(mouse_pos):
                    selected_mode = "bot"
                    game_state = STATE_MENU_MAP
                elif exit_btn.collidepoint(mouse_pos):
                    if lobby_instance:
                        lobby_instance.stop()
                    pygame.quit()
                    sys.exit()
        
        # MAP SEÇME MENÜSÜ
        elif game_state == STATE_MENU_MAP:
            if e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                btn_width = 400
                btn_height = 80
                start_x = (SCREEN_WIDTH - btn_width) // 2
                start_y = 250
                spacing = 100
                
                btn1 = pygame.Rect(start_x, start_y, btn_width, btn_height)
                btn2 = pygame.Rect(start_x, start_y + spacing, btn_width, btn_height)
                btn3 = pygame.Rect(start_x, start_y + spacing * 2, btn_width, btn_height)
                
                # Geri dön butonu
                back_btn = pygame.Rect(50, SCREEN_HEIGHT - 100, 150, 50)
                
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
                btn_x = (SCREEN_WIDTH - btn_width) // 2
                btn_y = SCREEN_HEIGHT // 2 + 100
                
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
                    action = multiplayer_game.handle_game_over_click(mouse_pos)
                    if action == "lobby":
                        return_to_lobby()
    
    # BOT HAREKET MANTIGI (event loop dışında - sürekli çalışır)
    if game_state == STATE_GAME and selected_mode == "bot" and not game_won:
        if bot_instance and not bot_instance.is_finished():
            bot_move_timer += clock.get_time()
            
            if bot_move_timer >= BOT_MOVE_DELAY:
                bot_move_timer = 0
                next_pos = bot_instance.get_next_move()
                
                if next_pos:
                    new_row, new_col = next_pos
                    target_value = maze[new_row][new_col]
                    
                    # Eski pozisyonu temizle
                    maze[mouse_row][mouse_col] = 0
                    
                    # Yeni pozisyona git
                    mouse_row = new_row
                    mouse_col = new_col
                    maze[mouse_row][mouse_col] = 2
                    move_count += 1
                    
                    # Peynire ulaştı mı?
                    if target_value == 3:
                        game_won = True
                        game_state = STATE_WIN
                        print(f"[BOT] Peynire ulaşıldı! {move_count} adımda")
    
    # EKRAN ÇİZİMLERİ
    if game_state == STATE_MENU_MODE:
        # Başlık
        font_title = pygame.font.Font(None, 96)
        title = font_title.render("MAZE GAME", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title, title_rect)
        
        # Butonlar
        btn_width = 400
        btn_height = 80
        start_x = (SCREEN_WIDTH - btn_width) // 2
        start_y = 200
        spacing = 100
        
        draw_button("1 Kisi", start_x, start_y, btn_width, btn_height, DARK_GRAY)
        draw_button("2 Kisi", start_x, start_y + spacing, btn_width, btn_height, DARK_GRAY)
        draw_button("Bot", start_x, start_y + spacing * 2, btn_width, btn_height, DARK_GRAY)
        draw_button("CIKIS", start_x, start_y + spacing * 3, btn_width, btn_height, (150, 50, 50))
    
    elif game_state == STATE_MENU_MAP:
        # Başlık
        font_title = pygame.font.Font(None, 96)
        title = font_title.render("HARITA SEC", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        screen.blit(title, title_rect)
        
        # Butonlar
        btn_width = 400
        btn_height = 80
        start_x = (SCREEN_WIDTH - btn_width) // 2
        start_y = 250
        spacing = 100
        
        draw_button("Map 1", start_x, start_y, btn_width, btn_height, LIGHT_BLUE)
        draw_button("Map 2", start_x, start_y + spacing, btn_width, btn_height, LIGHT_BLUE)
        draw_button("Map 3", start_x, start_y + spacing * 2, btn_width, btn_height, LIGHT_BLUE)
        
        # Geri dön butonu
        back_btn = pygame.Rect(50, SCREEN_HEIGHT - 100, 150, 50)
        pygame.draw.rect(screen, (200, 50, 50), back_btn)
        pygame.draw.rect(screen, WHITE, back_btn, 2)
        back_text = pygame.font.Font(None, 32).render("GERI DON", True, WHITE)
        screen.blit(back_text, (70, SCREEN_HEIGHT - 88))
    
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
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Metni ortala
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
            text2_rect = text2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text, text_rect)
            screen.blit(text2, text2_rect)
            
            # Devam butonu
            btn_width = 300
            btn_height = 80
            btn_x = (SCREEN_WIDTH - btn_width) // 2
            btn_y = SCREEN_HEIGHT // 2 + 100
            draw_button("DEVAM", btn_x, btn_y, btn_width, btn_height, LIGHT_BLUE)

    pygame.display.flip()
    clock.tick(60)  # 60 FPS
