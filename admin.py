import os, sys, threading, webbrowser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SMTP_PASS", "wnotpnjkoifygfea")

# Load .env file if it exists
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("\"'")

try:
    import tkinter as tk
except ImportError:
    import subprocess
    subprocess.Popen([sys.executable, "app.py"])
    sys.exit(0)

import config
from app import app

def start():
    threading.Thread(target=lambda: app.run(
        debug=False, port=config.FLASK_PORT, host="127.0.0.1", use_reloader=False
    ), daemon=True).start()
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    btn.config(state="disabled", text=" Lancé")

root = tk.Tk()
root.title("Guide Touristique")
root.geometry("260x120")
root.resizable(False, False)
root.configure(bg="#1a1a2e")

tk.Label(root, text="Guide Touristique", fg="#3ea8da", bg="#1a1a2e",
         font=("Segoe UI", 16, "bold")).pack(pady=(18, 10))

btn = tk.Button(root, text=" Lancer le site", command=start,
                bg="#3ea8da", fg="white", font=("Segoe UI", 11, "bold"),
                cursor="hand2", relief="flat", padx=20, pady=6)
btn.pack()

root.mainloop()
