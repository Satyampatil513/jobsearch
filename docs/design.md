# Job Search Pipeline — Build Spec

A local, stateful research pipeline that discovers and scores remote-international AI
startups, deduplicates deterministically across runs, and never re-researches the same
company twice.

Build this in **Claude Code**, in its own git repo. Work through the phases in order.
Do not skip Phase 1.

---

## 0. Design principles

Read these first. Every decision below follows from them.

1. **Deduplication lives in the data layer, not the model's memory.** The agent never
   recalls what it already searched. It asks SQLite, which answers deterministically.
2. **The canonical key is the root domain, not the company name.** "Sarvam" /
   "Sarvam AI" / "Sarvam.ai" must collapse to one row: `sarvam.ai`.
3. **Rejections are recorded as loudly as hits.** A company that was looked at and
   discarded must leave a row behind, or it gets re-researched forever.
4. **Rejections carry a TTL.** "Services business" is permanent. "No open roles right
   now" expires in ~45 days.
5. **Discovery and enrichment are separate stages.** Discovery is cheap and wide.
   Enrichment is expensive and deep. Any run drains the queue; there is no fixed
   day-by-day plan to keep in sync.
6. **Sources are tracked too, not just companies.** The agent picks the
   least-recently-scanned source each run.

---

## 1. Repo layout

```
jobsearch/
├─ .claude/skills/pipeline/SKILL.md
├─ scripts/db.py
├─ config/criteria.md
├─ config/sources.yaml
├─ docs/design.md          # this file
├─ tests/test_db.py
├─ jobsearch.db            # gitignored if using Desktop tasks; committed if using Routines
└─ exports/
```

---

## 2. Database schema

SQLite. Enable `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000` on every
connection so concurrent runs queue instead of erroring.

```sql
CREATE TABLE IF NOT EXISTS companies (
    domain          TEXT PRIMARY KEY,          -- canonical key, normalized
    name            TEXT,
    status          TEXT DEFAULT 'candidate',  -- candidate|enriched|rejected|applied
    reject_reason   TEXT,
    recheck_after   TEXT,                      -- ISO date; '9999-12-31' = permanent
    discovered_via  TEXT,                      -- source id, e.g. 'yc:W26'
    first_seen      TEXT DEFAULT CURRENT_TIMESTAMP,
    last_verified   TEXT,

    -- scoring
    score           REAL,
    tier            TEXT,                      -- A|B|C
    score_rationale TEXT,

    -- research fields
    sector          TEXT,
    sub_sector      TEXT,
    founding_year   TEXT,
    funding_stage   TEXT,
    total_funding   TEXT,
    last_round      TEXT,                      -- round + date
    investors       TEXT,
    founders        TEXT,
    founder_edu     TEXT,                      -- name institutions explicitly
    founder_bg      TEXT,
    headcount       TEXT,
    hq_location     TEXT,
    remote_policy   TEXT,
    remote_evidence TEXT,                      -- WHICH signal, quoted
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

    -- application tracking (Phase 5)
    applied_at      TEXT,
    contact         TEXT,
    followup_due    TEXT,
    outcome         TEXT,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS search_log (
    source      TEXT PRIMARY KEY,   -- 'yc:W26', 'wellfound:remote-ai'
    label       TEXT,
    last_run_at TEXT,
    runs        INTEGER DEFAULT 0,
    found_new   INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_status ON companies(status);
CREATE INDEX IF NOT EXISTS idx_tier ON companies(tier);
CREATE INDEX IF NOT EXISTS idx_recheck ON companies(recheck_after);
```

**Domain normalization** (one function, used everywhere):
lowercase → strip scheme → strip `www.` → strip path/query → strip trailing dot →
keep registrable domain only. `https://WWW.Sarvam.ai/careers` → `sarvam.ai`.

---

## 3. `scripts/db.py` — CLI spec

Claude must go through this script for all state access. No freehand SQL.

| Command | Behaviour |
|---|---|
| `init` | Create schema, set pragmas, seed `search_log` from `config/sources.yaml`. |
| `stale-source [--n 1]` | Return least-recently-scanned source id(s). Never-run sources first. |
| `filter-new <domains...>` | Normalize each, return only those absent from `companies`. Reads stdin if no args. **This is the dedup gate.** |
| `enqueue <domain> --name X --via Y` | `INSERT OR IGNORE` as `candidate`. Idempotent. |
| `next-batch --limit 15` | Return `candidate` rows oldest-first, plus any row whose `recheck_after` <= today. |
| `record <domain> --json FILE` | Write research fields, set `status='enriched'`, `last_verified=today`, score and tier. |
| `reject <domain> --reason X [--recheck-in 45d\|permanent]` | Set `status='rejected'`, reason, and `recheck_after`. |
| `mark <domain> --status applied [--contact X] [--followup-in 10d]` | Phase 5 application tracking. |
| `followups-due` | Rows where `followup_due` <= today and `outcome` is null. |
| `export --tier A,B --out FILE` | Write CSV. Column order fixed, defined in the script. |
| `stats` | Counts by status and tier, sources scanned, last run per source. |

Exit non-zero on unknown domain for `record`/`reject`/`mark` — silent no-ops hide bugs.

---

## 4. `config/sources.yaml` — seed list

```yaml
sources:
  - id: theme:agent-infra
    label: Agent infrastructure and orchestration
  - id: theme:llm-eval
    label: LLM eval and observability
  - id: theme:memory-context
    label: Memory and context systems
  - id: theme:voice-ai
    label: Voice AI
  - id: theme:rag-docs
    label: Document and RAG products
  - id: vertical:edtech-ai
    label: Applied AI — edtech
  - id: vertical:healthtech-ai
    label: Applied AI — healthtech
  - id: vertical:legal-ai
    label: Applied AI — legal and compliance
  - id: vertical:sales-support-ai
    label: Applied AI — sales and support
  - id: vertical:fintech-ai
    label: AI-first fintech
  - id: investor:accel-seed
    label: Accel seed-stage AI cheques
  - id: investor:peak-xv-surge
    label: Peak XV Surge AI cohort
  - id: investor:antler-elevation
    label: Antler / Elevation recent AI cheques
  - id: board:wellfound-remote-ai
    label: Wellfound — remote AI startups
  - id: board:remoteok-ai
    label: Remote OK — AI startups
  - id: theme:iit-founders-global
    label: IIT-founder-led AI startups in US and Europe
  - id: recency:seed-90d
    label: Seed rounds announced in the last 90 days
```

Add sources over time. Adding a row is all it takes for the rotation to pick it up.

No YC-batch sources on purpose — the goal is breadth across sectors/investors/boards,
not a directory crawl of one accelerator. If YC alumni surface through a generic search,
that's fine; there's just no dedicated source pointed at the YC company list.

---

## 5. `config/criteria.md` — the research brief

The skill reads this file. It replaces everything that used to be pasted per run.

```markdown
# Research criteria

## Candidate profile
- Research Engineer, Samsung Research Institute Noida, since June 2025 (~1 YOE):
  Android security architecture, SEAndroid policies, TEE<->Rich OS communication (ICCC),
  AOSP build system, Graph Neural Networks. Built an LLM automation pipeline that
  classifies policy issues, generates and validates rules, and prepares change lists
  (~80% of that work automated).
- Co-founder and full-stack engineer, Rankit — AI-powered JEE mock test product.
- Projects: CLI AI assistant with local RAG and persistent memory; knowledge-graph memory
  eval harness (LOCOMO runs, graph explorer, cost ledger); agentic health and transaction
  query agents.
- Stack: Python, FastAPI, PostgreSQL, async systems, LLM APIs, RAG, LangGraph, MCP, tool
  calling, Neo4j/Cypher, C++, DSA (~560 LeetCode), system design.
- Positioning: broad backend/AI engineer and generalist builder, NOT a security specialist.

## Target roles
Founding Engineer, Member of Technical Staff, Applied AI Engineer, AI/ML Engineer,
Forward Deployed Engineer, Backend Engineer, Full-Stack AI Engineer, Agent/LLM
Infrastructure Engineer.

## Primary target: remote-international
A company counts as remote-international ONLY with at least one of:
  (a) a job post saying remote worldwide / global / APAC / India
  (b) an existing employee based in India or APAC on LinkedIn
  (c) a stated EOR or contractor setup (Deel, Remote.com, Rippling, Oyster)
  (d) a public founder statement about hiring globally
Record which signal, quoted, in remote_evidence. No evidence means do not enrich —
reject with reason "no remote evidence", recheck in 90d.

Secondary: India-based startups in Bangalore, or remote-India.

## Sectors, priority order
1. AI-native infrastructure and devtools (agents, LLM infra, eval, memory, orchestration)
2. Applied AI in a vertical
3. AI-first SaaS / B2B
4. AI-first fintech

## Stage and size
Pre-seed to Series A. Series B only if under 200 people and hiring hard.
Headcount 5-40; 10-20 is the sweet spot.

## Compensation
25-30+ LPA India equivalent. USD-denominated remote roles preferred.

## Hard exclusions (reject permanently)
Services, consulting, agency, IT outsourcing. Web3-only. Frontend-only, mobile-only,
SDET, QA. Large slow MNCs. Requires US/EU work authorization with no remote path.

## Soft exclusions (reject with TTL)
No funding or hiring signal in 12 months → recheck 90d.
No open roles right now → recheck 45d.
No remote evidence → recheck 90d.

## Already in pipeline — reject permanently, reason "already applied"
Emergent, GetCrux, LiteLLM, Synth, Infisical, ProhostAI, Alaan, Wifi Dabba, Coulomb AI,
Pixxel, AgentCollect, Synthio Labs, Berry, Evam Labs, WisdomAI, Sarvam, Cardboard,
Litmus, GoComet, Invariant AI, Vela, Deployment.inc, Bolna.ai, WarpBuild.

## Scoring — base 100
- 30% Likelihood they'd hire someone with ~1 YOE. This is the binding constraint; I have
  been rejected for 1 YOE against a 2-3 year bar. Score high for "0-2 years", "early
  career", "founding engineer, we care what you've shipped", new-grad hiring history, or
  a founder who evaluates on projects.
- 20% Current hiring activity.
- 15% Learning and career upside — technical depth, founder calibre, exposure.
- 15% Growth potential — traction, market, investor quality.
- 10% Funding and runway; raised in last 18 months scores highest.
- 10% Ownership and exposure — small team, founder access, real scope, equity.

## Modifiers, capped at 100
+10 founder from IIT Bombay / Delhi / Madras / Kanpur / Kharagpur
+5  founder from another IIT, BITS Pilani, IIIT Hyderabad, NIT Trichy/Warangal
+5  headcount 10-20
+8  USD-denominated remote role open to India
-15 remote_evidence inferred rather than stated

## Tiers
A = 80+   B = 65-79   C = below 65

## Outreach flag
Set outreach_flag=1 when there is no suitable public opening but a clear imminent-hiring
signal: funded in last 6 months, founder posting about building the team, fast headcount
growth, new product line, or first engineering hires. In outreach_angle record: the
signal and its source, the exact role to pitch, which project to lead with (Rankit / KG
memory eval / CLI assistant / Samsung LLM pipeline) and why it fits them, plus who to
contact and on which channel.

## Verification rules
- Every enriched field needs a source URL. Cross-check funding and headcount across two
  sources.
- If a fact cannot be verified, write "unknown". Never invent funding figures, headcounts,
  LinkedIn URLs or job links. A blank cell beats a fabricated one.
- Set last_verified on every record.
```

---

## 6. `.claude/skills/pipeline/SKILL.md` — the run loop

```markdown
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
8. `python scripts/db.py stats` and report: sources scanned, new discovered, enriched,
   rejected with reason breakdown, new Tier A companies by name, outreach flags raised.
9. `git add -A && git commit -m "pipeline run <date>"`

## Report format
Keep the summary under 15 lines. Name new Tier A companies and outreach flags
explicitly — those are the only things needing attention today.
```

---

## 7. Build phases

### Phase 1 — `db.py` and tests, no web research
Build the script and make it correct before Claude ever touches the internet.

Required tests in `tests/test_db.py`:
- Inserting the same domain twice is a no-op.
- `https://WWW.Example.com/careers` and `example.com` collapse to one row.
- `filter-new` returns only unseen domains.
- A company rejected with `--recheck-in 45d` is excluded from `next-batch` today and
  included once that date passes.
- A permanently rejected company never appears in `next-batch`.
- `record` on an unknown domain exits non-zero.

Do not proceed until these pass.

### Phase 2 — Skill and config
Write `SKILL.md`, `criteria.md`, `sources.yaml`. Run `db.py init`.

### Phase 3 — One supervised run
Run interactively with `--limit 15`. Then audit, by hand:
- Open five Tier A rows and verify `source_urls` actually support the claims.
- Check `remote_evidence` is quoted, not inferred. If it's inferred, tighten criteria.
- Run the pipeline a second time and confirm **zero** companies get re-researched.

Do not automate until this run is clean. An unattended pipeline producing plausible
garbage is worse than no pipeline, because you will trust it.

### Phase 4 — Schedule
Claude Desktop → Schedule → New local task. Prompt: `/pipeline run`, working folder set
to the repo. Pick an off-minute (e.g. 8:07am) — the scheduler adds deterministic jitter
and `:00` / `:30` drift most.

Start at three runs a week, not daily.

Desktop tasks need the machine awake with the app open. If you want it running with the
laptop shut, use a cloud Routine instead — but Routines start from a fresh clone with no
state carried between runs, so `jobsearch.db` must be committed to the repo, and you
must enable pushes beyond `claude/`-prefixed branches for that repo.

### Phase 5 — Close the loop
Wire up `mark --status applied` and `followups-due` so the same table tracks applications,
not just discovery. "Who haven't I followed up with in 10 days" becomes one query.

---

## 8. Bootstrap prompt

Paste this into Claude Code after dropping this file at `docs/design.md`:

```
Read docs/design.md.

Build scripts/db.py per section 3, using the schema in section 2. SQLite with
WAL mode and busy_timeout=5000. Domain normalization exactly as specified in
section 2 — one shared function, used by every command.

Write tests/test_db.py covering every case listed in Phase 1.

Do not write the skill, do not create config files, and do not do any web
research yet. Stop when the tests pass and show me the results.
```

Then, once green:

```
Now create .claude/skills/pipeline/SKILL.md, config/criteria.md and
config/sources.yaml exactly as specified in sections 4-6 of docs/design.md.
Run db.py init. Do not run the pipeline yet.
```

---

## 9. The one thing to watch

The temptation is to skip Phase 1 and let Claude manage state conversationally, because
it appears to work. It works for roughly four runs, then `Sarvam` and `Sarvam AI` become
separate rows and the dedup guarantee is gone with no error to tell you. The script is
the whole design.
