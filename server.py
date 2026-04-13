from flask import Flask, request, jsonify, session, redirect
import sqlite3
import requests
import time
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.config["SESSION_PERMANENT"] = False

# -----------------------------
# TELEGRAM
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

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
            error = "Fill all fields"
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
                error = "Username already exists"

    return """
<html>
<head>
<style>
body {
    margin:0; height:100vh; display:flex;
    justify-content:center; align-items:center;
    background: linear-gradient(135deg,#0f2027,#2c5364);
    font-family:'Segoe UI';
}
.box {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    padding:40px; border-radius:15px;
    width:320px; text-align:center; color:white;
}
h2 { margin-bottom:5px; }
p { color:#aaa; font-size:13px; margin-bottom:20px; }
input {
    width:100%; padding:12px; margin:8px 0;
    border-radius:8px; border:none;
    background:rgba(255,255,255,0.15); color:white;
    box-sizing:border-box;
}
input::placeholder { color:#ccc; }
.btn {
    width:100%; padding:12px; margin-top:10px;
    background:#00c6ff; border:none;
    border-radius:8px; color:white;
    font-size:15px; cursor:pointer;
}
.divider {
    display:flex; align-items:center; margin:15px 0;
    color:#aaa; font-size:13px;
}
.divider::before, .divider::after {
    content:''; flex:1;
    height:1px; background:rgba(255,255,255,0.2);
    margin:0 10px;
}
.link { color:#00c6ff; text-decoration:none; font-size:13px; }
.error { color:#ff6b6b; font-size:13px; margin-bottom:10px; }
</style>
</head>
<body>
<div class="box">
    <h2>BharatShield</h2>
    <p>AI Security — Create your account</p>
    """ + (f'<div class="error">{error}</div>' if error else '') + """
    <form method="POST">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button class="btn" type="submit">Create Account</button>
    </form>
    <div class="divider">already have account?</div>
    <a href="/login" class="link">Login here →</a>
</div>
</body>
</html>
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

        if result and check_password_hash(result[0], pwd):
            session["user"] = user
            return redirect("/")
        else:
            error = "Wrong credentials"

    return """
<html>
<head>
<style>
body {
    margin:0; height:100vh; display:flex;
    justify-content:center; align-items:center;
    background: linear-gradient(135deg,#0f2027,#2c5364);
    font-family:'Segoe UI';
}
.box {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    padding:40px; border-radius:15px;
    width:320px; text-align:center; color:white;
}
h2 { margin-bottom:5px; }
p { color:#aaa; font-size:13px; margin-bottom:20px; }
input {
    width:100%; padding:12px; margin:8px 0;
    border-radius:8px; border:none;
    background:rgba(255,255,255,0.15); color:white;
    box-sizing:border-box;
}
input::placeholder { color:#ccc; }
.btn {
    width:100%; padding:12px; margin-top:10px;
    background:#00c6ff; border:none;
    border-radius:8px; color:white;
    font-size:15px; cursor:pointer;
}
.divider {
    display:flex; align-items:center; margin:15px 0;
    color:#aaa; font-size:13px;
}
.divider::before, .divider::after {
    content:''; flex:1;
    height:1px; background:rgba(255,255,255,0.2);
    margin:0 10px;
}
.link { color:#00c6ff; text-decoration:none; font-size:13px; }
.error { color:#ff6b6b; font-size:13px; margin-bottom:10px; }
</style>
</head>
<body>
<div class="box">
    <h2>BharatShield</h2>
    <p>AI Security — Welcome back</p>
    """ + (f'<div class="error">{error}</div>' if error else '') + """
    <form method="POST">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button class="btn" type="submit">Login</button>
    </form>
    <div class="divider">new here?</div>
    <a href="/signup" class="link">Create Account →</a>
</div>
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
# BLOCK / UNBLOCK
# -----------------------------
def is_valid_ip(ip):
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    return re.match(pattern, ip)
@app.route("/block", methods=["POST"])
def block_ip():
    if "user" not in session:
        return "Unauthorized"

    ip = request.json.get("ip")

    if not is_valid_ip(ip):
        return jsonify({"error": "Invalid IP"}), 400

    os.system(f'netsh advfirewall firewall add rule name="Block {ip}" dir=out action=block remoteip={ip}')
    return jsonify({"status": "blocked"})

    
@app.route("/unblock", methods=["POST"])
def unblock_ip():
    if "user" not in session:
        return "Unauthorized"

    ip = request.json.get("ip")
    if not is_valid_ip(ip):
        return jsonify({"error": "Invalid IP"}), 400
    os.system(f'netsh advfirewall firewall delete rule name="Block {ip}"')
    return jsonify({"status": "unblocked"})

# -----------------------------
# RECEIVE DATA
# -----------------------------
@app.route("/data", methods=["POST"])
def receive_data():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (process, score, device, action) VALUES (?, ?, ?, ?)",
        (data["process"], data["score"], data["device"], data["action"])
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})

# -----------------------------
# DASHBOARD (PRO UI)
# -----------------------------
@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect("/signup")

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT process, score, action FROM logs ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()

    high = sum(1 for r in rows if r[1] >= 90)
    medium = sum(1 for r in rows if 30 < r[1] < 90)
    low = sum(1 for r in rows if r[1] <= 30)

    html = f"""
    <html>
    <head>
    <style>
    body {{margin:0;font-family:Segoe UI;background:#0f2027;color:white;display:flex;}}
    .sidebar {{width:220px;background:#111;height:100vh;padding:20px;}}
    .sidebar h2 {{color:#00c6ff;}}
    .main {{flex:1;padding:20px;}}

    .cards {{display:flex;gap:20px;margin-bottom:20px;}}
    .card {{flex:1;padding:20px;border-radius:10px;text-align:center;font-weight:bold;}}
    .high {{background:red;}}
    .medium {{background:yellow;color:black;}}
    .low {{background:green;}}

    table {{width:100%;border-collapse:collapse;}}
    th, td {{padding:10px;border-bottom:1px solid rgba(255,255,255,0.1);}}

    button {{padding:5px;border:none;border-radius:5px;cursor:pointer;}}
    .block {{background:red;color:white;}}
    .unblock {{background:green;color:white;}}
    </style>
    </head>

    <body>

    <div class="sidebar">
        <h2>AI Security</h2>
        <a href="/">Dashboard</a><br>
        <a href="/logout">Logout</a>
    </div>

    <div class="main">
    <h1>Security Dashboard</h1>

    <div class="cards">
        <div class="card high">High<br>{high}</div>
        <div class="card medium">Medium<br>{medium}</div>
        <div class="card low">Low<br>{low}</div>
    </div>

    <table>
    <tr><th>IP</th><th>Score</th><th>Action</th><th>Control</th></tr>
    """

    for p, s, a in rows:
        html += f"""
        <tr>
        <td>{p}</td>
        <td>{s}</td>
        <td>{a}</td>
        <td>
        <button class="block" onclick="blockIP('{p}')">Block</button>
        <button class="unblock" onclick="unblockIP('{p}')">Unblock</button>
        </td>
        </tr>
        """

    html += """
    </table>

    <script>
    function blockIP(ip){
        fetch("/block",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ip:ip})});
    }
    function unblockIP(ip){
        fetch("/unblock",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ip:ip})});
    }
    setTimeout(()=>location.reload(),5000);
    </script>

    </div>
    </body>
    </html>
    """

    return html

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
