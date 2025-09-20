import subprocess, os, sys, shutil, atexit, signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVER_PATH = os.path.join(BASE_DIR, "app.py")
BOT_PATH = os.path.join(BASE_DIR, "bot.py")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
PYCACHE_DIR = os.path.join(BASE_DIR, "__pycache__")

python_exec = sys.executable

def clean_cache():
    for d in (CACHE_DIR, PYCACHE_DIR):
        shutil.rmtree(d, ignore_errors=True)

clean_cache()
atexit.register(clean_cache)

PROCS = [
    subprocess.Popen([python_exec, SERVER_PATH]),
    subprocess.Popen([python_exec, BOT_PATH]),
]

def terminate_children():
    for p in PROCS:
        if not p or p.poll() is not None:
            continue
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass

def handle_signal(signum, frame):
    terminate_children()
    clean_cache()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)
try:
    signal.signal(signal.SIGTERM, handle_signal)
except Exception:
    pass

try:
    for p in PROCS:
        p.wait()
finally:
    terminate_children()
    clean_cache()