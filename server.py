from flask import Flask, request, jsonify, render_template_string
import sqlite3

app = Flask(__name__)

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
                background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
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

            .high {{ color: red; }}
            .medium {{ color: yellow; }}
            .low {{ color: lightgreen; }}
        </style>
    </head>

    <body>

    <h1>🔥 AI Security Dashboard</h1>

    <h2 class="high">🔴 High: {high}</h2>
    <h2 class="medium">🟡 Medium: {medium}</h2>
    <h2 class="low">🟢 Low: {low}</h2>

    <canvas id="chart" width="400" height="200"></canvas>

    <table>
        <tr>
            <th>Process</th>
            <th>Score</th>
        </tr>
    """

    for process, score in rows:
        if score > 70:
            color = "red"
        elif score > 30:
            color = "yellow"
        else:
            color = "lightgreen"

        html += f"<tr><td>{process}</td><td style='color:{color}'>{score}</td></tr>"

    html += f"""
    </table>

    <!-- 🔊 SOUND -->
    <audio id="alertSound">
        <source src="https://www.soundjay.com/buttons/sounds/beep-07.mp3" type="audio/mpeg">
    </audio>

    <!-- 🚨 ALERT SCRIPT -->
    <script>
        var high = {high};

        if (high > 0) {{
            alert("🚨 HIGH THREAT DETECTED! (Click anywhere for sound)");
        }}

        // 🔊 SOUND ON CLICK (100% WORKING)
        document.body.addEventListener("click", function () {{
            var audio = document.getElementById("alertSound");
            audio.play().catch(() => console.log("Sound blocked"));
        }});

        // 🔄 AUTO REFRESH
        setTimeout(() => {{
            location.reload();
        }}, 5000);
    </script>

    <!-- 📊 GRAPH -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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

    </body>
    </html>
    """

    return html

# -----------------------------
# 🚀 Run
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
