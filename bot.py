import socketio, discord, yt_dlp, asyncio, time, uuid
from discord.ext import commands
from threading import Thread, Lock
from pathlib import Path
from collections import deque
from concurrent.futures import ThreadPoolExecutor

TOKEN = None
VOICE_CHANNEL_ID = None

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
voice_client = None

desired_volume = 0.5

bot = commands.Bot(command_prefix="!", intents=intents)
_bot_thread = None

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

backend_queue = deque()
queue_lock = Lock()
executor = ThreadPoolExecutor(max_workers=2)

# New playback control flags
REPEAT_CURRENT = False
LAST_PLAYED = None
SKIP_REPEAT_ONCE = False

def _run_bot():
    bot.run(TOKEN)

@bot.event
async def on_ready():
    print(f'{bot.user} connected!')
    try:
        sio.emit("bot_status", {"online": True})
    except Exception:
        pass

@bot.event
async def on_disconnect():
    try:
        sio.emit("bot_status", {"online": False})
    except Exception:
        pass

def run_coro_safe(coro):
    if bot.loop and not bot.loop.is_closed():
        return asyncio.run_coroutine_threadsafe(coro, bot.loop)

def download_track(link: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "noplaylist": True,
        "outtmpl": str(CACHE_DIR / "%(id)s.%(ext)s"),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            if "entries" in info:
                info = info["entries"][0]
            filepath = info.get("requested_downloads", [{}])[0].get("filepath")
            if not filepath:
                filepath = ydl.prepare_filename(info)
            title = info.get("title", str(link))
            return {"id": str(uuid.uuid4()), "title": title, "filepath": filepath}
    except Exception as e:
        print(f"Download error: {e}")
        return None

def emit_queue_update():
    with queue_lock:
        q = [{"id": item["id"], "title": item["title"]} for item in backend_queue]
    try:
        sio.emit("bot_queue_update", {"queue": q})
    except Exception as e:
        print(f"Emit error: {e}")

async def _make_source(filepath: str, is_url: bool):
    ffmpeg_opts = {"options": "-vn -loglevel error -hide_banner -nostdin"}
    if is_url:
        ffmpeg_opts["before_options"] = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    return discord.FFmpegPCMAudio(filepath, **ffmpeg_opts)

async def ensure_voice_connected():
    global voice_client
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if not channel or not isinstance(channel, discord.VoiceChannel):
        print("Couldn't find voice channel!")
        return
    guild = channel.guild
    if guild.voice_client and guild.voice_client.is_connected():
        voice_client = guild.voice_client
        if voice_client.channel.id != channel.id:
            await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

async def ensure_playing():
    global LAST_PLAYED
    await ensure_voice_connected()
    if not voice_client or voice_client.is_playing() or (hasattr(voice_client, "is_paused") and voice_client.is_paused()):
        return
    with queue_lock:
        next_item = backend_queue.popleft() if backend_queue else None
    if not next_item:
        return
    filepath = next_item["filepath"]
    LAST_PLAYED = next_item
    emit_queue_update()
    is_url = isinstance(filepath, str) and filepath.startswith(("http://", "https://"))
    try:
        source = await _make_source(filepath, is_url)
    except Exception as e:
        print(f"FFmpeg source error: {e}")
        return
    source = discord.PCMVolumeTransformer(source, volume=desired_volume)

    def _after(err):
        global SKIP_REPEAT_ONCE, REPEAT_CURRENT, LAST_PLAYED
        if err:
            print(f"Playback error: {err}")
        try:
            if REPEAT_CURRENT and LAST_PLAYED and not SKIP_REPEAT_ONCE:
                with queue_lock:
                    backend_queue.appendleft(LAST_PLAYED)
            if SKIP_REPEAT_ONCE:
                SKIP_REPEAT_ONCE = False
            if bot.loop and not bot.loop.is_closed():
                bot.loop.call_soon_threadsafe(asyncio.create_task, ensure_playing())
        except Exception as e2:
            print(f"after error: {e2}")

    voice_client.play(source, after=_after)
    print(f"Playing: {next_item['title']}")

async def skip_track():
    global SKIP_REPEAT_ONCE
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        SKIP_REPEAT_ONCE = True
        voice_client.stop()
        return
    await ensure_playing()

async def stop_playback(disconnect: bool = False):
    global LAST_PLAYED
    with queue_lock:
        backend_queue.clear()
    emit_queue_update()
    LAST_PLAYED = None
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
    if disconnect and voice_client and voice_client.channel:
        try:
            await voice_client.disconnect(force=False)
        except Exception as e:
            print(f"[voice] disconnect error: {e}")

async def pause_playback():
    if voice_client and voice_client.is_playing():
        voice_client.pause()

async def play_or_resume():
    await ensure_voice_connected()
    if not voice_client:
        return
    if hasattr(voice_client, "is_paused") and voice_client.is_paused():
        voice_client.resume()
        return
    if voice_client.is_playing():
        return
    await ensure_playing()

sio = socketio.Client()

@sio.on("flask_start_bot")
def start_bot(data):
    if not data:
        return
    global TOKEN, VOICE_CHANNEL_ID, _bot_thread
    if _bot_thread and _bot_thread.is_alive():
        return
    TOKEN = data['bot_token']
    VOICE_CHANNEL_ID = int(data['voice_channel_id'])
    _bot_thread = Thread(target=_run_bot, daemon=True)
    _bot_thread.start()

@sio.on("flask_queue_add")
def on_flask_queue_add(data):
    if not data:
        return
    link = data["music_link"]
    def work():
        track = download_track(link)
        if track:
            with queue_lock:
                backend_queue.append(track)
            emit_queue_update()
            # REMOVIDO auto-start: só tocará quando usuário apertar Play
    executor.submit(work)

@sio.on("flask_request_queue")
def on_request_queue():
    emit_queue_update()

@sio.on("play")
def on_play():
    fut = run_coro_safe(play_or_resume())
    if fut: fut.add_done_callback(lambda f: f.exception())

@sio.on("pause")
def on_pause():
    fut = run_coro_safe(pause_playback())
    if fut: fut.add_done_callback(lambda f: f.exception())

@sio.on("skip")
def on_skip():
    fut = run_coro_safe(skip_track())
    if fut: fut.add_done_callback(lambda f: f.exception())

@sio.on("stop")
def on_stop():
    fut = run_coro_safe(stop_playback())
    if fut: fut.add_done_callback(lambda f: f.exception())

@sio.on("flask_set_volume")
def on_flask_set_volume(data):
    global desired_volume, voice_client
    try:
        vol = int(data.get("volume", 50))
        vol = max(0, min(100, vol))
        desired_volume = vol / 100.0
        src = getattr(voice_client, "source", None)
        if src and hasattr(src, "volume"):
            src.volume = desired_volume
    except Exception as e:
        print(f"[volume] set failed: {e}")

# New handlers
@sio.on("flask_queue_reorder")
def on_queue_reorder(data):
    order = (data or {}).get("order", [])
    if not order:
        return
    with queue_lock:
        mapping = {item["id"]: item for item in backend_queue}
        new_q = deque()
        for _id in order:
            if _id in mapping:
                new_q.append(mapping[_id])
        # append any leftover
        for item in backend_queue:
            if item["id"] not in order:
                new_q.append(item)
        backend_queue.clear()
        backend_queue.extend(new_q)
    emit_queue_update()

@sio.on("flask_queue_delete")
def on_queue_delete(data):
    _id = (data or {}).get("id")
    if not _id:
        return
    removed = False
    with queue_lock:
        new_q = deque()
        while backend_queue:
            itm = backend_queue.popleft()
            if itm["id"] == _id:
                removed = True
                continue
            new_q.append(itm)
        backend_queue.extend(new_q)
    if removed:
        emit_queue_update()

@sio.on("flask_queue_play_now")
def on_queue_play_now(data):
    global SKIP_REPEAT_ONCE
    _id = (data or {}).get("id")
    if not _id:
        return
    target = None
    with queue_lock:
        new_q = deque()
        while backend_queue:
            itm = backend_queue.popleft()
            if itm["id"] == _id and not target:
                target = itm
            else:
                new_q.append(itm)
        backend_queue.extendleft(reversed(new_q))  # reorder preserved
        if target:
            backend_queue.appendleft(target)
    if target:
        emit_queue_update()
        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            SKIP_REPEAT_ONCE = True
            voice_client.stop()
        else:
            fut = run_coro_safe(ensure_playing())
            if fut: fut.add_done_callback(lambda f: f.exception())

@sio.on("flask_set_repeat")
def on_set_repeat(data):
    global REPEAT_CURRENT
    REPEAT_CURRENT = bool((data or {}).get("repeat"))
    try:
        sio.emit("repeat_state", {"repeat": REPEAT_CURRENT})
    except Exception:
        pass

@sio.on("flask_disconnect_bot")
def on_disconnect_bot():
    global TOKEN, VOICE_CHANNEL_ID, _bot_thread
    fut = run_coro_safe(stop_playback(disconnect=True))
    if fut:
        fut.add_done_callback(lambda f: f.exception())
    # Close bot (logout)
    fut2 = run_coro_safe(bot.close())
    if fut2:
        fut2.add_done_callback(lambda f: f.exception())
    TOKEN = None
    VOICE_CHANNEL_ID = None
    _bot_thread = None

if __name__ == "__main__":
    for _ in range(20):
        try:
            sio.connect("http://127.0.0.1:5000", wait_timeout=5)
            break
        except Exception as e:
            print(f"[socketio] connect failed: {e}; retrying...")
            time.sleep(0.5)
    else:
        raise SystemExit(1)
    sio.wait()
