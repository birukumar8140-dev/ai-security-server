from flask import Flask, request, jsonify, session, redirect
import sqlite3
import requests
import time
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SESSION_PERMANENT"] = False

# -----------------------------
# TELEGRAM
# -----------------------------
BOT_TOKEN = "8719648742:AAHZoS32yiIihyeM4WLMx2x7HZeF3VY-8Xk"
CHAT_ID = "2091748695"

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

# -----------------------------
# COOLDOWN
# -----------------------------
last_alert_time = {}
ALERT_COOLDOWN = 60

def should_alert(key):
    now = time.time()
    last = last_alert_time.get(key, 0)

    if now - last > ALERT_COOLDOWN:
        last_alert_time[key] = now
        return True
    return False

# -----------------------------
# DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        process TEXT,
        score INTEGER,
        device TEXT,
        action TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------------
# SIGNUP
# -----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = ""

    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if not user or not pwd:
            error = "❌ Fill all fields"
        else:
            hashed = generate_password_hash(pwd)

            try:
                conn = sqlite3.connect("data.db")
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (user, hashed)
                )
                conn.commit()
                conn.close()

                return redirect("/login")
            except:
                error = "❌ Username already exists"

    return f"""
    <h2 style="text-align:center;">Signup</h2>
    <div style="color:red;text-align:center;">{error}</div>
    <form method="POST" style="text-align:center;">
    <input name="username"><br><br>
    <input name="password" type="password"><br><br>
    <button>Signup</button>
    </form>
    <p style="text-align:center;"><a href="/login">Login</a></p>
    """

# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (user,))
        result = cursor.fetchone()
        conn.close()

        if result:
            stored_hash = result[0]

            if check_password_hash(stored_hash, pwd):
                session["user"] = user
                return redirect("/")
            else:
                error = "❌ Wrong Password"
        else:
            error = "❌ User not found"

    return f"""
    <html>
    <body style="text-align:center;margin-top:100px;">
    <h2>🔐 Login</h2>
    <div style="color:red">{error}</div>
    <form method="POST">
    <input name="username"><br><br>
    <input name="password" type="password"><br><br>
    <button>Login</button>
    </form>
    <br><a href="/signup">Create Account</a>
    </body>
    </html>
    """

# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -----------------------------
# RECEIVE DATA
# -----------------------------
@app.route("/data", methods=["POST"])
def receive_data():
    data = request.json

    process = data.get("process")
    score = data.get("score")
    device = data.get("device")
    action = data.get("action", "none")

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (process, score, device, action) VALUES (?, ?, ?, ?)",
        (process, score, device, action)
    )
    conn.commit()
    conn.close()

    if score >= 90:
        key = f"{device}-{process}"
        if should_alert(key):
            send_telegram(
                f"🚨 HIGH THREAT!\nDevice: {device}\nProcess/IP: {process}\nScore: {score}\nAction: {action}"
            )

    return jsonify({"status": "saved"})

# -----------------------------
# BLOCK
# -----------------------------
@app.route("/block", methods=["POST"])
def block_ip():
    if "user" not in session:
        return "Unauthorized"

    ip = request.json.get("ip")
    os.system(f'netsh advfirewall firewall add rule name="Block {ip}" dir=out action=block remoteip={ip}')
    return jsonify({"status": "blocked"})

# -----------------------------
# UNBLOCK
# -----------------------------
@app.route("/unblock", methods=["POST"])
def unblock_ip():
    if "user" not in session:
        return "Unauthorized"

    ip = request.json.get("ip")
    os.system(f'netsh advfirewall firewall delete rule name="Block {ip}"')
    return jsonify({"status": "unblocked"})

# -----------------------------
# DASHBOARD
# -----------------------------
@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT process, score, action FROM logs ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()

    html = """
    <html>
    <body style="background:#0f2027;color:white;text-align:center;">
    <h1>🔥 AI Security Dashboard</h1>
    <a href="/logout" style="color:white;">Logout</a>
    <table border="1" style="margin:auto;width:90%;color:white;">
    <tr><th>Process/IP</th><th>Score</th><th>Action</th></tr>
    """

    for p, s, a in rows:
        html += f"<tr><td>{p}</td><td>{s}</td><td>{a}</td></tr>"

    html += "</table></body></html>"

    return html

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
