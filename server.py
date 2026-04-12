from flask import Flask, request, jsonify
import sqlite3
import requests
import time
import os

app = Flask(__name__)

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

    print(f"📥 {device} | {process} | {score} | {action}")

    # 🚨 TELEGRAM ALERT
    if score >= 90:
        key = f"{device}-{process}"

        if should_alert(key):
            send_telegram(
                f"🚨 HIGH THREAT!\n"
                f"Device: {device}\n"
                f"IP: {process}\n"
                f"Score: {score}\n"
                f"Action: {action}"
            )

    return jsonify({"status": "saved"})

# -----------------------------
# 🚫 BLOCK API
# -----------------------------
@app.route("/block", methods=["POST"])
def block_ip_manual():
    data = request.json
    ip = data.get("ip")

    command = f'netsh advfirewall firewall add rule name="Manual Block {ip}" dir=out action=block remoteip={ip}'
    os.system(command)

    return jsonify({"status": "blocked", "ip": ip})

# -----------------------------
# 🔓 UNBLOCK API
# -----------------------------
@app.route("/unblock", methods=["POST"])
def unblock_ip():
    data = request.json
    ip = data.get("ip")

    os.system(f'netsh advfirewall firewall delete rule name="Block {ip}"')
    os.system(f'netsh advfirewall firewall delete rule name="Manual Block {ip}"')

    return jsonify({"status": "unblocked", "ip": ip})

# -----------------------------
# 📊 DASHBOARD
# -----------------------------
@app.route("/")
def dashboard():
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
        <title>AI Security Control Panel</title>
        <style>
            body {{
                background: #0f2027;
                color: white;
                text-align: center;
                font-family: Arial;
            }}
            table {{
                margin: auto;
                border-collapse: collapse;
                width: 90%;
            }}
            th, td {{
                border: 1px solid white;
                padding: 8px;
            }}
            button {{
                padding: 5px;
                margin: 2px;
            }}
        </style>
    </head>

    <body>

    <h1>🔥 AI Security Control Panel</h1>

    <h2>🔴 High: {high}</h2>
    <h2>🟡 Medium: {medium}</h2>
    <h2>🟢 Low: {low}</h2>

    <table>
        <tr>
            <th>IP</th>
            <th>Score</th>
            <th>Action</th>
            <th>Control</th>
        </tr>
    """

    for process, score, action in rows:
        color = "white"

        if score >= 90:
            color = "red"
        elif score > 30:
            color = "yellow"
        else:
            color = "lightgreen"

        html += f"""
        <tr style='color:{color}'>
            <td>{process}</td>
            <td>{score}</td>
            <td>{action}</td>
            <td>
                <button onclick="blockIP('{process}')">Block</button>
                <button onclick="unblockIP('{process}')">Unblock</button>
            </td>
        </tr>
        """

    html += f"""
    </table>

    <script>
        function blockIP(ip) {{
            fetch("/block", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ ip: ip }})
            }});
        }}

        function unblockIP(ip) {{
            fetch("/unblock", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ ip: ip }})
            }});
        }}

        setTimeout(() => {{
            location.reload();
        }}, 5000);
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
