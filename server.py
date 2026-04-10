from flask import Flask, request, jsonify
import sqlite3
import requests

app = Flask(__name__)

# -----------------------------
# 🔑 TELEGRAM CONFIG
# -----------------------------
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=data)
    except:
        pass

# -----------------------------
# 📦 DATABASE SETUP
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

    process = data.get("process", "unknown")
    score = data.get("score", 0)
    device = data.get("device", "unknown")
    action = data.get("action", "none")

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO logs (process, score, device, action) VALUES (?, ?, ?, ?)",
        (process, score, device, action)
    )

    conn.commit()
    conn.close()

    print("📥 Received:", data)

    # 🚨 TELEGRAM ALERT
    if score >= 90:
        send_telegram(
            f"🚨 HIGH THREAT!\n"
            f"Device: {device}\n"
            f"Process: {process}\n"
            f"Score: {score}\n"
            f"Action: {action}"
        )

    return jsonify({"status": "saved"})

# -----------------------------
# 📊 DASHBOARD
# -----------------------------
@app.route("/")
def dashboard():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    # Latest data
    cursor.execute("SELECT process, score, device, action FROM logs ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()

    # Total high (all time)
    cursor.execute("SELECT COUNT(*) FROM logs WHERE score >= 90")
    total_high = cursor.fetchone()[0]

    conn.close()

    high = sum(1 for r in rows if r[1] >= 90)
    medium = sum(1 for r in rows if 30 < r[1] < 90)
    low = sum(1 for r in rows if r[1] <= 30)

    html = f"""
    <html>
    <head>
        <title>AI Security Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

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
                width: 80%;
            }}
            th, td {{
                border: 1px solid white;
                padding: 8px;
            }}
            th {{
                background: #1c3b4a;
            }}
        </style>
    </head>

    <body>

    <h1>🔥 AI Security Dashboard</h1>

    <h2>🔴 High: {high}</h2>
    <h2>🟡 Medium: {medium}</h2>
    <h2>🟢 Low: {low}</h2>

    <h3>🔥 Total High Detected (All Time): {total_high}</h3>

    <canvas id="chart" width="300" height="150"></canvas>

    <script>
        var ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: ['High', 'Medium', 'Low'],
                datasets: [{{
                    label: 'Threat Levels',
                    data: [{high}, {medium}, {low}],
                    backgroundColor: ['red', 'yellow', 'green']
                }}]
            }}
        }});
    </script>

    <table>
        <tr>
            <th>Process</th>
            <th>Score</th>
            <th>Device</th>
            <th>Action</th>
        </tr>
    """

    for process, score, device, action in rows:
        color = "white"

        if score >= 90:
            color = "red"
        elif score > 30:
            color = "yellow"
        else:
            color = "lightgreen"

        html += f"""
        <tr>
            <td style="color:{color}">{process}</td>
            <td>{score}</td>
            <td>{device}</td>
            <td>{action}</td>
        </tr>
        """

    html += f"""
    </table>

    <script>
        var high = {high};

        if (high > 0) {{
            alert("🚨 HIGH THREAT DETECTED!");

            var audio = new Audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg");

            audio.play().catch(() => {{
                document.body.onclick = () => audio.play();
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
