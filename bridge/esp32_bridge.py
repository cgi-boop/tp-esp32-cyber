"""Pont WiFi/Bluetooth <-> site web (à lancer sur Windows, hors Docker).

Par défaut : utilise le WiFi et le Bluetooth du PC (aucun matériel en plus).
Option : si un ESP32 est branché en USB (et pyserial installé), il est utilisé.

Pourquoi ? Docker Desktop sous Windows ne donne pas accès aux ports COM
depuis un conteneur. Ce script lit l'ESP32 en série et expose une petite API
HTTP sur le port 5001 que le conteneur `web` appelle via host.docker.internal.

Usage :  python esp32_bridge.py            (détection auto du port COM)
         python esp32_bridge.py COM5       (port forcé)
         python esp32_bridge.py --pc       (sans ESP32 : WiFi/Bluetooth du PC)
Si aucun ESP32 n'est trouvé, le mode PC est activé automatiquement.
"""
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pc_scan

try:  # pyserial n'est utile que pour l'option ESP32
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

BAUD = 115200
PORT_HTTP = 5001
lock = threading.Lock()
ser = None
MODE = "esp32"  # ou "pc"


def find_port():
    if serial is None:
        return None
    for p in serial.tools.list_ports.comports():
        desc = f"{p.description} {p.manufacturer}".lower()
        if any(k in desc for k in ("cp210", "ch340", "ch910", "usb serial", "silicon labs", "esp32", "usb-serial")):
            return p.device
    return None


def open_serial(port):
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = port, BAUD, 1
    s.dtr = False  # évite le reset de l'ESP32 à l'ouverture
    s.rts = False
    s.open()
    time.sleep(2)
    s.reset_input_buffer()
    return s


def ask_esp32(command, timeout=20):
    with lock:
        ser.reset_input_buffer()
        ser.write((command + "\r\n").encode())
        end = time.time() + timeout
        while time.time() < end:
            line = ser.readline().decode(errors="ignore").strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    raise TimeoutError("Pas de réponse de l'ESP32 (main.py bien chargé ?)")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        routes = {"/wifi": "WIFI", "/bluetooth": "BLE", "/status": "PING"}
        cmd = routes.get(self.path)
        if not cmd:
            return self._send(404, {"error": "route inconnue"})
        try:
            if MODE == "pc":
                if cmd == "WIFI":
                    data = {"type": "wifi", "devices": pc_scan.scan_wifi()}
                elif cmd == "BLE":
                    data = {"type": "bluetooth", "devices": pc_scan.scan_bluetooth()}
                else:
                    data = {"type": "pong", "devices": []}
                data["source"] = "PC Windows (sans ESP32)"
            else:
                data = ask_esp32(cmd)
                data["source"] = "ESP32"
            print(f"[pont] {cmd} -> {len(data.get('devices', []))} appareil(s)")
            self._send(200, data)
        except Exception as e:
            self._send(500, {"error": str(e)})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    port = None if arg == "--pc" else (arg or find_port())
    if port:
        try:
            ser = open_serial(port)
            print(f"[pont] ESP32 sur {port}, API sur http://localhost:{PORT_HTTP}")
        except Exception as e:
            print(f"[pont] Impossible d'ouvrir {port} ({e})")
            port = None
    if not port:
        MODE = "pc"
        print(f"[pont] Mode PC : WiFi et Bluetooth de l'ordinateur, API sur http://localhost:{PORT_HTTP}")
        print("[pont] Laissez cette fenêtre ouverte.")
    ThreadingHTTPServer(("0.0.0.0", PORT_HTTP), Handler).serve_forever()
