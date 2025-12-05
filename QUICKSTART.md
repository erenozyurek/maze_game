# MULTIPLAYER QUICK START

## Hızlı Başlangıç

### 1. Oyunu Başlat
```bash
cd /Users/erenozyurek/maze_game
source .venv/bin/activate
python main.py
```

### 2. İki Oyuncu Modu
- Ana menüde **"2 Kisi"** butonuna tıkla
- Lobby ekranı açılır

### 3. Oyuncu Bulma
- Lobby otomatik olarak aynı ağdaki diğer oyuncuları arar
- 2-3 saniye içinde liste görünür

### 4. Davet Gönderme
- Oyuncunun yanındaki **"DAVET ET"** butonuna tıkla
- "Yanıt bekleniyor..." mesajı görünür

### 5. Davet Alma (Diğer Oyuncu)
- Popup açılır: "[İsim] seni oyuna davet ediyor!"
- **"KABUL ET"** veya **"REDDET"** seç

### 6. Oyun Başlangıcı
- Kabul sonrası 3-2-1 geri sayım
- Oyun başlar!

### 7. Oyun İçi
- **Player 1 (Host)**: Normal renkli fare
- **Player 2 (Client)**: Mavi renkli fare
- Ok tuşları ile hareket et
- İlk peynire ulaşan kazanır

---

## Test (Tek Bilgisayar)

İki terminal aç:

**Terminal 1:**
```bash
cd /Users/erenozyurek/maze_game
source .venv/bin/activate
python main.py
# > 2 Kisi > Bekle > Daveti kabul et
```

**Terminal 2:**
```bash
cd /Users/erenozyurek/maze_game
source .venv/bin/activate
python main.py
# > 2 Kisi > Diğer oyuncuyu gör > Davet gönder
```

---

## Mimari Özet

```
[Ana Menü] → "2 Kisi" 
    ↓
[Lobby] → Discovery başlar (UDP Broadcast)
    ↓
[Oyuncu Listesi] → Davet gönder
    ↓
[Popup] → Kabul/Reddet
    ↓
[Geri Sayım] → 3-2-1
    ↓
[Multiplayer Oyun] → TCP üzerinden senkronizasyon
    ↓
[Kazanan Ekranı] → Ana menüye dön
```

---

## Protokol Özet

- **Discovery**: UDP Port 37020 (Broadcast her 2 saniye)
- **Game**: TCP Port 37021 (Mesaj formatı: JSON + newline)
- **FPS**: 60 (Her hareket anında gönderilir)

---

## Modüller

- `network/discovery.py` - Oyuncu keşfi
- `network/server.py` - Host TCP server
- `network/client.py` - Client TCP bağlantı
- `network/messages.py` - Mesaj protokolü
- `lobby.py` - Lobby UI + davet sistemi
- `game_multiplayer.py` - İki oyunculu oyun

---

## Sorun Giderme

**Problem**: Oyuncu görünmüyor
- Firewall kontrolü: UDP 37020
- Aynı ağda olun
- 5 saniye bekleyin

**Problem**: Bağlanamıyor
- Firewall kontrolü: TCP 37021
- Port kullanımda mı: `lsof -i :37021`

**Problem**: Lag var
- Ağ kalitesini kontrol edin
- Ping testi: `ping <diğer_ip>`
