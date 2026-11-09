"""Mode « sans ESP32 » : utilise le WiFi et le Bluetooth du PC Windows.

WiFi      : commande Windows `netsh wlan show networks mode=bssid` (vrai scan).
Bluetooth : liste des appareils Bluetooth connus du PC (PowerShell Get-PnpDevice).
"""
import json
import re
import subprocess


def _run(cmd):
    out = subprocess.run(cmd, capture_output=True, timeout=30)
    raw = out.stdout
    for enc in ("utf-8", "cp850", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _auth(text):
    t = text.upper()
    if "WPA3" in t and "WPA2" in t:
        return "WPA2/WPA3-PSK"
    if "WPA3" in t:
        return "WPA3-PSK"
    if "WPA2" in t and ("ENTREPRISE" in t or "ENTERPRISE" in t):
        return "WPA2-ENTERPRISE"
    if "WPA2" in t:
        return "WPA2-PSK"
    if "WPA" in t:
        return "WPA-PSK"
    if "WEP" in t:
        return "WEP"
    if "OUVERT" in t or "OUVRIR" in t or "OPEN" in t:
        return "OPEN"
    return text.strip()


def parse_netsh(output):
    """Transforme la sortie de netsh (français ou anglais) en liste de réseaux."""
    devices, ssid, auth = [], "", ""
    current = None
    for line in output.splitlines():
        line = line.strip()
        m = re.match(r"^SSID\s+\d+\s*:\s*(.*)$", line)
        if m:
            ssid, auth = m.group(1).strip(), ""
            continue
        key, _, value = line.partition(":")
        k = key.strip().lower()
        value = value.strip()
        if k.startswith("authenti"):
            auth = _auth(value)
        elif re.match(r"^bssid\s+\d+", k):
            current = {"ssid": ssid, "bssid": line.split(":", 1)[1].strip(),
                       "channel": 0, "rssi": -100, "auth": auth or "?", "hidden": ssid == ""}
            devices.append(current)
        elif current and k == "signal":
            pct = int(re.sub(r"\D", "", value) or 0)
            current["rssi"] = int(pct / 2 - 100)  # conversion approximative % -> dBm
        elif current and k in ("canal", "channel"):
            current["channel"] = int(re.sub(r"\D", "", value) or 0)
    return devices


def scan_wifi():
    out = _run(["netsh", "wlan", "show", "networks", "mode=bssid"])
    if "localisation" in out.lower() or "location" in out.lower():
        raise RuntimeError("Windows bloque le scan WiFi : activez Paramètres > Confidentialité > Localisation.")
    return parse_netsh(out)


def scan_bluetooth():
    ps = ("Get-PnpDevice -Class Bluetooth | "
          "Where-Object { $_.InstanceId -match 'DEV_' } | "
          "Select-Object FriendlyName, InstanceId, Status | ConvertTo-Json")
    out = _run(["powershell", "-NoProfile", "-Command", ps]).strip()
    if not out:
        return []
    data = json.loads(out)
    if isinstance(data, dict):
        data = [data]
    devices = []
    for d in data:
        m = re.search(r"DEV_([0-9A-F]{12})", d.get("InstanceId", ""), re.I)
        mac = ":".join(m.group(1)[i:i + 2] for i in range(0, 12, 2)).lower() if m else "?"
        devices.append({"mac": mac, "name": d.get("FriendlyName", ""),
                        "rssi": "-", "status": d.get("Status", "")})
    return devices
