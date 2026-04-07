from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import os

app = Flask(__name__)

# 📦 Data store
data_store = []

# 🔐 Login credentials
USERNAME = "admin"
PASSWORD = "1234"
logged_in = False

# 📥 Receive data from agent
@app.route("/data", methods=["POST"])
def receive_data():
    data = request.json
    data_store.append(data)

    print("📥 Data Received:", data)

    return jsonify({"status": "success"})

# 🔐 Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    global logged_in

    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if user == USERNAME and pwd == PASSWORD:
            logged_in = True
            return redirect(url_for("dashboard_ui"))

    return """
    <html>
    <body style="font-family:Arial;text-align:center;margin-top:100px;">
        <h2>🔐 Login</h2>
        <form method="post">
            <input name="username" placeholder="Username"><br><br>
            <input name="password" type="password" placeholder="Password"><br><br>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """

# 🌐 Dashboard UI
@app.route("/")
def dashboard_ui():
    global logged_in

    if not logged_in:
        return redirect(url_for("login"))

    high = [d for d in data_store if d["score"] >= 70]
    medium = [d for d in data_store if 40 <= d["score"] < 70]

    html = """
    <html>
    <head>
        <title>AI Security Dashboard</title>
        <style>
            body {
                font-family: Arial;
                background: #0f172a;
                color: white;
                text-align: center;
            }
            .container {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin: 20px;
            }
            .card {
                padding: 20px;
                border-radius: 10px;
                width: 150px;
                font-size: 18px;
            }
            .safe { background: green; }
            .medium { background: orange; }
            .high { background: red; }
            table {
                margin: auto;
                margin-top: 20px;
                border-collapse: collapse;
                width: 60%;
            }
            th, td {
                padding: 10px;
                border: 1px solid white;
            }
        </style>
    </head>

    <body>
        <h1>🛡️ AI Security Dashboard</h1>

        <div class="container">
            <div class="card safe">
                🟢 SAFE<br>{{total - high_count - medium_count}}
            </div>
            <div class="card medium">
                🟡 MEDIUM<br>{{medium_count}}
            </div>
            <div class="card high">
                🔴 HIGH<br>{{high_count}}
            </div>
        </div>

        <h2>Threat Logs</h2>

        <table>
            <tr>
                <th>Process</th>
                <th>Score</th>
            </tr>

            {% for item in data %}
            <tr>
                <td>{{item.process}}</td>
                <td>{{item.score}}%</td>
            </tr>
            {% endfor %}
        </table>

    </body>
    </html>
    """

    return render_template_string(
        html,
        total=len(data_store),
        high_count=len(high),
        medium_count=len(medium),
        data=data_store
    )

# ▶ RUN SERVER (DEPLOY READY)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))