from flask import Flask, request, jsonify, render_template_string
import sqlite3

app = Flask(__name__)

# 🔹 Init DB
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

# 🔹 Receive data
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

    print("Saved:", data)

    return jsonify({"status": "saved"})


# 🔹 Dashboard
@app.route("/")
def dashboard():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    # ✅ Unique processes (no duplicate spam)
    cursor.execute("""
        SELECT process, MAX(score)
        FROM logs
        GROUP BY process
        ORDER BY MAX(score) DESC
        LIMIT 50
    """)

    rows = cursor.fetchall()
    conn.close()

    data = [{"process": r[0], "score": r[1]} for r in rows]

    # 🔥 Classification
    high = [d for d in data if d["score"] > 70]
    medium = [d for d in data if 40 <= d["score"] <= 70]
    low = [d for d in data if d["score"] < 40]

    # 🔥 HTML (SAFE VERSION - NO CRASH)
    html = """
    <html>
    <head>
    <title>AI Security Dashboard</title>

    <meta http-equiv="refresh" content="5">

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
    body {
        background: #0b1f3a;
        color: white;
        font-family: Arial;
        text-align: center;
    }

    table {
        margin: auto;
        border-collapse: collapse;
        width: 60%;
    }

    th, td {
        border: 1px solid white;
        padding: 8px;
    }
    </style>

    </head>
    <body>

    <h1>🔥 AI Security Dashboard</h1>
    """

    html += f"<h2 style='color:red;'>High: {len(high)}</h2>"
    html += f"<h2 style='color:yellow;'>Medium: {len(medium)}</h2>"
    html += f"<h2 style='color:lightgreen;'>Low: {len(low)}</h2>"

    html += """
    <canvas id="myChart"></canvas>

    <script>
    const data = {
        labels: ["High", "Medium", "Low"],
        datasets: [{
            label: "Threat Levels",
            data: [""" + str(len(high)) + "," + str(len(medium)) + "," + str(len(low)) + """],
            backgroundColor: ["red", "yellow", "green"]
        }]
    };

    new Chart(document.getElementById("myChart"), {
        type: "bar",
        data: data
    });
    </script>

    <table>
    <tr>
    <th>Process</th>
    <th>Score</th>
    </tr>
    """

    for d in data:
        if d["score"] > 70:
            color = "red"
        elif d["score"] >= 40:
            color = "yellow"
        else:
            color = "lightgreen"

        html += f"""
        <tr style="color:{color}">
            <td>{d['process']}</td>
            <td>{d['score']}</td>
        </tr>
        """

    html += """
    </table>

    </body>
    </html>
    """

    return render_template_string(html)


# 🔹 Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
