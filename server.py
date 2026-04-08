from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# 🔐 Login
USERNAME = "admin"
PASSWORD = "1234"
logged_in = False

# 📦 DB INIT
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

# 📥 Receive data
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

    print("📥 Saved:", data)

    return jsonify({"status": "saved"})

# 🔐 Login
@app.route("/login", methods=["GET", "POST"])
def login():
    global logged_in

    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if user == USERNAME and pwd == PASSWORD:
            logged_in = True
            return redirect(url_for("dashboard"))

    return """
    <h2>Login</h2>
    <form method="post">
        Username: <input name="username"><br><br>
        Password: <input name="password" type="password"><br><br>
        <button type="submit">Login</button>
    </form>
    """

# 🌐 Dashboard
@app.route("/")
def dashboard():
    global logged_in

    if not logged_in:
        return redirect(url_for("login"))

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT process, score FROM logs ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()

    conn.close()

    high = [r for r in rows if r[1] >= 70]
    medium = [r for r in rows if 40 <= r[1] < 70]

    html = """
    <html>
    <body style="background:#0f172a;color:white;text-align:center;">
        <h1>AI Security Dashboard</h1>

        <h2>🔴 High: {{high}}</h2>
        <h2>🟡 Medium: {{medium}}</h2>

        <table border="1" style="margin:auto;">
        <tr><th>Process</th><th>Score</th></tr>

        {% for row in rows %}
        <tr>
            <td>{{row[0]}}</td>
            <td>{{row[1]}}</td>
        </tr>
        {% endfor %}
        </table>
    </body>
    </html>
    """

    return render_template_string(
        html,
        rows=rows,
        high=len(high),
        medium=len(medium)
    )

# ▶ RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
