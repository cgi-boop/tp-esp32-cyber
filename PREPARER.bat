@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === PREPARATION : a faire UNE fois, AVEC Internet ===
echo Docker Desktop doit etre ouvert.
docker compose build
docker compose pull db clamav
docker compose up -d
echo.
echo Termine. Laissez tourner 5 minutes : ClamAV telecharge sa liste de virus.
echo Ensuite vous pouvez tester avec LANCER.bat
pause
