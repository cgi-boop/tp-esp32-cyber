"""Analyse d'un fichier : virus ou non ?

Deux moteurs :
1. ClamAV (antivirus open source, conteneur `clamav`) via le protocole clamd INSTREAM.
2. Analyse heuristique maison (hash connus, signature EICAR, extensions,
   exécutable déguisé, entropie, chaînes suspectes).
Si ClamAV n'est pas disponible, l'heuristique seule donne le verdict.
"""
import hashlib
import math
import os
import socket
import struct
from collections import Counter

CLAMD_HOST = os.getenv("CLAMD_HOST", "localhost")
CLAMD_PORT = int(os.getenv("CLAMD_PORT", "3310"))

# Hash SHA-256 de malwares connus (ici : fichier de test EICAR officiel)
KNOWN_BAD_HASHES = {
    "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f": "EICAR-Test-File",
}

EICAR_SIGNATURE = b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE"

DANGEROUS_EXT = {".exe", ".scr", ".bat", ".cmd", ".com", ".pif", ".vbs", ".js",
                 ".jse", ".wsf", ".ps1", ".hta", ".msi", ".dll", ".jar", ".lnk"}
DOC_EXT = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".txt", ".mp3", ".mp4"}

SUSPICIOUS_STRINGS = {
    b"powershell -enc": "PowerShell encodé",
    b"powershell.exe -nop": "PowerShell sans profil",
    b"cmd.exe /c": "Exécution de commandes",
    b"WScript.Shell": "Accès au shell Windows",
    b"CreateRemoteThread": "Injection de processus",
    b"VirtualAllocEx": "Allocation mémoire distante",
    b"URLDownloadToFile": "Téléchargement de charge",
    b"AutoOpen": "Macro auto-exécutable",
    b"Document_Open": "Macro auto-exécutable",
    b"eval(base64_decode": "Code PHP obfusqué",
    b"vssadmin delete shadows": "Suppression des sauvegardes (ransomware)",
    b"/bin/sh -i": "Reverse shell",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entropy(data: bytes) -> float:
    """Entropie de Shannon (0 à 8). > 7.5 = probablement chiffré/compressé/packé."""
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


def clamav_scan(data: bytes):
    """Envoie le fichier à clamd. Retourne (disponible, infecté, nom_signature)."""
    try:
        with socket.create_connection((CLAMD_HOST, CLAMD_PORT), timeout=30) as s:
            s.sendall(b"zINSTREAM\0")
            for i in range(0, len(data), 8192):
                chunk = data[i:i + 8192]
                s.sendall(struct.pack("!L", len(chunk)) + chunk)
            s.sendall(struct.pack("!L", 0))
            resp = b""
            while not resp.endswith(b"\0"):
                part = s.recv(4096)
                if not part:
                    break
                resp += part
        text = resp.rstrip(b"\0").decode(errors="ignore")  # ex: "stream: OK"
        if text.endswith("FOUND"):
            return True, True, text.split(":", 1)[1].replace("FOUND", "").strip()
        if text.endswith("OK"):
            return True, False, None
        return False, False, text
    except OSError:
        return False, False, None


def heuristic_scan(filename: str, data: bytes):
    findings, score = [], 0
    h = sha256(data)
    name = filename.lower()
    ext = os.path.splitext(name)[1]

    if h in KNOWN_BAD_HASHES:
        findings.append(f"Hash connu : {KNOWN_BAD_HASHES[h]}")
        score += 100
    if EICAR_SIGNATURE in data:
        findings.append("Signature EICAR détectée")
        score += 100

    parts = name.split(".")
    if len(parts) >= 3 and "." + parts[-2] in DOC_EXT and "." + parts[-1] in DANGEROUS_EXT:
        findings.append(f"Double extension trompeuse ({parts[-2]}.{parts[-1]})")
        score += 40
    elif ext in DANGEROUS_EXT:
        findings.append(f"Extension potentiellement dangereuse ({ext})")
        score += 15

    if data[:2] == b"MZ" and ext not in {".exe", ".dll", ".scr", ".com", ".msi"}:
        findings.append("Exécutable Windows déguisé (en-tête MZ)")
        score += 40
    if data[:4] == b"\x7fELF" and ext not in {"", ".elf", ".so", ".bin"}:
        findings.append("Exécutable Linux déguisé (en-tête ELF)")
        score += 30

    ent = entropy(data)
    if ent > 7.5 and ext not in {".zip", ".gz", ".7z", ".rar", ".jpg", ".jpeg", ".png", ".mp3", ".mp4", ".pdf", ".docx", ".xlsx"}:
        findings.append(f"Entropie très élevée ({ent:.2f}/8) : contenu chiffré ou packé")
        score += 20

    low = data.lower()
    for pattern, label in SUSPICIOUS_STRINGS.items():
        if pattern.lower() in low:
            findings.append(f"Chaîne suspecte : {label}")
            score += 25

    return min(score, 100), findings, round(ent, 2)


def scan_file(filename: str, data: bytes) -> dict:
    score, findings, ent = heuristic_scan(filename, data)
    clam_ok, infected, signature = clamav_scan(data)

    if clam_ok and infected:
        verdict, score = "MALVEILLANT", 100
        findings.insert(0, f"ClamAV : {signature}")
    elif score >= 70:
        verdict = "MALVEILLANT"
    elif score >= 30:
        verdict = "SUSPECT"
    else:
        verdict = "SAIN"

    return {
        "filename": filename,
        "sha256": sha256(data),
        "size": len(data),
        "verdict": verdict,
        "engine": "clamav + heuristique" if clam_ok else "heuristique (ClamAV indisponible)",
        "details": {"score": score, "entropy": ent, "findings": findings},
    }
