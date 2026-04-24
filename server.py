# BharatShield server

import os
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")


# =====================================================
# DB
# =====================================================

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id SERIAL PRIMARY KEY,
        device_id TEXT UNIQUE,
        hostname TEXT,
        os TEXT,
        ip TEXT,
        cpu REAL DEFAULT 0,
        ram REAL DEFAULT 0,
        version TEXT,
        status TEXT DEFAULT 'online',
        last_seen TIMESTAMP DEFAULT NOW(),
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id SERIAL PRIMARY KEY,
        device_id TEXT,
        device_name TEXT,
        hostname TEXT,
        threat_type TEXT,
        category TEXT,
        process TEXT,
        score INTEGER,
        severity TEXT,
        action TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS commands (
        id SERIAL PRIMARY KEY,
        device_id TEXT,
        command TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    conn.commit()
    conn.close()


init_db()


# =====================================================
# HELPERS
# =====================================================

def severity_from_score(score):
    if score >= 90:
        return "Critical"
    elif score >= 70:
        return "High"
    elif score >= 50:
        return "Medium"
    return "Low"


# =====================================================
# HEALTH
# =====================================================

@app.route("/")
def home():
    return jsonify({
        "name": "BharatShield API",
        "status": "online",
        "time": str(datetime.now(timezone.utc))
    })


# =====================================================
# CHECKIN
# =====================================================

@app.route("/api/checkin", methods=["POST"])
def checkin():
    data = request.json

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO devices
    (device_id, hostname, os, ip, cpu, ram, version, last_seen, status)
    VALUES (%s,%s,%s,%s,%s,%s,%s,NOW(),'online')
    ON CONFLICT (device_id)
    DO UPDATE SET
        hostname=EXCLUDED.hostname,
        os=EXCLUDED.os,
        ip=EXCLUDED.ip,
        cpu=EXCLUDED.cpu,
        ram=EXCLUDED.ram,
        version=EXCLUDED.version,
        last_seen=NOW(),
        status='online'
    """, (
        data.get("device_id"),
        data.get("hostname"),
        data.get("os"),
        data.get("ip"),
        data.get("cpu", 0),
        data.get("ram", 0),
        data.get("version", "1.0")
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


# =====================================================
# ALERT RECEIVE
# =====================================================

@app.route("/api/alert", methods=["POST"])
def receive_alert():
    data = request.json

    score = int(data.get("score", 0))
    severity = data.get("severity") or severity_from_score(score)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO alerts
    (
      device_id,
      device_name,
      hostname,
      threat_type,
      category,
      process,
      score,
      severity,
      action
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data.get("device_id"),
        data.get("device_name"),
        data.get("hostname"),
        data.get("type"),
        data.get("category"),
        data.get("process"),
        score,
        severity,
        data.get("action", "detected")
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})


# =====================================================
# DEVICES
# =====================================================

@app.route("/api/devices")
def devices():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM devices
    ORDER BY last_seen DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return jsonify(rows)


# =====================================================
# ALERTS
# =====================================================

@app.route("/api/alerts")
def alerts():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        id,
        device_id,
        device_name,
        hostname,
        threat_type AS type,
        category,
        process,
        score,
        severity,
        action,
        created_at
    FROM alerts
    ORDER BY created_at DESC
    LIMIT 100
    """)

    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)


# =====================================================
# COMMAND SEND
# =====================================================

@app.route("/api/command", methods=["POST"])
def send_command():
    data = request.json

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO commands (device_id, command)
    VALUES (%s,%s)
    """, (
        data.get("device_id"),
        data.get("command")
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "queued"})


# =====================================================
# COMMAND FETCH
# =====================================================

@app.route("/api/commands/<device_id>")
def get_commands(device_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM commands
    WHERE device_id=%s AND status='pending'
    ORDER BY id ASC
    """, (device_id,))

    rows = cur.fetchall()
    ids = [r["id"] for r in rows]

    if ids:
        cur.execute("""
        UPDATE commands
        SET status='sent'
        WHERE id = ANY(%s)
        """, (ids,))

    conn.commit()
    conn.close()

    return jsonify(rows)


# =====================================================
# RESET ALERTS (ONE CLICK CLEANUP)
# =====================================================

@app.route("/api/reset-alerts", methods=["POST"])
def reset_alerts():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM alerts")

    conn.commit()
    conn.close()

    return jsonify({"status": "alerts cleared"})


# =====================================================
# STATS
# =====================================================

@app.route("/api/stats")
def stats():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS c FROM devices")
    devices = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM alerts")
    alerts = cur.fetchone()["c"]

    cur.execute("""
    SELECT COUNT(*) AS c
    FROM alerts
    WHERE severity='Critical'
    """)
    critical = cur.fetchone()["c"]

    conn.close()

    return jsonify({
        "devices": devices,
        "alerts": alerts,
        "critical": critical
    })


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
