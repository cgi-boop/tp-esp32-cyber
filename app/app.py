"""Interface web CyberScan (TP Python & Cyber)."""
import os

import requests
from flask import Flask, jsonify, render_template, request

import cve
import db
import scanner

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:5001")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 Mo max par fichier


@app.route("/")
def index():
    return render_template("index.html")


# ---------- Scan de fichier ----------
@app.post("/api/scan/file")
def api_scan_file():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="Aucun fichier reçu. Choisissez un fichier puis relancez l'analyse."), 400
    result = scanner.scan_file(f.filename, f.read())
    saved = db.save_file_scan(result)
    result["id"], result["created_at"] = saved["id"], str(saved["created_at"])
    return jsonify(result)


@app.get("/api/scans/files")
def api_list_files():
    return jsonify(db.list_file_scans())


# ---------- CVE ----------
@app.get("/api/cve")
def api_cve_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify(error="Indiquez un mot-clé (ex. : openssl, wifi, bluetooth) ou * pour tout afficher."), 400
    results = cve.search_cves(q)
    db.save_cves(results, q)
    return jsonify(results)


@app.get("/api/cves")
def api_cve_saved():
    return jsonify(db.list_cves())


# ---------- WiFi / Bluetooth via ESP32 ----------
@app.post("/api/scan/<scan_type>")
def api_scan_network(scan_type):
    if scan_type not in ("wifi", "bluetooth"):
        return jsonify(error="Type de scan inconnu"), 404
    try:
        r = requests.get(f"{BRIDGE_URL}/{scan_type}", timeout=30)
        payload = r.json()
        if r.status_code != 200 or "error" in payload:
            return jsonify(error=payload.get("error", "Erreur du pont")), 502
        devices = payload.get("devices", [])
        source = payload.get("source", "ESP32")
    except requests.RequestException as e:
        return jsonify(error=("Le pont WiFi/Bluetooth ne répond pas. Relancez LANCER.bat "
                              f"et laissez sa fenêtre ouverte. ({e})")), 502
    saved = db.save_network_scan(scan_type, devices)
    return jsonify(id=saved["id"], created_at=str(saved["created_at"]), devices=devices, source=source)


@app.get("/api/scans/network")
def api_list_network():
    return jsonify(db.list_network_scans())


@app.get("/api/status")
def api_status():
    clam, _, _ = scanner.clamav_scan(b"ping")
    try:
        bridge = requests.get(f"{BRIDGE_URL}/status", timeout=3).ok
    except requests.RequestException:
        bridge = False
    return jsonify(clamav=clam, esp32_bridge=bridge, database=True)


@app.errorhandler(413)
def too_big(_):
    return jsonify(error="Fichier trop volumineux (20 Mo maximum)."), 413


if __name__ == "__main__":
    db.init_db()
    app.run(host="0.0.0.0", port=5000)
