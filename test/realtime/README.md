# TikTokLive API Study - Testing Folder

## Overview
Folder ini berisi studi dan testing untuk memahami cara kerja library **TikTokLive API** dalam project TikTok Live Games.

## TikTokLive API Library - Key Insights

### 🔗 Basic Connection
```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent

# Create client
client = TikTokLiveClient(unique_id="username")

# Setup event handlers
@client.on(ConnectEvent)
async def on_connect(event):
    print(f"Connected to @{event.unique_id}")

# Start connection
await client.start()  # Non-blocking
# OR
client.run()  # Blocking
```

### 📊 Event Types & Data Structure

#### 1. **ConnectEvent**
- Triggered ketika berhasil connect ke live stream
- Properties:
  - `event.unique_id`: Username yang di-connect
  - `client.room_id`: Room ID dari live stream
  - `client.connected`: Status connection

#### 2. **CommentEvent** 💬
- Real-time chat messages
- Properties:
  ```python
  event.user.unique_id    # Username
  event.user.nickname     # Display name
  event.comment          # Comment text
  ```

#### 3. **GiftEvent** 🎁
- Virtual gifts dari viewers
- **PENTING**: Handle gift streaks!
  ```python
  @client.on(GiftEvent)
  async def on_gift(event):
      # Streakable gift & streak selesai
      if event.gift.streakable and not event.streaking:
          print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")
      
      # Non-streakable gift
      elif not event.gift.streakable:
          print(f"{event.user.unique_id} sent \"{event.gift.name}\"")
  ```

#### 4. **LikeEvent** 👍
- Like events dari viewers
- Properties:
  ```python
  event.user.unique_id    # Username
  event.count            # Number of likes
  ```

#### 5. **FollowEvent** ➕
- New followers
- Properties:
  ```python
  event.user.unique_id    # Username yang follow
  event.user.nickname     # Display name
  ```

#### 6. **ShareEvent** 📤
- Stream sharing events
- Properties:
  ```python
  event.user.unique_id    # Username yang share
  ```

### 🛡️ Connection Best Practices

#### 1. **Check Live Status First**
```python
is_live = await client.is_live()
if not is_live:
    print("User is not live")
    return
```

#### 2. **Handle Timeouts**
```python
try:
    await asyncio.wait_for(client.start(), timeout=120)
except asyncio.TimeoutError:
    print("Connection timeout")
```

#### 3. **Graceful Disconnect**
```python
await client.disconnect()
```

### 🚧 TikTok Anti-Bot Protection

Library ini sering menghadapi **TikTok anti-bot protection** yang menyebabkan:
- Connection timeouts (45-300 detik)
- Rate limiting
- IP blocking

#### Solusi yang Bisa Diterapkan:
1. **Extended Timeouts**: 120-300 detik
2. **Random Delays**: Tunggu 30-120 detik antar connection
3. **User Agent Rotation**: Ganti user agent
4. **Proxy Support**: 
   ```python
   import httpx
   proxy = httpx.Proxy("http://proxy-server:port")
   client = TikTokLiveClient(unique_id="user", web_proxy=proxy, ws_proxy=proxy)
   ```
5. **Session Management**: Rotate session cookies

### 🎯 Integration dengan Project

Dalam project TikTok Live Games, library ini digunakan di:

#### `src/core/tiktok_connector.py`
- Wrapper untuk TikTokLive client
- Handle connection timeouts
- Adaptive timeout berdasarkan attempts
- Unicode logging integration

#### Event Processing Flow:
1. **Client Connection** → `ConnectEvent`
2. **Real-time Events** → `CommentEvent`, `GiftEvent`, `LikeEvent`
3. **Data Processing** → Update database stats
4. **Arduino Integration** → Trigger actions based on events

## Files dalam Testing Folder

### `tiktoklive_api_study.py`
- Complete study script untuk testing TikTokLive API
- Test connection ke multiple users
- Handle semua event types
- Statistics tracking
- Error handling dan debugging

## Usage Examples

### Run API Study
```bash
cd testing
python tiktoklive_api_study.py
```

### Test Specific User
```python
study = TikTokLiveStudy("rhianladiku19")
study.setup_client()
await study.test_connection(timeout=60)
```

## Key Learnings

1. **Connection Success**: Library bisa connect tapi sering blocked oleh TikTok anti-bot
2. **Event Handling**: Robust event system untuk real-time data
3. **Gift Streaks**: Perlu handling khusus untuk gift streaks
4. **Error Handling**: Timeout dan exception handling crucial
5. **User Status**: Always check `is_live()` sebelum connect

## Next Steps

1. **Implement Proxy Rotation** untuk bypass anti-bot
2. **Add User Agent Randomization**
3. **Implement Session Cookie Management**
4. **Add Retry Logic** dengan exponential backoff
5. **Enhanced Logging** untuk debugging connection issues

---

*Study dilakukan sebagai bagian dari TikTok Live Games project untuk memahami cara optimal menggunakan TikTokLive API library.*
