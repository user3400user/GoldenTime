"""
Kundenportal — Auth- & Mandanten-Logik (Loop 3, stdlib-only, sicherheits-first).

REINE Funktionen (ohne HTTP-Server testbar) auf der ``pipeline_state.db`` (Tabellen ``customer`` /
``portal_session`` / ``portal_lead``, Schema in control/state.py). Der HTTP-Handler (portal/app.py)
ist nur die dünne Hülle. Sicherheits-Entscheide:

- **Passwörter** als ``hashlib.scrypt`` + per-User-Salt — NIE Klartext. Vergleich timing-safe
  (``hmac.compare_digest``). Generischer Login-Fehler (kein User-Enumeration).
- **Sessions** als ``secrets.token_urlsafe`` — in der DB liegt nur ``sha256(token)`` (ein DB-Leck
  enthüllt keine Live-Tokens). Ablauf (``laeuft_ab``) wird erzwungen; abgelaufene Sessions gelten als ungültig.
- **Mandanten-Trennung:** ein Kunde ist genau einem ``gebiet`` zugeordnet und sieht NUR dessen Leads
  (``leads_for_customer`` filtert hart auf ``customer.gebiet``; ``lead_belongs_to`` prüft Einzel-Zugriff).
- **CSRF:** je Session ein Token für state-ändernde POSTs (Logout).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import secrets
import sqlite3

# scrypt-Parameter (interaktiv, RFC-7914-üblich) — CPU/Memory-hart genug für ein Low-N-B2B-Portal.
_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1
_DKLEN = 32
_SALT_BYTES = 16
SESSION_TTL_STUNDEN = 12


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    """(hash_hex, salt_hex) — scrypt über das Passwort + (neuen oder gegebenen) Salt."""
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_DKLEN)
    return dk.hex(), salt.hex()


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    """Timing-sicherer Passwort-Vergleich (re-hash mit gespeichertem Salt)."""
    kandidat, _ = hash_password(password, salt_hex)
    return hmac.compare_digest(kandidat, hash_hex)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_customer(con: sqlite3.Connection, *, login: str, password: str, name: str,
                    gebiet: str, funktion: str = "speicher_installateur") -> int:
    """Lege einen Portal-Kunden an (Passwort wird gehasht). Gibt die customer.id zurück.

    ``login`` ist UNIQUE → ein doppelter Login wirft sqlite3.IntegrityError (Aufrufer behandelt).
    """
    if not login or not password:
        raise ValueError("login und password sind Pflicht.")
    h, salt = hash_password(password)
    cur = con.execute(
        "INSERT INTO customer(login, name, pass_hash, pass_salt, gebiet, funktion, aktiv, erstellt_am) "
        "VALUES(?, ?, ?, ?, ?, ?, 1, ?)",
        (login.strip().lower(), name, h, salt, gebiet, funktion, _now().isoformat(timespec="seconds")),
    )
    con.commit()
    return int(cur.lastrowid)


def authenticate(con: sqlite3.Connection, login: str, password: str) -> sqlite3.Row | None:
    """Prüfe Login+Passwort. Gibt die customer-Zeile zurück oder ``None`` (generisch — kein Enumeration).

    Führt den scrypt-Vergleich AUCH bei unbekanntem Login durch (gegen einen Dummy-Hash), damit die
    Antwortzeit nicht verrät, ob der Login existiert (Timing-Härtung).
    """
    row = con.execute(
        "SELECT * FROM customer WHERE login = ? AND aktiv = 1", (login.strip().lower(),)
    ).fetchone()
    if row is None:
        # Dummy-Verifikation gegen Timing-/User-Enumeration (konstante Arbeit, immer False).
        verify_password(password, "00" * _DKLEN, "00" * _SALT_BYTES)
        return None
    if verify_password(password, row["pass_hash"], row["pass_salt"]):
        return row
    return None


def create_session(con: sqlite3.Connection, customer_id: int,
                   *, ttl_stunden: int = SESSION_TTL_STUNDEN) -> tuple[str, str]:
    """Lege eine Session an. Gibt (roh_token, csrf) zurück — der Roh-Token gehört NUR ins Cookie,
    in der DB liegt sein sha256-Hash. ``laeuft_ab`` = jetzt + TTL."""
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(16)
    jetzt = _now()
    con.execute(
        "INSERT INTO portal_session(token_hash, customer_id, csrf, erstellt_am, laeuft_ab) "
        "VALUES(?, ?, ?, ?, ?)",
        (_token_hash(token), customer_id, csrf, jetzt.isoformat(timespec="seconds"),
         (jetzt + dt.timedelta(hours=ttl_stunden)).isoformat(timespec="seconds")),
    )
    con.commit()
    return token, csrf


def session_customer(con: sqlite3.Connection, token: str | None) -> sqlite3.Row | None:
    """Roh-Token (aus dem Cookie) → die zugehörige customer-Zeile, oder ``None``.

    Gültig nur, wenn die Session existiert, NICHT abgelaufen ist und der Kunde aktiv ist. Liefert
    zusätzlich das Session-CSRF-Token als Attribut-frei via ``session_csrf`` separat abrufbar.
    """
    if not token:
        return None
    row = con.execute(
        "SELECT s.laeuft_ab, c.* FROM portal_session s JOIN customer c ON c.id = s.customer_id "
        "WHERE s.token_hash = ? AND c.aktiv = 1",
        (_token_hash(token),),
    ).fetchone()
    if row is None:
        return None
    if _ablauf_ueberschritten(row["laeuft_ab"]):
        return None
    return row


def session_csrf(con: sqlite3.Connection, token: str | None) -> str | None:
    """CSRF-Token der Session (für state-ändernde Formulare). ``None`` wenn ungültig/abgelaufen."""
    if not token:
        return None
    row = con.execute(
        "SELECT csrf, laeuft_ab FROM portal_session WHERE token_hash = ?", (_token_hash(token),)
    ).fetchone()
    if row is None or _ablauf_ueberschritten(row["laeuft_ab"]):
        return None
    return row["csrf"]


def _ablauf_ueberschritten(laeuft_ab: str) -> bool:
    try:
        return _now() >= dt.datetime.fromisoformat(laeuft_ab)
    except (ValueError, TypeError):
        return True   # unparsbar → als abgelaufen behandeln (fail-safe)


def destroy_session(con: sqlite3.Connection, token: str | None) -> None:
    """Logout: Session löschen (idempotent)."""
    if not token:
        return
    con.execute("DELETE FROM portal_session WHERE token_hash = ?", (_token_hash(token),))
    con.commit()


def invalidate_customer_sessions(con: sqlite3.Connection, customer_id: int) -> int:
    """ALLE Sessions eines Kunden löschen (bei Login/Passwortwechsel) — Single-Active-Session-Modell.

    Schließt das Session-Akkumulations-/Fixation-Restrisiko (Security-Review H1): ein Re-Login macht
    alte Tokens sofort ungültig; ein einmal abgegriffenes Token überlebt den nächsten Login nicht.
    """
    cur = con.execute("DELETE FROM portal_session WHERE customer_id = ?", (customer_id,))
    con.commit()
    return cur.rowcount


def purge_expired(con: sqlite3.Connection) -> int:
    """Abgelaufene Sessions aufräumen. Gibt die Zahl gelöschter Zeilen zurück."""
    cur = con.execute("DELETE FROM portal_session WHERE laeuft_ab <= ?",
                      (_now().isoformat(timespec="seconds"),))
    con.commit()
    return cur.rowcount


def leads_for_customer(con: sqlite3.Connection, customer: sqlite3.Row,
                       *, nur_demo: bool = True) -> list[sqlite3.Row]:
    """Die Leads, die dieser Kunde sehen darf — HART auf sein ``gebiet`` gefiltert (Mandanten-Trennung).

    Kein Parameter erlaubt es dem Kunden, ein anderes Gebiet zu wählen: das Gebiet kommt allein aus
    seiner customer-Zeile, nie aus der Anfrage. ``nur_demo`` (Default **True**, fail-safe) verriegelt §0
    serverseitig: solange die Live-Lieferung aus ist, werden NUR ``demo=1``-Leads gezeigt — kein echter
    Personendaten-Pfad an einen zahlenden Kunden, auch wenn versehentlich Echtdaten in der Tabelle lägen.
    """
    sql = "SELECT * FROM portal_lead WHERE gebiet = ?"
    params: list = [customer["gebiet"]]
    if nur_demo:
        sql += " AND demo = 1"
    sql += " ORDER BY (kwp IS NULL), kwp DESC, see"
    return list(con.execute(sql, params))


def lead_belongs_to(con: sqlite3.Connection, customer: sqlite3.Row, see: str,
                    *, nur_demo: bool = True) -> sqlite3.Row | None:
    """Einzel-Lead NUR, wenn er zum Gebiet des Kunden gehört (Mandanten-Trennung) — und (``nur_demo``)
    nur Demo-Leads, solange die Live-Lieferung aus ist (§0-Verriegelung im Lese-Pfad)."""
    sql = "SELECT * FROM portal_lead WHERE see = ? AND gebiet = ?"
    params: list = [see, customer["gebiet"]]
    if nur_demo:
        sql += " AND demo = 1"
    return con.execute(sql, params).fetchone()
