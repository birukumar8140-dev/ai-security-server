from flask import Flask, request, jsonify
import sqlite3
import requests

app = Flask(__name__)

# -----------------------------
# 🔑 TELEGRAM CONFIG
# -----------------------------
BOT_TOKEN = "8719648742:AAHZoS32yiIihyeM4WLMx2x7HZeF3VY-8Xk"
CHAT_ID = "2091748695"

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
# 📦 Database setup
# -----------------------------
def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process TEXT,
            score INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# 📡 Receive data
# -----------------------------
@app.route("/data", methods=["POST"])
def receive_data():
    data = request.json

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO logs (process, score) VALUES (?, ?)",
        (data["process"], data["score"])
    )

    conn.commit()
    conn.close()

    print("📥 Received:", data)

    # 🚨 TELEGRAM ALERT (HIGH ONLY)
    if data["score"] > 70:
        send_telegram(f"🚨 HIGH THREAT!\nProcess: {data['process']}\nScore: {data['score']}")

    return jsonify({"status": "saved"})

# -----------------------------
# 📊 Dashboard
# -----------------------------
@app.route("/")
def dashboard():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT process, score FROM logs ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()

    conn.close()

    high = sum(1 for r in rows if r[1] > 70)
    medium = sum(1 for r in rows if 30 < r[1] <= 70)
    low = sum(1 for r in rows if r[1] <= 30)

    html = f"""
    <html>
    <head>
        <title>AI Security Dashboard</title>
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
                width: 70%;
            }}
            th, td {{
                border: 1px solid white;
                padding: 10px;
            }}
        </style>
    </head>

    <body>

    <h1>🔥 AI Security Dashboard</h1>

    <h2>🔴 High: {high}</h2>
    <h2>🟡 Medium: {medium}</h2>
    <h2>🟢 Low: {low}</h2>

    <table>
        <tr>
            <th>Process</th>
            <th>Score</th>
        </tr>
    """

    for process, score in rows:
        html += f"<tr><td>{process}</td><td>{score}</td></tr>"

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
# 🚀 Run
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
