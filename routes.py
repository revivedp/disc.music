from app import app, socketio
from flask import render_template, redirect, request


# =======================================
#               Flask Routes
# =======================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_ping', methods=["POST"])
def send_ping():
    socketio.emit("flask_send_ping", {"msg": "Pong!"})
    return redirect("/")

@app.route('/start_bot', methods=["POST"])
def start_bot():
    token = request.form.get("bot_token")
    voice_channel_id = request.form.get("voice_channel_id")

    socketio.emit(
        "flask_start_bot", 
        {
            "bot_token": token,
            "voice_channel_id": voice_channel_id
        }
    )
    
    return redirect("/")

@app.route('/add_to_queue', methods=["POST"])
def add_to_queue():
    link = request.form.get("music_link")

    socketio.emit(
        "flask_queue_add",
        {
            "music_link": link
        }
    )

    return redirect("/")

@app.route('/skip', methods=["POST"])
def skip():
    socketio.emit(
        "skip"
    )

    return redirect("/")

@app.route('/stop', methods=["POST"])
def stop():
    socketio.emit(
        "stop"
    )

    return redirect("/")

# =======================================
#               Socket.IO
# =======================================

@socketio.on("bot_queue_update")
def on_bot_queue_update(data):
    socketio.emit("bot_queue_update", data)

@socketio.on("flask_request_queue")
def on_flask_request_queue():
    socketio.emit("flask_request_queue")

@socketio.on("set_volume")
def on_set_volume(data):
    socketio.emit("flask_set_volume", data)