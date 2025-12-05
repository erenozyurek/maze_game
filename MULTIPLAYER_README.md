# Maze Game - Multiplayer Dokümantasyonu

## Klasör Yapısı

```
maze_game/
├── main.py                 # Ana oyun döngüsü
├── lobby.py               # Multiplayer lobby ekranı
├── game_multiplayer.py    # Multiplayer oyun modu
├── engine/
│   ├── __init__.py
│   ├── map.py            # Harita tanımları (maze1, maze2, maze3)
│   └── ...
├── network/
│   ├── __init__.py
│   ├── messages.py       # Mesaj formatları ve protokol
│   ├── discovery.py      # UDP broadcast ile oyuncu keşfi
│   ├── server.py         # TCP server (host)
│   └── client.py         # TCP client (bağlanan oyuncu)
└── assets/
    └── images/
        ├── mouse.png
        └── cheese.png
```

## Mimari ve Akış

### 1. Network Katmanı

**discovery.py** - UDP Broadcast (Port 37020)
- Her 2 saniyede bir varlığını broadcast eder
- Diğer oyuncuları dinler ve listeler
- 5 saniye görünmeyen oyuncuları listeden çıkarır

**server.py** - TCP Server (Port 37021)
- Host oyuncu için server açar
- Bir client bağlantısı kabul eder
- Mesajları callback ile iletir

**client.py** - TCP Client
- Bağlanan oyuncu için client oluşturur
- Server'a bağlanır ve mesaj alışverişi yapar

**messages.py** - Protokol
- JSON formatında mesajlar
- MessageType sabitleri: DISCOVER, ANNOUNCE, INVITE, INVITE_ACCEPT, GAME_START, PLAYER_MOVE, GAME_END
- Her mesaj: `{"type": "...", "data": {...}}`

### 2. Lobby Sistemi

**lobby.py**
- Discovery başlatır
- Oyuncuları listeler
- Davet gönderme/alma
- Kabul/Ret popup'ı
- 3 saniyelik geri sayım
- Oyun başlatma callback'i

### 3. Multiplayer Oyun

**game_multiplayer.py**
- İki oyuncu senkronizasyonu
- Player 1 (host): Sol üst başlangıç
- Player 2 (client): Peynir yakını başlangıç
- Gerçek zamanlı konum güncellemeleri (60 FPS)
- Kazanan belirleme ve game over

## Protokol Detayları

### Discovery Akışı
```
[Oyuncu A] --ANNOUNCE--> [Broadcast]
[Oyuncu B] --ANNOUNCE--> [Broadcast]
Her oyuncu diğerlerini görür
```

### Davet Akışı
```
[Host] --INVITE--> [Client]
[Client] --INVITE_ACCEPT/REJECT--> [Host]
```

### Oyun Akışı
```
[Player 1] --PLAYER_MOVE--> [Player 2]
[Player 2] --PLAYER_MOVE--> [Player 1]
...
[Kazanan] --GAME_END--> [Diğer]
```

## Test Senaryosu

### Senaryo 1: Aynı Bilgisayarda Test (localhost)

1. **Terminal 1 - Host Oyuncu:**
   ```bash
   cd /Users/erenozyurek/maze_game
   source .venv/bin/activate
   python main.py
   ```
   - Ana menüde "2 Kisi" seç
   - Lobby açılır, discovery başlar

2. **Terminal 2 - Client Oyuncu:**
   ```bash
   cd /Users/erenozyurek/maze_game
   source .venv/bin/activate
   python main.py
   ```
   - Ana menüde "2 Kisi" seç
   - Lobby'de diğer oyuncuyu görürsün
   - "DAVET ET" butonuna tıkla

3. **Host Terminal:**
   - Davet popup'ı görünür
   - "KABUL ET" tıkla

4. **Her iki tarafta:**
   - 3-2-1 geri sayım başlar
   - Oyun başlar
   - İki fare (biri mavi) görünür
   - Ok tuşları ile hareket et
   - İlk peynire ulaşan kazanır

### Senaryo 2: Farklı Bilgisayarlarda Test (aynı ağ)

1. **Bilgisayar A (Host):**
   - Oyunu başlat, "2 Kisi" seç
   - Lobby'de bekle

2. **Bilgisayar B (Client):**
   - Oyunu başlat, "2 Kisi" seç
   - Lobby'de Bilgisayar A'yı gör
   - Davet gönder

3. **Bilgisayar A:**
   - Daveti kabul et

4. **Oyun başlar:**
   - Her iki tarafta senkronize hareket
   - Gerçek zamanlı multiplayer

## Port Kullanımı

- **UDP 37020**: Discovery broadcast
- **TCP 37021**: Oyun bağlantısı

## Önemli Notlar

### Senkronizasyon
- Her hareket anında karşı tarafa gönderilir
- Mesajlar newline (`\n`) ile ayrılır
- Buffer sistemi ile çoklu mesaj desteği

### Performans
- 60 FPS hedeflenir
- Network mesajları non-blocking
- Thread'ler daemon olarak çalışır

### Hata Yönetimi
- Bağlantı kopması durumunda "disconnected" callback
- Timeout mekanizmaları mevcut
- Try-catch ile istikrarlı çalışma

## Genişletme Önerileri

1. **Ping/Latency göstergesi**: RTT hesaplama ekle
2. **Reconnect**: Bağlantı koptuğunda yeniden bağlan
3. **Spectator modu**: Üçüncü oyuncular izleyebilsin
4. **Chat sistemi**: Oyun içi mesajlaşma
5. **Replay sistemi**: Oyunları kaydet ve tekrar oynat
6. **Matchmaking**: Otomatik eşleştirme
7. **Leaderboard**: Online skor tablosu

## Sorun Giderme

### "Oyuncu bulunamadı"
- Firewall UDP 37020'yi engelliyor olabilir
- Aynı ağda olduğunuzdan emin olun
- Broadcast desteği var mı kontrol edin

### "Bağlantı hatası"
- Firewall TCP 37021'i engelliyor olabilir
- IP adresini manuel test edin: `telnet <host_ip> 37021`

### "Senkronizasyon sorunu"
- Ağ gecikmesi yüksek olabilir
- FPS'i düşürmeyi deneyin
- Buffer boyutunu artırın

## Kod Örnekleri

### Mesaj Gönderme
```python
from network.messages import player_move_message

# Hareket mesajı oluştur
msg = player_move_message(player_id=1, row=5, col=10, move_count=15)

# Gönder
network_handler.send_message(msg)
```

### Mesaj Alma
```python
def message_callback(msg_type, msg_data):
    if msg_type == MessageType.PLAYER_MOVE:
        row = msg_data.get("row")
        col = msg_data.get("col")
        # Pozisyonu güncelle
```

### Discovery Kullanımı
```python
from network.discovery import PlayerDiscovery

discovery = PlayerDiscovery("Oyuncu1", tcp_port=37021)
discovery.start()

# Oyuncuları al
players = discovery.get_players()
# {ip: {"name": "...", "tcp_port": ..., "last_seen": ...}}

discovery.stop()
```
