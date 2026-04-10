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
# 🚨 SMART ALERT MEMORY
# -----------------------------
alerted_processes = set()

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
            score INTEGER,
            device TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    process = data.get("process")
    score = data.get("score")
    device = data.get("device", "unknown")

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO logs (process, score, device)
        VALUES (?, ?, ?)
    """, (process, score, device))

    conn.commit()
    conn.close()

    print(f"📥 {device} → {process} ({score})")

    # 🚨 SMART TELEGRAM ALERT
    if score > 70:
        if process not in alerted_processes:
            alerted_processes.add(process)

            send_telegram(
                f"🚨 NEW THREAT!\nDevice: {device}\nProcess: {process}\nScore: {score}"
            )

    # reset 
    if score < 40:
        alerted_processes.discard(process)

    return jsonify({"status": "saved"})

# -----------------------------
# 📊 Dashboard
# -----------------------------
@app.route("/")
def dashboard():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT process, score FROM logs
        ORDER BY id DESC LIMIT 50
    """)
    rows = cursor.fetchall()

    conn.close()

    high = sum(1 for r in rows if r[1] > 70)
    medium = sum(1 for r in rows if 30 < r[1] <= 70)
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
                width: 70%;
            }}
            th, td {{
                border: 1px solid white;
                padding: 10px;
            }}
            canvas {{
                max-width: 400px;
                margin: auto;
            }}
        </style>
    </head>

    <body>

    <h1>🔥 AI Security Dashboard</h1>

    <h2>🔴 High: {high}</h2>
    <h2>🟡 Medium: {medium}</h2>
    <h2>🟢 Low: {low}</h2>

    <canvas id="chart"></canvas>

    <table>
        <tr>
            <th>Process</th>
            <th>Score</th>
        </tr>
    """

    for process, score in rows:
        color = "white"
        if score > 70:
            color = "red"
        elif score > 30:
            color = "yellow"
        else:
            color = "lightgreen"

        html += f"<tr><td style='color:{color}'>{process}</td><td>{score}</td></tr>"

    html += f"""
    </table>

    <script>
        let high = {high};
        let medium = {medium};
        let low = {low};

        // 📊 GRAPH
        const ctx = document.getElementById('chart');

        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: ['High', 'Medium', 'Low'],
                datasets: [{{
                    label: 'Threat Levels',
                    data: [high, medium, low],
                    backgroundColor: ['red', 'yellow', 'green']
                }}]
            }}
        }});

        // 🔊 SOUND
        function playAlarm() {{
            let audio = new Audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg");
            audio.loop = true;

            audio.play().catch(() => {{
                document.body.addEventListener("click", () => {{
                    audio.play();
                }});
            }});
        }}

        // 🚨 ALERT
        if (high > 0) {{
            if (!localStorage.getItem("alerted")) {{
                alert("🚨 HIGH THREAT DETECTED!");
                playAlarm();
                localStorage.setItem("alerted", "yes");
            }}
        }} else {{
            localStorage.removeItem("alerted");
        }}

        // 🔄 AUTO REFRESH
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
