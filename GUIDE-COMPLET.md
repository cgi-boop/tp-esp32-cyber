# Guide complet — CyberScan (version sans ESP32)

Tout est expliqué simplement. Ce guide marche **sans Internet** :
ouvre-le avec le Bloc-notes.

Le projet fonctionne **sans ESP32 et sans câble** : il utilise le WiFi et le
Bluetooth de ton ordinateur. Si un jour tu as un ESP32, voir l'ANNEXE à la fin.

---

## PARTIE 1 — CE QUE TU DOIS FAIRE, ÉTAPE PAR ÉTAPE

### ÉTAPE 0 — Récupérer les fichiers sur l'ordinateur
1. Sur l'ordinateur, ouvre Chrome et va sur claude.ai (même compte que ton téléphone).
2. Ouvre la conversation et télécharge `tp-esp32-cyber.zip` et les 2 PowerPoint.
3. Ils arrivent dans le dossier **Téléchargements**.

### ÉTAPE 1 — Créer le dossier du projet
1. Appuie sur **Windows + E** pour ouvrir tes dossiers.
2. Va dans **Téléchargements**.
3. **Clic droit** sur `tp-esp32-cyber.zip`, puis **Extraire tout…**
4. Dans la case du chemin, efface tout et écris : `C:\`
5. Clique sur **Extraire**.
→ Tu as maintenant le dossier **`C:\tp-esp32-cyber`**. C'est ton projet.

### ÉTAPE 2 — Installer 3 programmes
- **Python** (python.org) → ⚠️ coche **« Add python.exe to PATH »** puis Install Now.
  *Sert à : faire tourner le petit programme qui scanne le WiFi.*
- **Docker Desktop** (docker.com) → installe, puis **redémarre l'ordinateur**.
  *Sert à : allumer le site, la base de données et l'antivirus.*
- **Git** (git-scm.com) → Next partout.
  *Sert à : sauvegarder le projet (le prof l'exige).*

### ÉTAPE 3 — Autoriser le scan WiFi dans Windows
Paramètres Windows → **Confidentialité et sécurité** → **Localisation** → **Activé**.
*Pourquoi : Windows 11 demande cette autorisation pour lister les WiFi autour.*

### ÉTAPE 4 — Préparer (UNE fois, AVEC Internet)
1. Ouvre **Docker Desktop** (la baleine 🐳) et attends « Engine running ».
2. Dans `C:\tp-esp32-cyber`, **double-clique sur `PREPARER.bat`**.
3. Attends que ce soit fini (5 à 10 minutes), puis encore 5 minutes.
*Sert à : télécharger tout ce dont Docker a besoin. Après ça, plus besoin d'Internet.*

### ÉTAPE 5 — Lancer le projet
1. Docker Desktop ouvert.
2. **Double-clique sur `LANCER.bat`**.
   → 2 fenêtres noires s'ouvrent. **Ne les ferme pas.**
3. Ouvre Chrome et tape : **`localhost:5000`**
→ Le site apparaît. ✅

### ÉTAPE 6 — Tester
1. Ouvre le dossier `C:\tp-esp32-cyber\samples`.
2. Clique dans la barre d'adresse en haut, tape `cmd`, Entrée, puis tape :
   `python make_samples.py` puis Entrée.
   → 3 fichiers de test sont créés.
3. Sur le site :
   - **Analyser un fichier** : `rapport.txt` → SAIN, `facture.pdf.exe` → SUSPECT, `eicar.com` → MALVEILLANT
     (si Windows supprime eicar.com, c'est normal : ça prouve que c'est un « virus » de test)
   - **CVE** : tape `wifi` → les failles et leurs solutions
   - **Scan WiFi** → les WiFi autour de toi
   - **Scan Bluetooth** → les appareils Bluetooth connus de l'ordinateur
   - **Historique** → tout est enregistré
🎉 Ton projet marche.

### ÉTAPE 7 — Sauvegarder avec Git
Dans `C:\tp-esp32-cyber`, clique dans la barre d'adresse, tape `powershell`, Entrée, puis :
```
git config --global user.name "Chaima Ghezali"
git config --global user.email "ton.email@exemple.com"
git init
git add .
git commit -m "TP Python et Cyber"
```

### ÉTAPE 8 — Les prompts IA (obligatoire)
1. Ouvre `prompts\README.md` avec le Bloc-notes.
2. Vérifie que tous tes messages à l'IA sont dedans, ajoute ceux qui manquent, Ctrl + S.
3. Dans PowerShell : `git add .` puis `git commit -m "prompts"`

### ÉTAPE 9 — Rendre (avec Internet)
1. github.com → crée un compte → **+** → **New repository** → nom `tp-esp32-cyber` → Create.
2. Copie le lien qui finit par `.git`. Dans PowerShell :
```
git remote add origin COLLE_LE_LIEN
git branch -M main
git push -u origin main
```
3. Classroom → le devoir → **Ajouter le devoir** → **Lien** → colle le lien GitHub → **Rendre**.

### LE JOUR DE LA PRÉSENTATION (sans Internet)
1. Ouvrir Docker Desktop.
2. Double-cliquer sur `LANCER.bat`.
3. Chrome : `localhost:5000`.
4. Montrer les diapos, lire les **Notes** sous chaque diapo.
5. Pour éteindre : `ARRETER.bat`.

---

## PARTIE 2 — À QUOI SERT LE PROJET

C'est un **outil de cybersécurité**, comme un petit antivirus fait maison. Il fait 4 choses :
1. Dire si un **fichier est un virus**.
2. Montrer les **failles de sécurité (CVE)** des logiciels, avec une solution.
3. Scanner le **WiFi** et le **Bluetooth** autour de l'ordinateur et signaler les WiFi dangereux.
4. **Tout sauvegarder** dans une base de données.

### Le schéma
```
  Navigateur (toi)
       │
       ▼
  Conteneur WEB (Flask) ──► Conteneur DB (PostgreSQL) : la mémoire
       │      └──────────► Conteneur CLAMAV : l'antivirus
       │      └──────────► API NVD (CVE, si Internet) / base locale
       ▼
  Pont (script Python sur Windows) ──► WiFi et Bluetooth du PC
                                    └─► (option) ESP32 en USB
```

### Les 3 conteneurs Docker
Un **conteneur** = une boîte qui contient un programme et tout ce dont il a besoin.
- **web** : le site en Python (Flask). Le cerveau.
- **db** : la base de données PostgreSQL. La mémoire.
- **clamav** : un vrai antivirus gratuit. Le détecteur.

### Pourquoi un « pont » hors de Docker ?
Un conteneur Docker est **isolé** : il ne voit pas la carte WiFi ni le Bluetooth de Windows.
Le pont est un petit programme Python qui tourne **directement sur Windows** :
1. le site lui demande « scanne le WiFi » (adresse `host.docker.internal`, port 5001) ;
2. le pont lance la commande Windows `netsh wlan show networks mode=bssid` ;
3. il transforme le résultat en JSON et le renvoie au site, qui l'enregistre.
Pour le Bluetooth, il utilise la commande PowerShell `Get-PnpDevice -Class Bluetooth`.

---

## PARTIE 3 — CHAQUE FICHIER EXPLIQUÉ

| Fichier | Rôle |
|---|---|
| `PREPARER.bat` | Télécharge et construit tout (une fois, avec Internet) |
| `LANCER.bat` | Lance le pont + Docker |
| `ARRETER.bat` | Éteint Docker |
| `docker-compose.yml` | Décrit les 3 conteneurs |
| `app/Dockerfile` | Recette du conteneur web |
| `app/app.py` | Le serveur web : reçoit les demandes, répond en JSON |
| `app/scanner.py` | Le détecteur de virus |
| `app/cve.py` | La recherche de failles + solutions |
| `app/db.py` | La base de données |
| `app/data/cves_offline.json` | 20 CVE célèbres pour travailler sans Internet |
| `app/templates/index.html` | La page web |
| `app/static/style.css` | Les couleurs et la mise en page |
| `bridge/esp32_bridge.py` | Le pont entre le site et le WiFi/Bluetooth |
| `bridge/pc_scan.py` | Le scan WiFi/Bluetooth avec l'ordinateur |
| `esp32/main.py` | (option) Programme pour un ESP32 |
| `samples/make_samples.py` | Crée les fichiers de test |
| `prompts/README.md` | Les prompts IA (obligatoire) |

### app.py — les adresses du site
| Adresse | Rôle |
|---|---|
| `/` | Affiche la page |
| `/api/scan/file` | Analyse un fichier et l'enregistre |
| `/api/cve?q=...` | Cherche des CVE et les enregistre |
| `/api/scan/wifi` et `/api/scan/bluetooth` | Demande un scan au pont et l'enregistre |
| `/api/scans/files`, `/api/scans/network`, `/api/cves` | L'historique |
| `/api/status` | Les voyants (ClamAV, pont, base) |

### scanner.py — comment on détecte un virus
**1. ClamAV** compare le fichier à des millions de signatures (empreintes de virus connus).
**2. Analyse heuristique** : on cherche des indices, chacun ajoute des points :

| Indice | Points |
|---|---|
| Hash SHA-256 d'un virus connu | +100 |
| Signature EICAR (faux virus de test) | +100 |
| Double extension (`facture.pdf.exe`) | +40 |
| Exécutable Windows caché (commence par « MZ ») | +40 |
| Exécutable Linux caché (« ELF ») | +30 |
| Chaîne suspecte (`cmd.exe /c`, `powershell -enc`…) | +25 chacune |
| Entropie très élevée | +20 |
| Extension dangereuse (.exe, .bat, .vbs…) | +15 |

**Verdict** : ClamAV trouve un virus ou score ≥ 70 → **MALVEILLANT** ; 30 à 69 → **SUSPECT** ; moins de 30 → **SAIN**.

- **Hash** : l'empreinte digitale d'un fichier. Un octet change → le hash change complètement.
- **Entropie** : le « désordre » des données, de 0 à 8. Texte ≈ 4-5. Fichier chiffré ≈ 8.
- **EICAR** : un faux virus officiel et inoffensif pour tester les antivirus.

### cve.py — les failles
- **CVE** : numéro unique d'une faille (CVE-2014-0160 = Heartbleed).
- **CVSS** : gravité de 0 à 10 (LOW, MEDIUM, HIGH, CRITICAL).
- **CWE** : le type de faille (CWE-89 = injection SQL).
1. Avec Internet → API officielle NVD.
2. Sans Internet → base locale de 20 CVE (bascule automatique).
3. Solution proposée selon le CWE + lien du correctif officiel s'il existe.
Astuce : taper `*` affiche toutes les CVE locales.

### db.py — la base de données (3 tables)
| Table | Contenu |
|---|---|
| `file_scans` | fichier, hash, verdict, détails, date |
| `network_scans` | wifi/bluetooth, nombre d'appareils, résultats, date |
| `cves` | numéro, description, score, gravité, solution, date |
- Requêtes avec paramètres `%s` → protection contre l'**injection SQL**.
- `ON CONFLICT DO UPDATE` → pas de doublon de CVE.
- **JSONB** = du JSON rangé dans la base.

### pc_scan.py — le scan WiFi/Bluetooth
- **WiFi** : lit le résultat de `netsh` (en français ou en anglais) et récupère pour chaque réseau :
  **SSID** (nom), **BSSID** (adresse de la box), **canal**, **signal**, **sécurité**.
  Le signal en % est converti en dBm : `dBm = % / 2 − 100`.
  Les réseaux **OPEN** ou **WEP** sont signalés **risqués**.
- **Bluetooth** : liste les appareils Bluetooth connus du PC (nom, adresse MAC, état).

### index.html — l'interface
5 onglets, 3 voyants en haut, verdict affiché comme un tampon de couleur.
`fetch()` appelle l'API sans recharger la page. `esc()` protège contre le **XSS**.

---

## PARTIE 4 — SCÉNARIO DE DÉMO (5 minutes)
1. Montrer les 3 conteneurs dans Docker Desktop.
2. Analyser `rapport.txt` → SAIN, `facture.pdf.exe` → SUSPECT, `eicar.com` → MALVEILLANT.
3. CVE : chercher `wifi` puis `bluetooth`.
4. Scan WiFi : montrer les réseaux et ceux qui sont « risqués ».
5. Scan Bluetooth.
6. Historique : tout est sauvegardé.
7. Bonus : `docker compose exec db psql -U cyber -d cyberdb -c "SELECT filename, verdict FROM file_scans;"`
8. Montrer `git log` et le dossier `prompts`.

---

## PARTIE 5 — QUESTIONS DU PROF ET RÉPONSES

**Où est l'ESP32 ?**
« Je n'avais pas d'ESP32. Le projet utilise donc le WiFi et le Bluetooth de l'ordinateur via un pont.
Le code ESP32 est quand même prêt : si on en branche un, le pont l'utilise automatiquement. »

**Pourquoi Docker ?** Pour que le projet marche pareil sur tous les PC, chaque service isolé.

**Pourquoi le pont est hors de Docker ?** Un conteneur ne voit pas la carte WiFi ni le Bluetooth de Windows.

**Comment tu sais qu'un fichier est un virus ?** ClamAV (signatures) + heuristique (indices et score).

**Signature ou heuristique ?** Signature = virus déjà connu. Heuristique = comportement suspect,
même pour un virus nouveau, mais avec un risque de faux positif.

**C'est quoi un faux positif ?** Un fichier sain détecté comme dangereux.

**CVE, CVSS, CWE ?** Numéro de faille, note de gravité, type de faille.

**Ça marche sans Internet ?** Oui : ClamAV garde ses signatures, les CVE passent sur la base locale,
le WiFi est scanné par l'ordinateur.

**Comment tu protèges ton site ?** Requêtes SQL paramétrées, échappement HTML (XSS),
limite de 20 Mo, le fichier est seulement lu, jamais exécuté.

**Pourquoi un WiFi OPEN ou WEP est risqué ?** OPEN = aucune protection, tout le monde peut lire le trafic.
WEP = protection cassée depuis des années. Il faut WPA2 ou WPA3.

**Comment tu as utilisé l'IA ?** Pour la base du code, puis j'ai testé et compris. Prompts dans `prompts/`.

**Améliorations ?** Brancher un ESP32, mot de passe sur le site, export PDF, scan d'un dossier entier.

---

## PARTIE 6 — SI ÇA NE MARCHE PAS
| Problème | Solution |
|---|---|
| `LANCER.bat` se ferme tout de suite | Docker Desktop n'est pas ouvert : l'ouvrir et attendre « Engine running » |
| Voyant « pont » rouge | La fenêtre du pont a été fermée : relancer `LANCER.bat` |
| Scan WiFi : erreur localisation | Paramètres → Confidentialité → Localisation → Activé |
| Scan WiFi vide | Le WiFi de l'ordinateur est désactivé, ou c'est un PC fixe sans WiFi |
| Voyant ClamAV rouge | Attendre 5 minutes ; l'heuristique marche quand même |
| « python n'est pas reconnu » | Réinstaller Python en cochant « Add python.exe to PATH » |
| Port 5000 déjà utilisé | Dans `docker-compose.yml`, mettre `"5050:5000"` et aller sur localhost:5050 |
| Windows supprime `eicar.com` | Normal : le recréer juste avant la démo |

---

## PARTIE 7 — MOTS À CONNAÎTRE
- **API** : adresse qu'un programme appelle pour obtenir des données.
- **Flask** : bibliothèque Python pour faire un site web.
- **JSON** : format texte pour échanger des données `{"nom": "valeur"}`.
- **Port** : porte d'entrée d'un programme (5000 = site, 5001 = pont, 3310 = ClamAV, 5432 = base).
- **Conteneur / image / volume** : boîte isolée / modèle de boîte / dossier qui garde les données.
- **Git / commit / push** : historique du code / une sauvegarde / envoi en ligne.
- **SSID / BSSID / RSSI** : nom du WiFi / adresse de la box / force du signal en dBm.
- **Malware / ransomware** : logiciel malveillant / malware qui chiffre les fichiers contre rançon.
- **Injection SQL / XSS** : attaques qui glissent du code dans un formulaire ou une page web.

---

## ANNEXE — SI TU AS UN ESP32 (optionnel)
Un ESP32 est une petite carte électronique avec WiFi et Bluetooth, branchée avec un câble USB.
1. Installer **Thonny** (thonny.org) et faire `pip install pyserial`.
2. Thonny → Outils → Options → Interpréteur → MicroPython (ESP32) → Installer MicroPython.
3. Ouvrir `esp32/main.py` → Enregistrer sous → Appareil MicroPython → `main.py`. Fermer Thonny.
4. Lancer `LANCER.bat` : le pont détecte l'ESP32 et l'utilise à la place du PC.
