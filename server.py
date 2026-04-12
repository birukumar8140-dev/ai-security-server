from flask import Flask, request, jsonify, session, redirect
import sqlite3
import requests
import time
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"   # change later

# -----------------------------
# 🔑 LOGIN CONFIG
# -----------------------------
USERNAME = "admin"
PASSWORD = "veer$#@01"

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
# 🔐 LOGIN PAGE
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if user == USERNAME and pwd == PASSWORD:
            session["logged_in"] = True
            return redirect("/")
        else:
            return "❌ Wrong credentials"

    return """
    <html>
    <body style="text-align:center; margin-top:100px;">
        <h2>🔐 Admin Login</h2>
        <form method="POST">
            <input name="username" placeholder="Username"><br><br>
            <input name="password" type="password" placeholder="Password"><br><br>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """

# -----------------------------
# 🔒 AUTH CHECK
# -----------------------------
def is_logged_in():
    return session.get("logged_in")

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

    # 🚨 TELEGRAM
    if score >= 90:
        key = f"{device}-{process}"

        if should_alert(key):
            send_telegram(
                f"🚨 HIGH THREAT!\nDevice: {device}\nIP: {process}\nScore: {score}\nAction: {action}"
            )

    return jsonify({"status": "saved"})

# -----------------------------
# 🚫 BLOCK
# -----------------------------
@app.route("/block", methods=["POST"])
def block_ip_manual():
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

    os.system(f'netsh advfirewall firewall delete rule name="Block {ip}"')
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

    html = """
    <html>
    <body style="background:black; color:white; text-align:center;">
    <h1>🔥 Secure AI Dashboard</h1>
    <table border=1 style="margin:auto;">
    <tr><th>IP</th><th>Score</th><th>Action</th><th>Control</th></tr>
    """

    for process, score, action in rows:
        html += f"""
        <tr>
        <td>{process}</td>
        <td>{score}</td>
        <td>{action}</td>
        <td>
            <button onclick="blockIP('{process}')">Block</button>
            <button onclick="unblockIP('{process}')">Unblock</button>
        </td>
        </tr>
        """

    html += """
    </table>

    <script>
    function blockIP(ip){
        fetch("/block", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({ip:ip})
        });
    }

    function unblockIP(ip){
        fetch("/unblock", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({ip:ip})
        });
    }
    setTimeout(()=>location.reload(),5000);
    </script>

    </body>
    </html>
    """

    return html

# -----------------------------
# 🚀 RUN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
