# Multiplayer Test Rehberi

## Düzeltilen Sorunlar

### 1. Davet Sistemi
✅ **Düzeltildi**: Davet gönderen artık HOST olarak kalıyor
✅ **Düzeltildi**: Davet alan CLIENT olarak bağlanıyor
✅ **Düzeltildi**: Popup her iki tarafta da düzgün görünüyor

### 2. Oyun Akışı
✅ **Düzeltildi**: Her iki oyuncu da seçilen haritada başlıyor
✅ **Düzeltildi**: Player 1 (Host) = Normal fare
✅ **Düzeltildi**: Player 2 (Client) = Mavi fare
✅ **Düzeltildi**: Kazanan bilgisi her iki tarafa gidiyor

### 3. Lobby Persistence
✅ **Düzeltildi**: Oyun bitince bağlantı kopmadan lobby'ye dönüş
✅ **Düzeltildi**: Aynı bağlantıyla yeni oyun başlatabilme
✅ **Düzeltildi**: Harita değiştirip tekrar oynayabilme

## Test Adımları

### Bilgisayar 1 (HOST)
```bash
cd /Users/erenozyurek/maze_game
source .venv/bin/activate
python main.py
```

1. Ana menü > "2 Kisi"
2. Lobby açılır
3. Map seçimi yap (opsiyonel)
4. Diğer oyuncuyu bekle
5. Liste göründüğünde "DAVET ET" tıkla
6. "Yanıt bekleniyor..." mesajı görünür

**Terminal çıktısı:**
```
[DISCOVERY] Broadcasting: Player
[LOBBY] Davet gönderildi: Player2 (192.168.1.X)
[LOBBY-SERVER] Mesaj alındı: invite_accept
[LOBBY-SERVER] Davet kabul edildi: Player2
```

### Bilgisayar 2 (CLIENT)
```bash
cd /Users/erenozyurek/maze_game
source .venv/bin/activate
python main.py
```

1. Ana menü > "2 Kisi"
2. Lobby açılır
3. HOST oyuncuyu listede gör (2-3 saniye)
4. Popup açılır: "Player1 seni oyuna davet ediyor!"
5. "KABUL ET" tıkla

**Terminal çıktısı:**
```
[DISCOVERY] Broadcasting: Player2
[DISCOVERY] Found player: Player1 at 192.168.1.X
[LOBBY-CLIENT] Davet geldi: ...
[LOBBY] Davet kabul edildi: Player1
```

### Oyun İçi

**Her iki tarafta:**
- 3-2-1 geri sayım başlar
- Oyun ekranı açılır
- HOST: Normal renkli fare (sol üst)
- CLIENT: Mavi renkli fare (peynir yakını)
- Ok tuşları ile hareket et

**Terminal çıktıları:**
```
[GAME] Mesaj alındı: player_move - ...
[GAME] Rakip pozisyonu güncellendi
```

### Kazanma

İlk peynire ulaşan kazanır:

**Kazanan ekranı:**
```
KAZANDINIZ!
15 hamlede tamamlandı
[LOBBY'YE DÖN]
```

**Kaybeden ekranı:**
```
Player 1 Kazandı!
20 hamlede tamamlandı
[LOBBY'YE DÖN]
```

**Terminal:**
```
[GAME] Oyun bitti! Winner: 1
```

### Lobby'ye Dönüş

**Her iki tarafta:**
- "LOBBY'YE DÖN" tıkla
- Lobby ekranı açılır
- Bağlantı hala açık
- Discovery yeniden çalışıyor
- Aynı oyuncular listede
- Tekrar davet gönderebilirsin

**Yeni oyun başlatma:**
1. HOST harita değiştirir (< > butonları)
2. HOST tekrar davet gönderir
3. CLIENT kabul eder
4. Yeni oyun başlar

## Debug Çıktıları

Tüm önemli eventler terminalde görünür:

```
[DISCOVERY] Broadcasting: PlayerName
[DISCOVERY] Received from 192.168.1.X
[DISCOVERY] Found player: ...
[LOBBY] Davet gönderildi: ...
[LOBBY-SERVER] Mesaj alındı: invite_accept
[LOBBY-CLIENT] Davet geldi: ...
[GAME] Mesaj alındı: player_move
[GAME] Oyun bitti! Winner: 1
[LOBBY] Yeni oyun için hazır
```

## Sorun Giderme

### "Oyuncu görünmüyor"
**Çözüm:**
```bash
# Firewall'u kapat
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

### "Davet popup'ı çıkmıyor"
**Kontrol:**
- Terminal çıktısında `[LOBBY-CLIENT] Davet geldi` var mı?
- Varsa: UI render sorunu - oyunu yeniden başlat
- Yoksa: Mesaj gitmemiş - network kontrolü

### "Bağlantı kopuyor"
**Çözüm:**
- Port kullanımda mı: `lsof -i :37020 -i :37021`
- Çakışma varsa oyunları yeniden başlat

### "Senkronizasyon yavaş"
**Normal:**
- LAN'da < 10ms gecikme olmalı
- WiFi kalitesini kontrol et
- `ping <diğer_ip>` ile test et

## Başarı Kriterleri

✅ Lobby'de oyuncu listesi 5 saniye içinde görünür
✅ Davet popup'ı anında açılır
✅ Kabul sonrası 3 saniye içinde oyun başlar
✅ Her iki oyuncu hareket edebilir
✅ Kazanan her iki tarafta görünür
✅ Lobby'ye dönüş bağlantıyı kesmez
✅ Aynı sessionda 2+ oyun oynanabilir
