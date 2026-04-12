from flask import Flask, request, jsonify, session, redirect
import sqlite3
import requests
import time
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -----------------------------
# 🔑 TELEGRAM
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
# ⏱ COOLDOWN
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
# 📦 DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    # logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process TEXT,
            score INTEGER,
            device TEXT,
            action TEXT
        )
    """)

    # users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------------
# 🧑 SIGNUP
# -----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()

        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
        conn.commit()
        conn.close()

        return redirect("/login")

    return """
    <h2>Signup</h2>
    <form method="POST">
    <input name="username" placeholder="Username"><br><br>
    <input name="password" type="password" placeholder="Password"><br><br>
    <button>Signup</button>
    </form>
    """

# -----------------------------
# 🔐 LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        result = cursor.fetchone()
        conn.close()

        if result:
            session["user"] = user
            return redirect("/")
        else:
            return "❌ Wrong credentials"

    return """
    <h2>Login</h2>
    <form method="POST">
    <input name="username"><br><br>
    <input name="password" type="password"><br><br>
    <button>Login</button>
    </form>
    """

# -----------------------------
# 🔒 AUTH CHECK
# -----------------------------
def is_logged_in():
    return "user" in session

# -----------------------------
# 📡 RECEIVE DATA
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
            send_telegram(f"🚨 THREAT: {process}")

    return jsonify({"status": "saved"})

# -----------------------------
# 🚫 BLOCK
# -----------------------------
@app.route("/block", methods=["POST"])
def block_ip():
    if not is_logged_in():
        return "Unauthorized"

    ip = request.json.get("ip")
    os.system(f'netsh advfirewall firewall add rule name="Manual Block {ip}" dir=out action=block remoteip={ip}')

    return jsonify({"status": "blocked"})

# -----------------------------
# 🔓 UNBLOCK
# -----------------------------
@app.route("/unblock", methods=["POST"])
def unblock_ip():
    if not is_logged_in():
        return "Unauthorized"

    ip = request.json.get("ip")
    os.system(f'netsh advfirewall firewall delete rule name="Manual Block {ip}"')

    return jsonify({"status": "unblocked"})

# -----------------------------
# 📊 DASHBOARD
# -----------------------------
@app.route("/")
def dashboard():
    if not is_logged_in():
        return redirect("/login")

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT process, score, action FROM logs ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()

    conn.close()

    html = "<h1>AI Security Dashboard</h1><table border=1>"
    html += "<tr><th>IP</th><th>Score</th><th>Action</th><th>Control</th></tr>"

    for p, s, a in rows:
        html += f"""
        <tr>
        <td>{p}</td>
        <td>{s}</td>
        <td>{a}</td>
        <td>
        <button onclick="blockIP('{p}')">Block</button>
        <button onclick="unblockIP('{p}')">Unblock</button>
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
    </script>
    """

    return html

# -----------------------------
# 🚀 RUN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
