@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === LANCEMENT DE CYBERSCAN ===
start "Pont WiFi-Bluetooth (laisser ouvert)" cmd /k python bridge\esp32_bridge.py
echo Ouvrez http://localhost:5000 quand le texte arrete de defiler.
docker compose up
pause
