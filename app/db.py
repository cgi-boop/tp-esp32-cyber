"""Accès à la base PostgreSQL : création des tables + fonctions d'enregistrement."""
import json
import os
import time

import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cyber:cyber@localhost:5432/cyberdb")

SCHEMA = """
CREATE TABLE IF NOT EXISTS file_scans (
    id          SERIAL PRIMARY KEY,
    filename    TEXT NOT NULL,
    sha256      TEXT NOT NULL,
    size_bytes  INTEGER NOT NULL,
    verdict     TEXT NOT NULL,          -- SAIN / SUSPECT / MALVEILLANT
    engine      TEXT NOT NULL,          -- clamav / heuristique
    details     JSONB NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS network_scans (
    id          SERIAL PRIMARY KEY,
    scan_type   TEXT NOT NULL,          -- wifi / bluetooth
    device_count INTEGER NOT NULL,
    results     JSONB NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cves (
    id          SERIAL PRIMARY KEY,
    cve_id      TEXT UNIQUE NOT NULL,
    keyword     TEXT,
    description TEXT,
    score       REAL,
    severity    TEXT,
    published   TEXT,
    cwe         TEXT,
    solution    TEXT,
    refs        JSONB,
    saved_at    TIMESTAMP DEFAULT NOW()
);
"""


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def init_db(retries=20):
    """Crée les tables. Réessaie le temps que PostgreSQL démarre."""
    for i in range(retries):
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(SCHEMA)
            print("[DB] Tables prêtes")
            return
        except psycopg2.OperationalError as e:
            print(f"[DB] Attente de PostgreSQL ({i + 1}/{retries}) : {e}")
            time.sleep(2)
    raise RuntimeError("Impossible de se connecter à PostgreSQL")


def save_file_scan(r):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO file_scans (filename, sha256, size_bytes, verdict, engine, details)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, created_at""",
            (r["filename"], r["sha256"], r["size"], r["verdict"], r["engine"], json.dumps(r["details"])),
        )
        return cur.fetchone()


def save_network_scan(scan_type, devices):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO network_scans (scan_type, device_count, results)
               VALUES (%s, %s, %s) RETURNING id, created_at""",
            (scan_type, len(devices), json.dumps(devices)),
        )
        return cur.fetchone()


def save_cves(cves, keyword):
    with get_conn() as conn, conn.cursor() as cur:
        for c in cves:
            cur.execute(
                """INSERT INTO cves (cve_id, keyword, description, score, severity, published, cwe, solution, refs)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (cve_id) DO UPDATE SET
                       description = EXCLUDED.description, score = EXCLUDED.score,
                       severity = EXCLUDED.severity, solution = EXCLUDED.solution,
                       refs = EXCLUDED.refs, saved_at = NOW()""",
                (c["id"], keyword, c["description"], c["score"], c["severity"],
                 c["published"], c["cwe"], c["solution"], json.dumps(c["references"])),
            )


def list_file_scans(limit=50):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM file_scans ORDER BY created_at DESC LIMIT %s", (limit,))
        return cur.fetchall()


def list_network_scans(limit=50):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM network_scans ORDER BY created_at DESC LIMIT %s", (limit,))
        return cur.fetchall()


def list_cves(limit=100):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM cves ORDER BY saved_at DESC LIMIT %s", (limit,))
        return cur.fetchall()
