#!/usr/bin/env python3
"""
scripts/db.py — the only place that talks SQL for the job-search pipeline.

All state access (dedup, enrichment, rejection, scheduling) goes through the
CLI defined here. See docs/design.md sections 2-3 for the schema and spec.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "jobsearch.db"
DEFAULT_SOURCES_PATH = REPO_ROOT / "config" / "sources.yaml"

PERMANENT = "9999-12-31"

# ---------------------------------------------------------------------------
# Domain normalization — the canonical key. One function, used everywhere.
# ---------------------------------------------------------------------------

# Registrable-domain suffixes that are themselves two labels long (public
# suffix list is much bigger than this; this covers the common cases the
# pipeline is likely to hit). Anything not in this set is assumed to have a
# single-label public suffix (.com, .ai, .io, .co, ...).
TWO_LABEL_SUFFIXES = {
    "co.uk", "co.in", "co.jp", "co.nz", "co.za", "co.id", "co.kr",
    "com.au", "com.br", "com.sg", "com.mx", "com.cn", "com.hk",
    "org.uk", "net.in", "ac.in", "gov.in",
}


def normalize_domain(raw: str) -> str:
    """
    lowercase -> strip scheme -> strip userinfo/port -> strip path/query/fragment
    -> strip trailing dot -> strip leading www. -> collapse to registrable domain.

    'https://WWW.Sarvam.ai/careers' -> 'sarvam.ai'
    'careers.sarvam.ai'             -> 'sarvam.ai'
    'example.co.uk/jobs'            -> 'example.co.uk'
    """
    if raw is None:
        return ""
    s = raw.strip().lower()
    if not s:
        return ""

    if "//" in s:
        s = s.split("//", 1)[1]

    s = s.split("/", 1)[0]
    s = s.split("?", 1)[0]
    s = s.split("#", 1)[0]

    if "@" in s:
        s = s.rsplit("@", 1)[1]

    s = s.split(":", 1)[0]  # strip port

    s = s.rstrip(".")

    if s.startswith("www."):
        s = s[4:]

    labels = [l for l in s.split(".") if l]
    if len(labels) <= 2:
        return ".".join(labels)

    last_two = ".".join(labels[-2:])
    if last_two in TWO_LABEL_SUFFIXES and len(labels) >= 3:
        return ".".join(labels[-3:])
    return last_two


# ---------------------------------------------------------------------------
# Connection / schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    domain          TEXT PRIMARY KEY,
    name            TEXT,
    status          TEXT DEFAULT 'candidate',
    reject_reason   TEXT,
    recheck_after   TEXT,
    discovered_via  TEXT,
    first_seen      TEXT DEFAULT CURRENT_TIMESTAMP,
    last_verified   TEXT,

    score           REAL,
    tier            TEXT,
    score_rationale TEXT,

    sector          TEXT,
    sub_sector      TEXT,
    founding_year   TEXT,
    funding_stage   TEXT,
    total_funding   TEXT,
    last_round      TEXT,
    investors       TEXT,
    founders        TEXT,
    founder_edu     TEXT,
    founder_bg      TEXT,
    headcount       TEXT,
    hq_location     TEXT,
    remote_policy   TEXT,
    remote_evidence TEXT,
    product_desc    TEXT,
    is_hiring       TEXT,
    open_roles      TEXT,
    min_experience  TEXT,
    careers_url     TEXT,
    job_links       TEXT,
    founder_li      TEXT,
    eng_lead_li     TEXT,
    recent_news     TEXT,
    outreach_flag   INTEGER DEFAULT 0,
    outreach_angle  TEXT,
    source_urls     TEXT,

    applied_at      TEXT,
    contact         TEXT,
    followup_due    TEXT,
    outcome         TEXT,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS search_log (
    source      TEXT PRIMARY KEY,
    label       TEXT,
    last_run_at TEXT,
    runs        INTEGER DEFAULT 0,
    found_new   INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_status ON companies(status);
CREATE INDEX IF NOT EXISTS idx_tier ON companies(tier);
CREATE INDEX IF NOT EXISTS idx_recheck ON companies(recheck_after);
"""

# Columns on `companies` that record()/mark() are allowed to write via the
# generic field-update path (excludes domain/status/first_seen which are
# managed explicitly).
RECORD_FIELDS = {
    "name", "score", "tier", "score_rationale",
    "sector", "sub_sector", "founding_year", "funding_stage", "total_funding",
    "last_round", "investors", "founders", "founder_edu", "founder_bg",
    "headcount", "hq_location", "remote_policy", "remote_evidence",
    "product_desc", "is_hiring", "open_roles", "min_experience",
    "careers_url", "job_links", "founder_li", "eng_lead_li", "recent_news",
    "outreach_flag", "outreach_angle", "source_urls",
}

EXPORT_COLUMNS = [
    "domain", "name", "tier", "score", "score_rationale",
    "sector", "sub_sector", "funding_stage", "total_funding", "last_round",
    "headcount", "hq_location", "remote_policy", "remote_evidence",
    "product_desc", "is_hiring", "open_roles", "min_experience",
    "careers_url", "job_links", "founder_li", "eng_lead_li", "recent_news",
    "outreach_flag", "outreach_angle", "source_urls",
    "discovered_via", "last_verified",
]


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def today() -> str:
    return date.today().isoformat()


def parse_ttl(spec: Optional[str], default_permanent: bool = True) -> str:
    """'45d' -> today+45 days (ISO). 'permanent' or None -> PERMANENT."""
    if spec is None:
        return PERMANENT if default_permanent else None
    s = spec.strip().lower()
    if s == "permanent":
        return PERMANENT
    m = re.match(r"^(\d+)d$", s)
    if not m:
        raise ValueError(f"invalid TTL {spec!r}; expected '<N>d' or 'permanent'")
    days = int(m.group(1))
    return (date.today() + timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# Library functions — one per CLI command, testable without argparse/subprocess.
# ---------------------------------------------------------------------------

def init_db(conn: sqlite3.Connection, sources_path: Optional[Path] = None) -> dict:
    conn.executescript(SCHEMA)
    conn.commit()

    sources_path = sources_path or DEFAULT_SOURCES_PATH
    seeded = 0
    if sources_path.exists():
        import yaml  # local import: only needed for init
        with open(sources_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for src in data.get("sources", []):
            cur = conn.execute(
                "INSERT OR IGNORE INTO search_log (source, label) VALUES (?, ?)",
                (src["id"], src.get("label", "")),
            )
            if cur.rowcount:
                seeded += 1
        conn.commit()

    return {"schema": "created", "sources_seeded": seeded, "sources_file_found": sources_path.exists()}


def get_stale_sources(conn: sqlite3.Connection, n: int = 1, touch: bool = True) -> list[dict]:
    rows = conn.execute(
        """
        SELECT * FROM search_log
        ORDER BY (last_run_at IS NOT NULL), last_run_at ASC, source ASC
        LIMIT ?
        """,
        (n,),
    ).fetchall()
    result = [dict(r) for r in rows]
    if touch:
        for r in result:
            conn.execute(
                "UPDATE search_log SET last_run_at = ?, runs = runs + 1 WHERE source = ?",
                (today(), r["source"]),
            )
        conn.commit()
    return result


def filter_new(conn: sqlite3.Connection, domains: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in domains:
        d = normalize_domain(raw)
        if not d or d in seen:
            continue
        seen.add(d)
        ordered.append(d)
    if not ordered:
        return []
    placeholders = ",".join("?" * len(ordered))
    existing = {
        row["domain"]
        for row in conn.execute(
            f"SELECT domain FROM companies WHERE domain IN ({placeholders})", ordered
        )
    }
    return [d for d in ordered if d not in existing]


def enqueue(conn: sqlite3.Connection, domain: str, name: Optional[str] = None,
            via: Optional[str] = None) -> bool:
    d = normalize_domain(domain)
    if not d:
        raise ValueError(f"cannot normalize domain from {domain!r}")
    cur = conn.execute(
        "INSERT OR IGNORE INTO companies (domain, name, status, discovered_via) "
        "VALUES (?, ?, 'candidate', ?)",
        (d, name, via),
    )
    inserted = cur.rowcount > 0
    if inserted and via:
        conn.execute(
            "UPDATE search_log SET found_new = found_new + 1 WHERE source = ?", (via,)
        )
    conn.commit()
    return inserted


def next_batch(conn: sqlite3.Connection, limit: int = 15) -> list[dict]:
    rows = conn.execute(
        """
        SELECT * FROM companies
        WHERE status = 'candidate'
           OR (status = 'rejected' AND recheck_after IS NOT NULL AND recheck_after <= ?)
        ORDER BY first_seen ASC
        LIMIT ?
        """,
        (today(), limit),
    ).fetchall()
    return [dict(r) for r in rows]


class UnknownDomainError(LookupError):
    pass


def _require_exists(conn: sqlite3.Connection, domain: str) -> str:
    d = normalize_domain(domain)
    row = conn.execute("SELECT domain FROM companies WHERE domain = ?", (d,)).fetchone()
    if row is None:
        raise UnknownDomainError(f"unknown domain: {d}")
    return d


def record(conn: sqlite3.Connection, domain: str, data: dict) -> None:
    d = _require_exists(conn, domain)
    fields = {k: v for k, v in data.items() if k in RECORD_FIELDS}
    fields["status"] = "enriched"
    fields["last_verified"] = today()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [d]
    conn.execute(f"UPDATE companies SET {set_clause} WHERE domain = ?", values)
    conn.commit()


def reject(conn: sqlite3.Connection, domain: str, reason: str,
           recheck_in: Optional[str] = None) -> None:
    d = _require_exists(conn, domain)
    recheck_after = parse_ttl(recheck_in, default_permanent=True)
    conn.execute(
        "UPDATE companies SET status = 'rejected', reject_reason = ?, "
        "recheck_after = ?, last_verified = ? WHERE domain = ?",
        (reason, recheck_after, today(), d),
    )
    conn.commit()


def mark(conn: sqlite3.Connection, domain: str, status: Optional[str] = None,
         contact: Optional[str] = None, followup_in: Optional[str] = None) -> None:
    d = _require_exists(conn, domain)
    updates: dict[str, Any] = {}
    if status:
        updates["status"] = status
        if status == "applied":
            updates["applied_at"] = today()
    if contact:
        updates["contact"] = contact
    if followup_in:
        updates["followup_due"] = parse_ttl(followup_in, default_permanent=False)
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [d]
    conn.execute(f"UPDATE companies SET {set_clause} WHERE domain = ?", values)
    conn.commit()


def followups_due(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT * FROM companies
        WHERE followup_due IS NOT NULL AND followup_due <= ? AND outcome IS NULL
        ORDER BY followup_due ASC
        """,
        (today(),),
    ).fetchall()
    return [dict(r) for r in rows]


def export_csv(conn: sqlite3.Connection, tiers: list[str], out_path: Path) -> int:
    placeholders = ",".join("?" * len(tiers))
    rows = conn.execute(
        f"SELECT * FROM companies WHERE tier IN ({placeholders}) ORDER BY score DESC",
        tiers,
    ).fetchall()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in EXPORT_COLUMNS})
    return len(rows)


def get_stats(conn: sqlite3.Connection) -> dict:
    by_status = {
        r["status"]: r["n"]
        for r in conn.execute("SELECT status, COUNT(*) AS n FROM companies GROUP BY status")
    }
    by_tier = {
        r["tier"]: r["n"]
        for r in conn.execute(
            "SELECT tier, COUNT(*) AS n FROM companies WHERE tier IS NOT NULL GROUP BY tier"
        )
    }
    sources = [dict(r) for r in conn.execute("SELECT * FROM search_log ORDER BY source ASC")]
    return {"by_status": by_status, "by_tier": by_tier, "sources": sources}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _read_domains_arg(domains: list[str]) -> list[str]:
    if domains:
        return domains
    return [line.strip() for line in sys.stdin if line.strip()]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="db.py", description="Job search pipeline state store")
    p.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="path to sqlite db")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("init")
    sp.add_argument("--sources", type=Path, default=DEFAULT_SOURCES_PATH)

    sp = sub.add_parser("stale-source")
    sp.add_argument("--n", type=int, default=1)
    sp.add_argument("--no-touch", action="store_true",
                     help="don't update last_run_at/runs (for inspection only)")

    sp = sub.add_parser("filter-new")
    sp.add_argument("domains", nargs="*")

    sp = sub.add_parser("enqueue")
    sp.add_argument("domain")
    sp.add_argument("--name")
    sp.add_argument("--via")

    sp = sub.add_parser("next-batch")
    sp.add_argument("--limit", type=int, default=15)

    sp = sub.add_parser("record")
    sp.add_argument("domain")
    sp.add_argument("--json", required=True, dest="json_file", type=Path)

    sp = sub.add_parser("reject")
    sp.add_argument("domain")
    sp.add_argument("--reason", required=True)
    sp.add_argument("--recheck-in")

    sp = sub.add_parser("mark")
    sp.add_argument("domain")
    sp.add_argument("--status")
    sp.add_argument("--contact")
    sp.add_argument("--followup-in")

    sub.add_parser("followups-due")

    sp = sub.add_parser("export")
    sp.add_argument("--tier", required=True, help="comma-separated, e.g. A,B")
    sp.add_argument("--out", required=True, type=Path)

    sub.add_parser("stats")

    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    conn = get_connection(args.db)
    try:
        if args.command == "init":
            print(json.dumps(init_db(conn, args.sources)))

        elif args.command == "stale-source":
            print(json.dumps(get_stale_sources(conn, args.n, touch=not args.no_touch)))

        elif args.command == "filter-new":
            domains = _read_domains_arg(args.domains)
            for d in filter_new(conn, domains):
                print(d)

        elif args.command == "enqueue":
            inserted = enqueue(conn, args.domain, name=args.name, via=args.via)
            print(json.dumps({"domain": normalize_domain(args.domain), "inserted": inserted}))

        elif args.command == "next-batch":
            print(json.dumps(next_batch(conn, args.limit)))

        elif args.command == "record":
            with open(args.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            record(conn, args.domain, data)
            print(json.dumps({"domain": normalize_domain(args.domain), "status": "enriched"}))

        elif args.command == "reject":
            reject(conn, args.domain, args.reason, args.recheck_in)
            print(json.dumps({"domain": normalize_domain(args.domain), "status": "rejected"}))

        elif args.command == "mark":
            mark(conn, args.domain, status=args.status, contact=args.contact,
                 followup_in=args.followup_in)
            print(json.dumps({"domain": normalize_domain(args.domain), "status": "marked"}))

        elif args.command == "followups-due":
            print(json.dumps(followups_due(conn)))

        elif args.command == "export":
            tiers = [t.strip() for t in args.tier.split(",") if t.strip()]
            n = export_csv(conn, tiers, args.out)
            print(f"Wrote {n} rows to {args.out}")

        elif args.command == "stats":
            print(json.dumps(get_stats(conn)))

        return 0

    except UnknownDomainError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
