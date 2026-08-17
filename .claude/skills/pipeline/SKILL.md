---
name: pipeline
description: Run one cycle of the job-search research pipeline — discover companies from
  the least-recently-scanned source, enrich a batch of candidates, score them, and export
  Tier A/B. Use when asked to run the pipeline or find new companies.
---

# Job search pipeline — one run

Read `config/criteria.md` before doing anything else. It is the authority on targets,
exclusions and scoring.

## Rules that must not be broken
1. NEVER write SQL directly. All state access goes through `scripts/db.py`.
2. EVERY company you look at gets an outcome — `record` or `reject`. No silent skips.
   A company examined and forgotten will be re-researched forever.
3. Never invent a fact. "unknown" is always acceptable; a plausible guess is not.
4. Respect the batch limit. Do not enrich beyond it even if the budget feels available.

## Steps

1. `python scripts/db.py stale-source` — get the source to scan.
2. Scan that source on the web. Extract company names and websites. Aim for 20-40.
   - **For `board:*` sources** (a specific remote-jobs board, e.g. Wellfound, RemoteOK):
     if a direct fetch of the board is blocked or fails, do NOT fall back to a generic
     "AI startup funding hiring" web search — that pulls in well-known, heavily-funded
     companies with no actual connection to the board, and most will fail the
     remote-evidence gate for nothing, wasting the batch. Instead use `site:<board-domain>`
     scoped search queries (e.g. `site:wellfound.com remote AI engineer`,
     `site:remoteok.com AI startup`) so every discovered candidate is an actual listing
     from that board. A search snippet that already shows "Remote" or a location in its
     title (e.g. "• Bengaluru • Remote (Work from Home)") is a strong early signal —
     prefer these over snippets with no location/remote info at all.
   - For `theme:*`, `vertical:*`, `investor:*`, `recency:*` sources, which aren't tied to
     one board, a general web search on the theme is fine — there's no board population
     to stay scoped to.
3. `python scripts/db.py filter-new <domains>` — keep only what comes back.
4. `python scripts/db.py enqueue` each new one with `--via <source id>`.
5. `python scripts/db.py next-batch --limit 15`.
6. For each company in the batch:
   - Apply hard exclusions first — cheapest check, do it before any research.
   - Check remote evidence next. No evidence → reject, do not research further.
   - Research the remaining fields. Score using the rubric. Set tier.
   - Write a JSON file per company and call `record`, or call `reject` with a reason
     and TTL.
7. `python scripts/db.py export --tier A,B --out exports/tier-ab.csv`
8. `python scripts/db.py report --out README.md` — human-readable ranked-candidates table,
   rejection-reason breakdown, and source-rotation status. This is the primary way anyone
   (including you, next run) sees results without querying the db directly.
9. `python scripts/db.py stats` and report: sources scanned, new discovered, enriched,
   rejected with reason breakdown, new Tier A companies by name, outreach flags raised.
10. `git add -A && git commit -m "pipeline run <date>"`

## Report format
Keep the summary under 15 lines. Name new Tier A companies and outreach flags
explicitly — those are the only things needing attention today.
