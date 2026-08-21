#!/usr/bin/env python3
"""
scripts/find_contacts.py — find founder/engineer contact routes for a target company,
using only free public sources (the GitHub API via `gh`, which is already authenticated).

Why this exists: the pipeline reliably finds founders' LinkedIn URLs but rarely an email,
so most outreach was stuck starting with a LinkedIn DM. Technical founders at AI startups
usually have public GitHub activity, and git commits carry a real author email.

Usage:
    python scripts/find_contacts.py --org lamatic
    python scripts/find_contacts.py --domain lamatic.ai --name "Aman Sharma"
    python scripts/find_contacts.py --user amanintech

Output is JSON so the pipeline can drop it straight into `outreach_contact`.

IMPORTANT: everything reported here is observed, never inferred. Emails come from real
commit metadata or a profile field. This script never guesses `firstname@company.com` —
criteria.md forbids inventing addresses, and a bounced cold email is worse than a DM.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from typing import Any, Optional

# Emails that are noise rather than a contact route.
NOISE = re.compile(
    r"(noreply|no-reply|users\.noreply\.github\.com|actions@github|"
    r"bot@|\[bot\]|example\.com|localhost)",
    re.I,
)


def gh_api(path: str, jq: Optional[str] = None) -> Any:
    """Call the GitHub API through the `gh` CLI. Returns None on any failure."""
    if not shutil.which("gh"):
        raise SystemExit("error: `gh` CLI not found. Install it or use --no-github.")
    cmd = ["gh", "api", path]
    if jq:
        cmd += ["--jq", jq]
    try:
        # encoding is explicit: commit author names are UTF-8 and the Windows default
        # (cp1252) raises UnicodeDecodeError on the first non-Latin-1 name.
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return None
    if out.returncode != 0 or out.stdout is None:
        return None
    text = out.stdout.strip()
    if not text:
        return None
    if jq:
        return [l for l in text.splitlines() if l.strip()]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def clean_emails(pairs: list[str]) -> list[dict]:
    """pairs look like 'Name <email>'. Drop noise, dedupe, keep name association."""
    seen: dict[str, str] = {}
    for line in pairs or []:
        m = re.match(r"^(.*?)\s*<(.+?)>$", line.strip())
        if not m:
            continue
        name, email = m.group(1).strip(), m.group(2).strip().lower()
        if NOISE.search(email):
            continue
        seen.setdefault(email, name)
    return [{"email": e, "name": n} for e, n in seen.items()]


def profile(user: str) -> Optional[dict]:
    p = gh_api(f"users/{user}")
    if not p:
        return None
    return {
        "login": p.get("login"),
        "name": p.get("name"),
        "company": p.get("company"),
        "blog": p.get("blog"),
        "email": p.get("email"),
        "twitter": p.get("twitter_username"),
        "profile_url": p.get("html_url"),
    }


def emails_from_user_events(user: str) -> list[dict]:
    """Public PushEvents expose the commit author email the user pushes with."""
    rows = gh_api(
        f"users/{user}/events/public?per_page=100",
        '.[] | select(.type=="PushEvent") | .payload.commits[]? '
        '| (.author.name) + " <" + (.author.email) + ">"',
    )
    return clean_emails(rows or [])


def rank_email(email: str, domain: Optional[str]) -> str:
    """
    How much to trust that this address belongs to the target company.

    Guessed org slugs can land on an unrelated project — searching `redacto` for
    redacto.ai returns an org whose commits are all @redact.dev, a different company.
    Emailing that address would be worse than sending nothing, so classify rather
    than dumping every address out at equal weight.
    """
    if not domain:
        return "unknown"
    root = domain.split(".")[0].lower()
    edomain = email.split("@")[-1].lower()
    if edomain == domain.lower():
        return "high — matches company domain"
    if root in edomain:
        return "medium — related domain, confirm it is the same company"
    if edomain in {"gmail.com", "outlook.com", "hotmail.com", "proton.me", "protonmail.com"}:
        return "low — personal address, confirm the person works there"
    return "low — unrelated domain, may be a different company entirely"


def emails_from_org(org: str, repo_limit: int = 5, commit_limit: int = 50) -> dict:
    """Walk an org's most recently pushed repos and collect commit author emails."""
    repos = gh_api(f"orgs/{org}/repos?sort=pushed&per_page={repo_limit}", ".[].name") or []
    found: list[dict] = []
    for repo in repos:
        rows = gh_api(
            f"repos/{org}/{repo}/commits?per_page={commit_limit}",
            '.[] | (.commit.author.name) + " <" + (.commit.author.email) + ">"',
        )
        found += clean_emails(rows or [])
    members = gh_api(f"orgs/{org}/members", ".[].login") or []
    # dedupe across repos
    dedup: dict[str, str] = {}
    for f in found:
        dedup.setdefault(f["email"], f["name"])
    return {
        "org": org,
        "repos_scanned": repos,
        "members": members,
        "commit_emails": [{"email": e, "name": n} for e, n in dedup.items()],
    }


def guess_orgs(domain: str) -> list[str]:
    """Candidate GitHub org slugs for a domain. Cheap to try, so try a few."""
    base = domain.split(".")[0].lower()
    return [base, f"{base}-ai", f"{base}ai", f"{base}-inc", f"{base}hq", f"get{base}"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Find contact routes from public GitHub data")
    ap.add_argument("--domain", help="company domain, e.g. lamatic.ai")
    ap.add_argument("--org", help="GitHub org slug, if you already know it")
    ap.add_argument("--user", help="a specific GitHub username to inspect")
    ap.add_argument("--name", help="person's name, used only to highlight matches")
    args = ap.parse_args()

    if not any([args.domain, args.org, args.user]):
        ap.error("give at least one of --domain, --org, --user")

    result: dict[str, Any] = {"query": vars(args), "org_results": [], "people": []}

    orgs = [args.org] if args.org else (guess_orgs(args.domain) if args.domain else [])
    for org in orgs:
        if not gh_api(f"orgs/{org}"):
            continue
        data = emails_from_org(org)
        data["guessed"] = args.org is None
        for e in data["commit_emails"]:
            e["confidence"] = rank_email(e["email"], args.domain)
        data["commit_emails"].sort(key=lambda e: not e["confidence"].startswith("high"))
        if data["guessed"] and not any(
            e["confidence"].startswith("high") for e in data["commit_emails"]
        ):
            data["warning"] = (
                f"org '{org}' was guessed from the domain and no address matches "
                f"{args.domain} — it may belong to an unrelated project. Verify before use."
            )
        result["org_results"].append(data)
        for login in data["members"][:10]:
            prof = profile(login)
            if prof:
                prof["commit_emails"] = emails_from_user_events(login)
                result["people"].append(prof)
        if args.org:
            break

    if args.user:
        prof = profile(args.user)
        if prof:
            prof["commit_emails"] = emails_from_user_events(args.user)
            result["people"].append(prof)

    if args.name:
        needle = args.name.lower()
        for bucket in result["org_results"]:
            bucket["name_matches"] = [
                e for e in bucket["commit_emails"] if needle in (e["name"] or "").lower()
            ]

    if not result["org_results"] and not result["people"]:
        result["note"] = (
            "No public GitHub presence found. Fall back to LinkedIn, the company's "
            "/team or /contact page, or a paid enrichment tool. Do NOT guess an address."
        )

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
