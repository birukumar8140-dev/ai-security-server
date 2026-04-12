from flask import Flask, request, jsonify, session, redirect
import sqlite3
import requests
import time
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SESSION_PERMANENT"] = False

# -----------------------------
# TELEGRAM
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
# DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

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
# SIGNUP
# -----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = ""
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if not user or not pwd:
            error = "Fill all fields"
        else:
            hashed = generate_password_hash(pwd)
            try:
                conn = sqlite3.connect("data.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users VALUES (NULL, ?, ?)", (user, hashed))
                conn.commit()
                conn.close()
                return redirect("/login")
            except:
                error = "Username exists"

    return f"""
    <h2>Signup</h2>
    <div style="color:red">{error}</div>
    <form method="POST">
    <input name="username"><br><br>
    <input name="password" type="password"><br><br>
    <button>Signup</button>
    </form>
    """

# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (user,))
        result = cursor.fetchone()
        conn.close()

        if result and check_password_hash(result[0], pwd):
            session["user"] = user
            return redirect("/")
        else:
            error = "Wrong credentials"

    return f"""
    <h2>Login</h2>
    <div style="color:red">{error}</div>
    <form method="POST">
    <input name="username"><br><br>
    <input name="password" type="password"><br><br>
    <button>Login</button>
    </form>
    """

# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -----------------------------
# BLOCK
# -----------------------------
@app.route("/block", methods=["POST"])
def block_ip():
    if "user" not in session:
        return "Unauthorized"

    ip = request.json.get("ip")
    os.system(f'netsh advfirewall firewall add rule name="Block {ip}" dir=out action=block remoteip={ip}')
    return jsonify({"status": "blocked"})

# -----------------------------
# UNBLOCK
# -----------------------------
@app.route("/unblock", methods=["POST"])
def unblock_ip():
    if "user" not in session:
        return "Unauthorized"

    ip = request.json.get("ip")
    os.system(f'netsh advfirewall firewall delete rule name="Block {ip}"')
    return jsonify({"status": "unblocked"})

# -----------------------------
# DASHBOARD
# -----------------------------
@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT process, score, action FROM logs ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()

    html = """
    <html>
    <body style="background:#0f2027;color:white;text-align:center;">
    <h1>🔥 AI Security Dashboard</h1>
    <a href="/logout">Logout</a>

    <table border="1" style="margin:auto;width:90%;">
    <tr>
    <th>IP</th>
    <th>Score</th>
    <th>Action</th>
    <th>Control</th>
    </tr>
    """

    for p, s, a in rows:
        html += f"""
        <tr>
        <td>{p}</td>
        <td>{s}</td>
        <td>{a}</td>
        <td>
        <button onclick="blockIP('{p}')">Block</button>
        <button onclick="unblockIP('{p}')">Unblock</button>
        </td>
        </tr>
        """

    html += """
    </table>

    <script>
    function blockIP(ip){
        fetch("/block",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ip:ip})});
    }
    function unblockIP(ip){
        fetch("/unblock",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ip:ip})});
    }
    </script>

    </body>
    </html>
    """

    return html

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
