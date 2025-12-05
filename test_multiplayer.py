"""
Multiplayer test senaryosu
Tek bilgisayarda iki oyuncu simülasyonu
"""

import subprocess
import time
import sys

def test_scenario():
    print("=== MAZE GAME MULTIPLAYER TEST ===\n")
    
    print("Test Senaryosu:")
    print("1. İki terminal açılacak")
    print("2. Host oyuncu (Terminal 1): Ana menü > '2 Kisi' > Lobby'de bekle")
    print("3. Client oyuncu (Terminal 2): Ana menü > '2 Kisi' > Host'u gör > Davet gönder")
    print("4. Host: Daveti kabul et")
    print("5. 3-2-1 geri sayım")
    print("6. Oyun başlar - Her iki oyuncu ok tuşları ile hareket eder")
    print("7. İlk peynire ulaşan kazanır")
    print("\n" + "="*50 + "\n")
    
    print("Manuel Test Adımları:")
    print("\n[Terminal 1 - Host]")
    print("  $ cd /Users/erenozyurek/maze_game")
    print("  $ source .venv/bin/activate")
    print("  $ python main.py")
    print("  > Ana menüde '2 Kisi' butonuna tıkla")
    print("  > Lobby ekranında bekle")
    print("  > Davet gelince 'KABUL ET' tıkla")
    print("  > Ok tuşları ile oyna\n")
    
    print("[Terminal 2 - Client]")
    print("  $ cd /Users/erenozyurek/maze_game")
    print("  $ source .venv/bin/activate")
    print("  $ python main.py")
    print("  > Ana menüde '2 Kisi' butonuna tıkla")
    print("  > Lobby'de Host oyuncuyu gör")
    print("  > 'DAVET ET' butonuna tıkla")
    print("  > Geri sayımı bekle")
    print("  > Ok tuşları ile oyna\n")
    
    print("="*50)
    print("\nNetwork Detayları:")
    print("  - Discovery: UDP Port 37020 (Broadcast)")
    print("  - Game: TCP Port 37021")
    print("  - Protocol: JSON mesajlar")
    print("  - Update Rate: 60 FPS")
    print("\nBeklenen Davranış:")
    print("  ✓ Lobby'de karşı oyuncu 2 saniye içinde görünür")
    print("  ✓ Davet popup'ı anında görünür")
    print("  ✓ Kabul sonrası 3 saniyelik geri sayım")
    print("  ✓ İki fare ekranda (biri normal, biri mavi)")
    print("  ✓ Her hareket anında senkronize")
    print("  ✓ Peynir bulan kazanır mesajı görür")
    print("\nOlası Sorunlar:")
    print("  ✗ Firewall UDP/TCP portları engelliyor")
    print("  ✗ Aynı ağda değilsiniz")
    print("  ✗ Port zaten kullanımda")
    print("\nÇözümler:")
    print("  → Firewall'u kapatın veya portları açın")
    print("  → 'netstat -an | grep 37020' ile port kontrolü")
    print("  → Logs için terminal çıktısına bakın")

if __name__ == "__main__":
    test_scenario()
