from flask import Flask, request, jsonify
import sqlite3
import requests
import time

app = Flask(__name__)

# -----------------------------
# 🔑 TELEGRAM CONFIG
# -----------------------------
BOT_TOKEN = "8719648742:AAHZoS32yiIihyeM4WLMx2x7HZeF3VY-8Xk"
CHAT_ID = "2091748695"

# cooldown storage
last_alert_time = {}
ALERT_COOLDOWN = 300  # 5 minutes

def should_alert(key):
    now = time.time()
    last = last_alert_time.get(key, 0)

    if now - last > ALERT_COOLDOWN:
        last_alert_time[key] = now
        return True
    return False

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except:
        pass

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
            score INTEGER
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

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO logs (process, score) VALUES (?, ?)",
        (process, score)
    )

    conn.commit()
    conn.close()

    print("📥 Received:", process, score)

    # 🚨 TELEGRAM ALERT (WITH COOLDOWN)
    if score >= 90 and should_alert(process):
        send_telegram(
            f"🚨 HIGH THREAT!\n"
            f"Process: {process}\n"
            f"Score: {score}"
        )

    return jsonify({"status": "saved"})

# -----------------------------
# 📊 DASHBOARD
# -----------------------------
@app.route("/")
def dashboard():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT process, score FROM logs ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()

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
                background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
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
            canvas {{
                margin-top: 30px;
            }}
        </style>
    </head>

    <body>

    <h1>🔥 AI Security Dashboard</h1>

    <h2>🔴 High: {high}</h2>
    <h2>🟡 Medium: {medium}</h2>
    <h2>🟢 Low: {low}</h2>

    <canvas id="chart" width="300" height="150"></canvas>

    <table>
        <tr>
            <th>Process</th>
            <th>Score</th>
        </tr>
    """

    for process, score in rows:
        color = "white"
        if score >= 90:
            color = "red"
        elif score > 30:
            color = "yellow"
        else:
            color = "lightgreen"

        html += f"<tr><td style='color:{color}'>{process}</td><td>{score}</td></tr>"

    html += f"""
    </table>

    <script>
        // 📊 GRAPH
        var ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: ['High', 'Medium', 'Low'],
                datasets: [{{
                    label: 'Threat Levels',
                    data: [{high}, {medium}, {low}],
                }}]
            }}
        }});

        // 🚨 ALERT ONLY ONCE
        if ({high} > 0 && !localStorage.getItem("alerted")) {{

            alert("🚨 HIGH THREAT DETECTED!");

            var audio = new Audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg");

            audio.play().catch(() => {{
                document.body.onclick = () => audio.play();
            }});

            localStorage.setItem("alerted", "true");
        }}

        // 🔄 RESET IF SAFE
        if ({high} === 0) {{
            localStorage.removeItem("alerted");
        }}

        // 🔁 AUTO REFRESH
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
