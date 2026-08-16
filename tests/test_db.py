import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import db  # noqa: E402


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "test.db"
    c = db.get_connection(db_path)
    db.init_db(c, sources_path=tmp_path / "nonexistent-sources.yaml")
    yield c
    c.close()


@pytest.fixture
def db_path(tmp_path):
    p = tmp_path / "test.db"
    c = db.get_connection(p)
    db.init_db(c, sources_path=tmp_path / "nonexistent-sources.yaml")
    c.close()
    return p


# ---------------------------------------------------------------------------
# Domain normalization
# ---------------------------------------------------------------------------

def test_normalize_domain_strips_scheme_www_and_path():
    assert db.normalize_domain("https://WWW.Sarvam.ai/careers") == "sarvam.ai"


def test_normalize_domain_bare_domain_unchanged():
    assert db.normalize_domain("sarvam.ai") == "sarvam.ai"


def test_normalize_domain_subdomain_collapses():
    assert db.normalize_domain("careers.sarvam.ai") == "sarvam.ai"


def test_normalize_domain_two_label_suffix():
    assert db.normalize_domain("https://www.example.co.uk/jobs") == "example.co.uk"


# ---------------------------------------------------------------------------
# Required Phase 1 behaviors
# ---------------------------------------------------------------------------

def test_inserting_same_domain_twice_is_a_noop(conn):
    first = db.enqueue(conn, "https://sarvam.ai", name="Sarvam", via="yc:W26")
    second = db.enqueue(conn, "https://sarvam.ai", name="Sarvam AI", via="yc:W26")

    assert first is True
    assert second is False

    rows = conn.execute("SELECT * FROM companies WHERE domain = 'sarvam.ai'").fetchall()
    assert len(rows) == 1
    assert rows[0]["name"] == "Sarvam"  # first write wins, second was ignored


def test_www_and_bare_variants_collapse_to_one_row(conn):
    db.enqueue(conn, "https://WWW.Example.com/careers", name="Example")
    db.enqueue(conn, "example.com", name="Example Inc")

    rows = conn.execute("SELECT * FROM companies").fetchall()
    assert len(rows) == 1
    assert rows[0]["domain"] == "example.com"


def test_filter_new_returns_only_unseen_domains(conn):
    db.enqueue(conn, "sarvam.ai", name="Sarvam")

    result = db.filter_new(conn, ["sarvam.ai", "https://www.newco.dev/", "newco.dev"])

    assert result == ["newco.dev"]


def test_rejected_with_ttl_excluded_today_included_after_expiry(conn):
    db.enqueue(conn, "temp-reject.com", name="TempReject")
    db.reject(conn, "temp-reject.com", reason="no open roles right now", recheck_in="45d")

    batch_today = db.next_batch(conn, limit=50)
    assert "temp-reject.com" not in [r["domain"] for r in batch_today]

    # simulate the recheck date having passed
    past = (date.today() - timedelta(days=1)).isoformat()
    conn.execute(
        "UPDATE companies SET recheck_after = ? WHERE domain = 'temp-reject.com'", (past,)
    )
    conn.commit()

    batch_later = db.next_batch(conn, limit=50)
    assert "temp-reject.com" in [r["domain"] for r in batch_later]


def test_permanently_rejected_never_appears_in_next_batch(conn):
    db.enqueue(conn, "services-co.com", name="Services Co")
    db.reject(conn, "services-co.com", reason="services business", recheck_in="permanent")

    row = conn.execute(
        "SELECT recheck_after FROM companies WHERE domain = 'services-co.com'"
    ).fetchone()
    assert row["recheck_after"] == db.PERMANENT

    batch = db.next_batch(conn, limit=50)
    assert "services-co.com" not in [r["domain"] for r in batch]


def test_record_on_unknown_domain_raises(conn):
    with pytest.raises(db.UnknownDomainError):
        db.record(conn, "never-seen.com", {"score": 90, "tier": "A"})


def test_reject_on_unknown_domain_raises(conn):
    with pytest.raises(db.UnknownDomainError):
        db.reject(conn, "never-seen.com", reason="whatever")


def test_mark_on_unknown_domain_raises(conn):
    with pytest.raises(db.UnknownDomainError):
        db.mark(conn, "never-seen.com", status="applied")


def test_record_cli_on_unknown_domain_exits_nonzero(tmp_path, db_path):
    json_file = tmp_path / "payload.json"
    json_file.write_text('{"score": 90, "tier": "A"}', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent.parent / "scripts" / "db.py"),
         "--db", str(db_path), "record", "never-seen.com", "--json", str(json_file)],
        capture_output=True, text=True,
    )

    assert result.returncode != 0
    assert "never-seen.com" in result.stderr


# ---------------------------------------------------------------------------
# Additional coverage for the rest of the CLI surface
# ---------------------------------------------------------------------------

def test_record_sets_status_enriched_and_fields(conn):
    db.enqueue(conn, "goodco.ai", name="GoodCo")
    db.record(conn, "goodco.ai", {"score": 88, "tier": "A", "sector": "agent infra"})

    row = conn.execute("SELECT * FROM companies WHERE domain = 'goodco.ai'").fetchone()
    assert row["status"] == "enriched"
    assert row["score"] == 88
    assert row["tier"] == "A"
    assert row["sector"] == "agent infra"
    assert row["last_verified"] == db.today()


def test_next_batch_includes_fresh_candidates(conn):
    db.enqueue(conn, "a.com", name="A")
    db.enqueue(conn, "b.com", name="B")

    batch = db.next_batch(conn, limit=15)
    assert {r["domain"] for r in batch} == {"a.com", "b.com"}


def test_stale_source_prefers_never_run_then_least_recent(conn):
    conn.execute("INSERT INTO search_log (source, label) VALUES ('src:a', 'A')")
    conn.execute(
        "INSERT INTO search_log (source, label, last_run_at) VALUES ('src:b', 'B', '2020-01-01')"
    )
    conn.commit()

    picked = db.get_stale_sources(conn, n=1)
    assert picked[0]["source"] == "src:a"  # never run comes first

    picked2 = db.get_stale_sources(conn, n=1)
    assert picked2[0]["source"] == "src:b"  # now the least-recently-run


def test_enqueue_increments_found_new_for_source(conn):
    conn.execute("INSERT INTO search_log (source, label) VALUES ('yc:W26', 'YC W26')")
    conn.commit()

    db.enqueue(conn, "newco.ai", name="NewCo", via="yc:W26")

    row = conn.execute("SELECT found_new FROM search_log WHERE source = 'yc:W26'").fetchone()
    assert row["found_new"] == 1


def test_mark_applied_sets_applied_at_and_followup(conn):
    db.enqueue(conn, "applyco.com", name="ApplyCo")
    db.record(conn, "applyco.com", {"score": 82, "tier": "A"})
    db.mark(conn, "applyco.com", status="applied", contact="founder@applyco.com",
            followup_in="10d")

    row = conn.execute("SELECT * FROM companies WHERE domain = 'applyco.com'").fetchone()
    assert row["status"] == "applied"
    assert row["applied_at"] == db.today()
    assert row["contact"] == "founder@applyco.com"
    assert row["followup_due"] == (date.today() + timedelta(days=10)).isoformat()


def test_followups_due_only_returns_past_due_without_outcome(conn):
    db.enqueue(conn, "due.com", name="Due")
    db.record(conn, "due.com", {"score": 82, "tier": "A"})
    db.mark(conn, "due.com", status="applied", followup_in="0d")

    db.enqueue(conn, "notdue.com", name="NotDue")
    db.record(conn, "notdue.com", {"score": 82, "tier": "A"})
    db.mark(conn, "notdue.com", status="applied", followup_in="30d")

    due = db.followups_due(conn)
    assert [r["domain"] for r in due] == ["due.com"]


def test_export_csv_writes_expected_rows(conn, tmp_path):
    db.enqueue(conn, "tiera.com", name="TierA")
    db.record(conn, "tiera.com", {"score": 90, "tier": "A"})
    db.enqueue(conn, "tierc.com", name="TierC")
    db.record(conn, "tierc.com", {"score": 40, "tier": "C"})

    out = tmp_path / "out.csv"
    n = db.export_csv(conn, ["A", "B"], out)

    assert n == 1
    content = out.read_text(encoding="utf-8")
    assert "tiera.com" in content
    assert "tierc.com" not in content


def test_init_is_idempotent(tmp_path):
    p = tmp_path / "reinit.db"
    c = db.get_connection(p)
    db.init_db(c, sources_path=tmp_path / "missing.yaml")
    db.enqueue(c, "x.com", name="X")
    db.init_db(c, sources_path=tmp_path / "missing.yaml")  # must not wipe data

    row = c.execute("SELECT * FROM companies WHERE domain = 'x.com'").fetchone()
    assert row is not None
    c.close()
