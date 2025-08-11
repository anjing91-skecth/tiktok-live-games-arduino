# Installation Guide

## Prerequisites

### Python Requirements
- Python 3.8 atau lebih tinggi
- pip (Python package installer)

### Hardware Requirements
- Arduino Uno/Nano/Pro Mini atau compatible
- USB cable untuk koneksi Arduino
- Relay modules atau LED untuk testing (opsional)

### System Requirements
- Windows 10/11 (tested)
- Minimum 4GB RAM
- 1GB storage space

## Installation Steps

### 1. Clone atau Download Project

```bash
git clone https://github.com/anjing91-skecth/tiktok-live-games-arduino.git
cd tiktok-live-games-arduino
```

Atau download sebagai ZIP dan extract.

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Jika ada error, coba install satu per satu:

```bash
pip install TikTokLive==1.0.4
pip install pyserial==3.5
pip install pygame==2.5.2
```

### 3. Setup Arduino

1. **Install Arduino IDE** dari https://www.arduino.cc/en/software
2. **Upload Arduino Code**:
   - Buka `arduino_code/tiktok_live_controller.ino`
   - Install library `ArduinoJson` melalui Library Manager
   - Select board type (Arduino Uno/Nano)
   - Select correct COM port
   - Upload code ke Arduino

3. **Test Arduino Connection**:
   - Open Serial Monitor (9600 baud)
   - Arduino harus mengirim "READY:Arduino initialized"

### 4. Setup Sound Files (Optional)

1. Download atau buat sound files (.wav format)
2. Letakkan di folder `sounds/` dengan nama:
   - `gift.wav`
   - `comment.wav`
   - `like.wav`
   - `follow.wav`
   - `share.wav`

### 5. First Run

```bash
python main.py
```

## Configuration

### 1. Add TikTok Account

1. Launch aplikasi
2. Click "Account Management"
3. Click "Add Account"
4. Enter TikTok username (tanpa @)
5. Select Arduino COM port
6. Save

### 2. Arduino Pin Configuration

1. Select account dari dropdown
2. Go to "Arduino Settings" tab
3. Configure pins sesuai kebutuhan:
   - Gift pins (2-5): Pin untuk different coin values
   - Event pins (6-9): Comment, Like, Follow, Share
4. Test each pin dengan "Test" button
5. Save settings

### 3. Level System

Default level system berdasarkan viewer count:
- Level 1: 0-99 viewers
- Level 2: 100-199 viewers  
- Level 3: 200-299 viewers
- dst.

Stability check: 30 detik dalam range sebelum naik level.

## Usage

### 1. Start Session

1. Select account dari dropdown
2. Click "Start Session"
3. Program akan connect ke TikTok Live
4. Events akan muncul di Live Feed tab
5. Arduino pins akan triggered sesuai konfigurasi

### 2. Monitor Activity

- **Live Feed Tab**: Real-time events, statistics, leaderboard
- **Arduino Settings Tab**: Test pins, modify settings
- **Account Management**: Add/edit/delete accounts

### 3. Stop Session

1. Click "Stop Session" untuk stop gracefully
2. Click "Emergency Stop" untuk immediate stop semua Arduino pins

## Troubleshooting

### TikTok Connection Issues

1. **"Failed to connect"**: Pastikan username benar dan live streaming aktif
2. **"Connection timeout"**: Check internet connection
3. **"Room ID changed"**: Normal, session akan auto-resume

### Arduino Issues

1. **"Port in use"**: Tutup Arduino IDE Serial Monitor
2. **"Connection failed"**: 
   - Check COM port di Device Manager
   - Try different USB cable/port
   - Reset Arduino
3. **"Pin not triggering"**: 
   - Test with LED atau multimeter
   - Check wiring
   - Verify pin configuration

### Performance Issues

1. **GUI lag**: 
   - Reduce window size
   - Disable sound effects
   - Close other applications
2. **High memory usage**:
   - Restart application periodically
   - Clear event feed regularly

### Database Issues

1. **"Database locked"**: 
   - Close multiple instances
   - Restart application
2. **"Corrupted database"**:
   - Backup `data/tiktok_live.db`
   - Delete file to recreate

## Advanced Configuration

### Custom Sound Files

Edit `config/settings.json`:

```json
{
  "sound": {
    "sound_files": {
      "gift": "custom_sounds/my_gift.wav",
      "comment": "custom_sounds/my_comment.wav"
    }
  }
}
```

### Custom Pin Mappings

```json
{
  "arduino": {
    "pins": {
      "gift_pin_1": {"pin": 3, "coin_value": 5},
      "gift_pin_2": {"pin": 4, "coin_value": 25}
    }
  }
}
```

### Level System Customization

```json
{
  "levels": {
    "level_1": {"min_viewers": 0, "max_viewers": 50},
    "level_2": {"min_viewers": 51, "max_viewers": 150}
  }
}
```

## Support

Untuk issues atau questions:

1. Create issue di GitHub repository
2. Include log files dari `logs/` folder
3. Describe steps to reproduce problem
4. Include system info (OS, Python version, Arduino model)

## Updates

Untuk update ke versi terbaru:

1. Backup `data/` dan `config/` folders
2. Download versi terbaru
3. Copy backup folders ke installation baru
4. Run `pip install -r requirements.txt` untuk update dependencies
