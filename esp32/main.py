# Firmware MicroPython pour ESP32
# Attend une commande sur le port série USB : "WIFI" ou "BLE"
# et répond par une ligne JSON : {"type": "...", "devices": [...]}
import sys
import time
import json
import network
import ubinascii
import bluetooth

AUTH = {0: "OPEN", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK",
        5: "WPA2-ENTERPRISE", 6: "WPA3-PSK", 7: "WPA2/WPA3-PSK"}


def scan_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    devices = []
    for ssid, bssid, channel, rssi, auth, hidden in wlan.scan():
        try:
            name = ssid.decode()
        except Exception:
            name = "?"
        devices.append({
            "ssid": name,
            "bssid": ubinascii.hexlify(bssid, ":").decode(),
            "channel": channel,
            "rssi": rssi,
            "auth": AUTH.get(auth, str(auth)),
            "hidden": bool(hidden),
        })
    return devices


_found = {}


def _adv_name(payload):
    i = 0
    while i + 1 < len(payload):
        length = payload[i]
        if length == 0:
            break
        if payload[i + 1] in (0x08, 0x09):  # nom court / nom complet
            try:
                return bytes(payload[i + 2:i + 1 + length]).decode()
            except Exception:
                return ""
        i += 1 + length
    return ""


def _irq(event, data):
    if event == 5:  # _IRQ_SCAN_RESULT
        addr_type, addr, adv_type, rssi, adv_data = data
        mac = ubinascii.hexlify(bytes(addr), ":").decode()
        name = _adv_name(bytes(adv_data))
        old = _found.get(mac)
        if old is None or (name and not old["name"]):
            _found[mac] = {"mac": mac, "rssi": rssi, "name": name}


def scan_ble(duration_ms=5000):
    _found.clear()
    ble = bluetooth.BLE()
    ble.active(True)
    ble.irq(_irq)
    ble.gap_scan(duration_ms, 30000, 30000)
    time.sleep_ms(duration_ms + 500)
    ble.active(False)
    return list(_found.values())


while True:
    cmd = sys.stdin.readline().strip().upper()
    try:
        if cmd == "WIFI":
            print(json.dumps({"type": "wifi", "devices": scan_wifi()}))
        elif cmd == "BLE":
            print(json.dumps({"type": "bluetooth", "devices": scan_ble()}))
        elif cmd == "PING":
            print(json.dumps({"type": "pong", "devices": []}))
    except Exception as e:
        print(json.dumps({"type": "error", "error": str(e), "devices": []}))
