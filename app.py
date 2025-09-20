from flask import Flask
from flask_socketio import SocketIO


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, cors_allowed_origins="*")

from routes import *

if __name__ == "__main__":  
    HOST = "127.0.0.1"
    PORT = 5000

    socketio.run(app, host=HOST, port=PORT, debug=True, use_reloader=False)
