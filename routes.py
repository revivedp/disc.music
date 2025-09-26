from app import app, socketio
from flask import render_template, redirect, request

BOT_SID = None
BOT_ONLINE = False
LAST_VOLUME = 50  # novo

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_bot', methods=['POST'])
def start_bot():
    token = request.form.get('bot_token')
    vcid = request.form.get('voice_channel_id')
    socketio.emit('flask_start_bot', {'bot_token': token, 'voice_channel_id': vcid})
    return redirect('/')

@app.route('/disconnect_bot', methods=['POST'])
def disconnect_bot():
    socketio.emit('flask_disconnect_bot')
    return redirect('/')

@app.route('/add_to_queue', methods=['POST'])
def add_to_queue():
    link = request.form.get('music_link')
    socketio.emit('flask_queue_add', {'music_link': link})
    return redirect('/')

@app.route('/play', methods=['POST'])
def play():
    socketio.emit('play'); return redirect('/')

@app.route('/pause', methods=['POST'])
def pause():
    socketio.emit('pause'); return redirect('/')

@app.route('/skip', methods=['POST'])
def skip():
    socketio.emit('skip'); return redirect('/')

@app.route('/stop', methods=['POST'])
def stop():
    socketio.emit('stop'); return redirect('/')

@socketio.on('bot_status')
def on_bot_status(data):
    global BOT_ONLINE, BOT_SID
    BOT_ONLINE = bool(data.get('online'))
    BOT_SID = request.sid
    socketio.emit('bot_status', {'online': BOT_ONLINE})

@socketio.on('request_status_ping')
def on_request_status_ping():
    socketio.emit('bot_status', {'online': BOT_ONLINE}, to=request.sid)
    socketio.emit('volume_state', {'volume': LAST_VOLUME}, to=request.sid)

@socketio.on('connect')
def on_ws_connect():
    socketio.emit('bot_status', {'online': BOT_ONLINE}, to=request.sid)
    socketio.emit('volume_state', {'volume': LAST_VOLUME}, to=request.sid)

@socketio.on('disconnect')
def on_ws_disconnect():
    global BOT_SID, BOT_ONLINE
    if request.sid == BOT_SID:
        BOT_SID = None
        BOT_ONLINE = False
        socketio.emit('bot_status', {'online': False})

@socketio.on('bot_queue_update')
def on_bot_queue_update(data):
    socketio.emit('bot_queue_update', data)

@socketio.on('flask_request_queue')
def on_flask_request_queue():
    socketio.emit('flask_request_queue')

@socketio.on('set_volume')
def on_set_volume(data):
    global LAST_VOLUME
    try:
        v = int(data.get('volume', 50))
    except Exception:
        v = 50
    v = max(0, min(100, v))
    LAST_VOLUME = v
    socketio.emit('flask_set_volume', {'volume': v})
    # também devolve estado (garante sincronia)
    socketio.emit('volume_state', {'volume': v}, to=request.sid)

@socketio.on('queue_reorder')
def on_queue_reorder(data):
    socketio.emit('flask_queue_reorder', data)

@socketio.on('queue_delete')
def on_queue_delete(data):
    socketio.emit('flask_queue_delete', data)

@socketio.on('queue_play_now')
def on_queue_play_now(data):
    socketio.emit('flask_queue_play_now', data)

@socketio.on('set_repeat')
def on_set_repeat(data):
    socketio.emit('flask_set_repeat', data)

@socketio.on('repeat_state')
def on_repeat_state(data):
    socketio.emit('repeat_state', data)

@socketio.on('queue_add_request')
def on_queue_add_request(data):
    socketio.emit('flask_queue_add', data)