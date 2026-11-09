# TP Python & Cyber — CyberScan

> Tout est expliqué pas à pas dans **GUIDE-COMPLET.md**.

Application web Python (Flask) qui :
- analyse un fichier : **sain, suspect ou malveillant** (ClamAV + heuristique) ;
- liste les **CVE** avec une **solution** (API NVD, ou base locale sans Internet) ;
- scanne le **WiFi** et le **Bluetooth** (carte WiFi du PC, ou ESP32 en option) ;
- **sauvegarde** tout dans **PostgreSQL** ;
- tourne dans **Docker Desktop** (conteneurs `web`, `db`, `clamav`).

## Démarrage rapide (Windows)
1. Installer Python (cocher « Add to PATH »), Docker Desktop, Git.
2. Activer la localisation Windows (nécessaire au scan WiFi).
3. Docker Desktop ouvert → double-clic sur **PREPARER.bat** (une fois, avec Internet).
4. Double-clic sur **LANCER.bat** → ouvrir http://localhost:5000
5. Éteindre : **ARRETER.bat**

## Architecture
```
Navigateur ──► web (Flask :5000) ──► db (PostgreSQL)
                  │        ├───────► clamav (:3310)
                  │        └───────► API NVD / base locale
                  └──► host.docker.internal:5001
                           │
              bridge/esp32_bridge.py (Windows) ──► WiFi/Bluetooth du PC
                                               └─► ESP32 en USB (option)
```

## IA
Utilisation d'IA autorisée : tous les prompts sont dans `prompts/README.md`.
