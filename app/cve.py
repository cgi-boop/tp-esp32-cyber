"""Recherche de CVE via l'API officielle NVD (NIST) + proposition de solutions."""
import json
import os

import requests

OFFLINE_FILE = os.path.join(os.path.dirname(__file__), "data", "cves_offline.json")

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_API_KEY = os.getenv("NVD_API_KEY", "")

# Solutions types selon la faiblesse (CWE) associée à la CVE
CWE_SOLUTIONS = {
    "CWE-79": "XSS : échapper/encoder toutes les sorties HTML, valider les entrées, activer une Content-Security-Policy.",
    "CWE-89": "Injection SQL : utiliser des requêtes paramétrées, jamais de concaténation de chaînes, compte BDD à privilèges minimaux.",
    "CWE-78": "Injection de commandes OS : ne pas passer d'entrée utilisateur au shell, utiliser des listes d'arguments et une liste blanche.",
    "CWE-77": "Injection de commandes : filtrer les entrées et éviter les appels au shell.",
    "CWE-22": "Path traversal : normaliser les chemins, refuser '..', limiter l'accès à un dossier racine.",
    "CWE-787": "Écriture hors limites : appliquer le correctif éditeur, activer ASLR/DEP, utiliser des fonctions mémoire sûres.",
    "CWE-125": "Lecture hors limites : appliquer le correctif, vérifier les tailles de buffer.",
    "CWE-416": "Use-after-free : mettre à jour le logiciel, activer les protections mémoire du compilateur.",
    "CWE-120": "Débordement de tampon : contrôle des tailles, fonctions sécurisées (strncpy, snprintf), mise à jour.",
    "CWE-20": "Validation d'entrée insuffisante : valider type, longueur et format de toutes les entrées.",
    "CWE-287": "Authentification défaillante : MFA, politique de mots de passe forts, mettre à jour.",
    "CWE-306": "Fonction critique sans authentification : exiger une authentification, restreindre l'accès réseau.",
    "CWE-798": "Identifiants codés en dur : supprimer les secrets du code, changer les mots de passe par défaut.",
    "CWE-352": "CSRF : jetons anti-CSRF, cookies SameSite, vérifier l'origine des requêtes.",
    "CWE-434": "Upload dangereux : liste blanche d'extensions, scan antivirus, stockage hors racine web.",
    "CWE-502": "Désérialisation non sûre : ne pas désérialiser de données non fiables, utiliser JSON.",
    "CWE-918": "SSRF : liste blanche des URL autorisées, bloquer les IP internes.",
    "CWE-400": "Consommation de ressources : limites de débit, timeouts, quotas.",
    "CWE-200": "Fuite d'informations : restreindre les messages d'erreur et les accès aux données sensibles.",
    "CWE-269": "Mauvaise gestion des privilèges : principe du moindre privilège, mettre à jour.",
    "CWE-119": "Erreur mémoire : appliquer les correctifs, activer les protections du système.",
}
DEFAULT_SOLUTION = ("Appliquer le dernier correctif de l'éditeur, limiter l'exposition réseau du service "
                    "et surveiller les journaux. Voir les références ci-dessous.")


def _parse(item):
    cve = item["cve"]
    desc = next((d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"), "")

    score, severity = None, "N/A"
    metrics = cve.get("metrics", {})
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if metrics.get(key):
            m = metrics[key][0]
            score = m["cvssData"].get("baseScore")
            severity = m["cvssData"].get("baseSeverity") or m.get("baseSeverity", "N/A")
            break

    cwe = None
    for w in cve.get("weaknesses", []):
        for d in w.get("description", []):
            if d["value"].startswith("CWE-"):
                cwe = d["value"]
                break
        if cwe:
            break

    refs = [r["url"] for r in cve.get("references", [])][:5]
    patch_refs = [r["url"] for r in cve.get("references", []) if "Patch" in r.get("tags", [])]

    solution = CWE_SOLUTIONS.get(cwe, DEFAULT_SOLUTION)
    if patch_refs:
        solution += f" Correctif officiel disponible : {patch_refs[0]}"

    return {
        "id": cve["id"],
        "description": desc,
        "score": score,
        "severity": severity,
        "published": cve.get("published", "")[:10],
        "cwe": cwe,
        "solution": solution,
        "references": refs,
    }


def search_offline(keyword: str):
    """Recherche dans la base locale (fonctionne sans Internet).
    Mot-clé '*' = toutes les CVE locales."""
    with open(OFFLINE_FILE, encoding="utf-8") as f:
        data = json.load(f)
    q = keyword.lower().strip()
    results = []
    for c in data:
        text = f"{c['id']} {c['keywords']} {c['description']}".lower()
        if q == "*" or all(word in text for word in q.split()):
            item = {k: v for k, v in c.items() if k != "keywords"}
            item["source"] = "Base locale (hors ligne)"
            results.append(item)
    return results


def search_online(keyword: str, limit: int = 20):
    params = {"keywordSearch": keyword, "resultsPerPage": limit}
    headers = {"apiKey": NVD_API_KEY} if NVD_API_KEY else {}
    r = requests.get(NVD_URL, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    items = r.json().get("vulnerabilities", [])
    results = [_parse(i) for i in items]
    for c in results:
        c["source"] = "NVD en ligne"
    return results


def search_cves(keyword: str, limit: int = 20):
    """Essaie l'API NVD en ligne ; sans Internet, bascule sur la base locale."""
    if keyword.strip() == "*":
        return search_offline(keyword)
    try:
        return search_online(keyword, limit)
    except requests.RequestException:
        return search_offline(keyword)
