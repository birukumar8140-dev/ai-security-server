from flask import Flask, request, jsonify, render_template_string
import sqlite3

app = Flask(__name__)

# 🔹 Create DB if not exists
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

# 🔹 Receive data from scanner
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

    print("✅ Saved:", data)

    return jsonify({"status": "saved"})


# 🔹 Dashboard UI
@app.route("/")
def dashboard():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

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

    html = f"""
    <html>
    <head>
        <title>AI Security Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{
                background: #0b1f3a;
                color: white;
                font-family: Arial;
                text-align: center;
            }}
            table {{
                margin: auto;
                border-collapse: collapse;
                width: 60%;
            }}
            th, td {{
                border: 1px solid white;
                padding: 8px;
            }}
            th {{
                background: #1f3f6b;
            }}
            .high {{ color: red; }}
            .medium {{ color: yellow; }}
            .low {{ color: lightgreen; }}
        </style>
    </head>
    <body>

        <h1>🔥 AI Security Dashboard</h1>

        <h2 class="high">🔴 High: {len(high)}</h2>
        <h2 class="medium">🟡 Medium: {len(medium)}</h2>
        <h2 class="low">🟢 Low: {len(low)}</h2>

        <table>
            <tr>
                <th>Process</th>
                <th>Score</th>
            </tr>
    """

    for d in data:
        if d["score"] > 70:
            cls = "high"
        elif d["score"] >= 40:
            cls = "medium"
        else:
            cls = "low"

        html += f"""
            <tr class="{cls}">
                <td>{d["process"]}</td>
                <td>{d["score"]}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return render_template_string(html)


# 🔹 Run server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
