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
6. For each company in the batch, run `config/criteria.md`'s **four gates in order** and
   stop at the first failure — each gate is cheaper than the research that follows it:
   - **Gate 1 — AI-native software product?** Hardware, devices, manufacturing, launch
     vehicles, satellites, and non-AI software are permanent rejections no matter how good
     the team or funding look. Litmus test: *would they hire a Python/FastAPI/LLM backend
     engineer to build the core product?* If no, reject and move on.
   - **Gate 2 — Location.** Bangalore, remote-within-India, or remote-international with
     India eligibility. Onsite anywhere else in India (Delhi-NCR, Mumbai, Hyderabad, Pune)
     → reject, recheck 180d.
   - **Gate 3 — Can they pay 25-30+ LPA?** Needs ~$2M+ raised or verifiable revenue.
     Unfunded or bootstrapped with no revenue evidence → reject, recheck 180d.
   - **Gate 4 — Health and data freshness.** Actively search for layoffs, down rounds,
     failed raises, founder departures — do not just confirm the good news. Verify the
     funding round's **date**, not only that it happened. Put anything found in
     `risk_flags` with a source. Negative signals → reject, recheck 180d.
   - **"No open roles right now" is NOT a rejection.** Cold outreach is the primary
     channel — a promising 5-25 person company with no posting is a normal target.
   - Only now research the remaining fields. Score using the rubric. Set tier.
   - Identify the best human to email and fill `outreach_contact` and `outreach_angle`.
     Set `outreach_flag=1` for anything worth writing to.
   - **Try for a real email**: run `python scripts/find_contacts.py --domain <domain>`.
     It mines public GitHub commit metadata for addresses and returns each with a
     confidence rating. Only use ones rated **high** (address domain matches the company)
     without further checks; treat medium/low as leads to verify, and heed the `warning`
     field — a guessed org slug can belong to an unrelated project (searching `redacto`
     for redacto.ai returns a different company's @redact.dev addresses).
     Record the address AND where it came from, e.g.
     `shubham@collinear.ai (public commit in collinear-ai/<repo>)`.
   - **Never invent an email address.** No `firstname@company.com` guesses. If nothing is
     findable, give the LinkedIn and say so explicitly — a bounced cold email is worse
     than a DM.
   - Always set `name`. A row with a null name renders blank in the report and gets
     overlooked even when it scores well.
   - Write a JSON file per company and call `record`, or call `reject` with a reason
     and TTL.
7. `python scripts/db.py export --tier A,B --out exports/tier-ab.csv`
8. `python scripts/db.py report --out README.md` — human-readable ranked-candidates table,
   rejection-reason breakdown, and source-rotation status. This is the primary way anyone
   (including you, next run) sees results without querying the db directly.
9. `python scripts/db.py stats` and report: sources scanned, new discovered, enriched,
   rejected with reason breakdown, new Tier A companies by name, outreach flags raised.
10. `git add -A && git commit -m "pipeline run <date>"`, then `git push`. In a cloud
    Routine session the checkout is often a **detached HEAD**, not `master` — plain
    `git push` fails with "You are not currently on a branch" in that case. Check
    `git status`/`git branch` first, and if detached, push explicitly with
    `git push origin HEAD:master` instead. If the push still fails after that, do not
    retry in a loop and do not fall back to pushing a different branch — that just hides
    work nobody will see. Stop, and say so explicitly and first thing in your report: the
    commit exists locally, the push failed, and why (paste the actual git error). This
    matters more than anything else in the report, because unpushed work vanishes when
    this session ends and every subsequent run re-researches it from scratch.

## Report format
Keep the summary under 15 lines. Lead with the **new outreach targets** — name, who to
contact, and the one-line angle — since those are what he acts on. Then new Tier A
companies. If the push failed, that goes first, before anything else.
