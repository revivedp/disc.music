import subprocess, os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVER_PATH = os.path.join(BASE_DIR, "app.py")
BOT_PATH = os.path.join(BASE_DIR, "bot.py")

python_exec = sys.executable

server_proc = subprocess.Popen([python_exec, SERVER_PATH])
bot_proc = subprocess.Popen([python_exec, BOT_PATH])

try:

    server_proc.wait()
    bot_proc.wait()

except KeyboardInterrupt:

    server_proc.terminate()
    bot_proc.terminate()