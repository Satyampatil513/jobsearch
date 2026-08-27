# Research criteria

## How this pipeline is actually used
The primary channel is **cold outreach**, not applying to posted jobs. The goal of a run
is a ranked list of small, promising companies worth emailing a founder at — whether or
not they have an open listing. A posted role is a bonus, not a prerequisite.

"No open roles right now" is NOT a rejection. It is a normal outreach target.

---

# GATE 1 — Is it an AI-native software product company?

**Apply this before anything else. Failing it is a permanent rejection, no exceptions,
regardless of how good the team, funding or traction look.**

The company's *product that customers pay for* must be software, and AI/ML must be core
to it — not a feature bolted onto something else, and not an internal tool.

**Reject permanently as "not an AI-native software company":**
- Hardware, devices, manufacturing, components, avionics, aerospace parts
- Launch vehicles, satellites, satellite telecom, ground stations
- Physical products of any kind: air purifiers, fitness equipment, robotics-first, wearables
- Biotech / diagnostics whose product is a device, assay or physical test
- Any company where the engineering hiring is firmware, embedded, mechanical or hardware
- Non-AI software: a fintech, SaaS or marketplace that is simply a normal software product
  with no meaningful AI/ML core

**Real examples this gate exists to catch** (all were wrongly ranked at the top before it
existed): Aspera Industries (avionics component manufacturing — scored 100), QOSMIC
(satellite telecom), EtherealX (launch vehicles), Praan (air purifiers), Ferra/Aroleap
(fitness hardware), Dognosis (canine diagnostics devices), Resollect (fintech, not AI).

**Space is allowed only when the product is software.** Satellite *data analytics*,
geospatial AI, or ground software qualifies (Pixxel-shaped). Anything that flies, or that
is a physical component, does not. There is deliberately no space discovery source — space
software should surface through the AI/vertical sources on its own merit.

Litmus test: *"Would they hire a Python/FastAPI/LLM backend engineer to build the core
product?"* If the honest answer is no, reject.

---

# GATE 2 — Location (soft — scores, does not reject)

**This gate no longer rejects anything.** It used to be a hard cut when the pipeline was
India-only; now that sourcing has expanded to Europe/US, location is a scoring factor, not
a gatekeeper. Every company that passes Gates 1, 3 and 4 gets scored and recorded,
regardless of where it's based or what its remote policy is. Satyam is in Noida now and
would relocate for the right role, but a great non-India company is worth an outreach
email even with no India-specific hiring motion — it just scores lower than one that has
it.

**Location bands, for `hq_location` / `remote_policy` / `remote_evidence` and the scoring
modifier below:**
- **Bangalore / Bengaluru** — the bullseye, he will relocate. No penalty.
- **Remote-within-India** — genuinely remote for India-based employees. No penalty.
- **Remote-international with India eligibility** — per the evidence rules below. No
  penalty (the existing -15 "inferred rather than stated" modifier still applies).
- **Remote-international/global with no India-specific evidence** — e.g. "fully remote"
  or "remote worldwide" language but nothing naming India or APAC. See -20 modifier below.
- **Onsite only, anywhere outside Bangalore** — India (Noida, Gurugram, Delhi-NCR,
  Mumbai, Hyderabad, Pune, Chennai) or abroad (Munich, Berlin, Paris, NYC, etc.) with no
  stated remote policy at all. See -35 modifier below. (YoLearn.ai is the canonical
  example — Noida-onsite, still worth scoring, just heavily penalized.)

**Remote-international evidence** (needed to avoid the -20/-35 penalties below):
  (a) a job post saying remote worldwide / global / APAC / India
  (b) an existing employee based in India or APAC on LinkedIn
  (c) a stated EOR or contractor setup (Deel, Remote.com, Rippling, Oyster)
  (d) a public founder statement about hiring globally
Record which signal, quoted, in `remote_evidence`. No evidence found → still record and
score, just note "no remote evidence found" in `remote_evidence` and apply the
appropriate penalty below rather than rejecting.

---

# GATE 3 — Can they actually pay 25-30+ LPA?

He needs **25-30+ LPA (~$30-36k)**. A company that cannot plausibly pay that is a waste of
an email no matter how interesting it is.

**Passes** if either:
- **Raised roughly $2M or more** (total, and recent enough to still have runway), or
- **Verifiable revenue** that could support senior-ish salaries — e.g. Careerflow's
  reported $5.6M ARR while bootstrapped. Revenue claims need a source, not a vibe.

**Rejects (reason "cannot support target comp", recheck 180d):**
- Unfunded with no revenue evidence (timepay.ai — 13 people, unfunded)
- Bootstrapped with no revenue evidence (EaseOps)
- Tiny pre-seed only: sub-$1M / sub-Rs 5 Cr with nothing else going for it

Use 180d, not permanent — a seed round changes the answer, and these are otherwise often
good companies.

Record the actual number and its date in `total_funding` and `last_round`, and put the
comp reasoning in `score_rationale`. If funding genuinely cannot be found, write "unknown"
and treat it as failing this gate unless revenue evidence exists.

---

# GATE 4 — Is the company healthy, and is the data current?

A company can pass every gate above and still be a bad target because it is quietly
struggling. **Before enriching, actively search for negative signals** — do not just
confirm the good news.

Search explicitly for: layoffs, down round, shutdown, "failed to raise", founder or
senior-leadership departures, stalled hiring, acquisition-and-absorbed, dormant socials.

**Verify the DATE of the funding round, not just its existence.** Reporting an old round
as if it were recent is a serious error: Adopt AI was surfaced as "$6M Elevation seed in
2026" when the round was roughly two years old, the company had reportedly failed to raise
a Series A, and had recently done layoffs. None of that showed up because the research only
confirmed the round existed.

Rules:
- A round older than ~24 months is a **stale-funding risk** — say so explicitly and treat
  runway as questionable.
- Any negative signal found goes in `risk_flags`, verbatim with a source URL.
- Layoffs, a failed raise, or a founder exit → reject "declining / negative signals",
  recheck 180d.
- If `risk_flags` is empty, it must be because you looked and found nothing — not because
  you did not look.

---

## Candidate profile
- **Satyam Patil.** Research Engineer, Samsung Research Institute Noida, since June 2025
  (~1 YOE). Based in Noida; **target city Bangalore, willing to relocate.**
- **Education: IIT Mandi, B.Tech CSE (2021-2025)**, plus an exchange semester at
  **TU Dresden**. An IIT Mandi or TU Dresden founder is a warm-intro path worth flagging.
- Positioning: **backend + AI engineer, generalist builder, fast learner.** NOT a security
  specialist. Not a hardware, firmware or embedded engineer — he has no such experience,
  which is the other reason Gate 1 exists.
- Shipped work worth leading a cold email with:
  - **Rankit** (co-founder, full-stack) — AI-powered JEE mock-test platform, live with real
    users. FastAPI + PostgreSQL + Vite + LLM analysis; LangGraph post-exam insights
    pipeline. → edtech / applied AI / "I ship products with real users".
  - **CLAI** — context-aware CLI AI assistant with local RAG and persistent memory; built
    his own LLM abstraction layer before discovering LiteLLM. → devtools / agent infra.
  - **Samsung SELinux automation pipeline** — classifies policy issues, generates and
    validates rules, prepares change lists. → "automated a real workflow end-to-end".
  - **Consistify** — Flow/Cadence habit tracker. Only for crypto-adjacent companies.
- Differentiators: **NASA CanSat global Top 21**, **ISRO finalist**, IIT Roorkee hackathon
  winner. Useful for space-*software* companies; does not make hardware companies a fit.
- Stack: Python, FastAPI, PostgreSQL, async systems, LLM APIs, RAG, LangGraph, MCP, tool
  calling, Neo4j/Cypher, C++, DSA (~560 LeetCode), system design.
- Motivation: "bored at slow-paced MNC, want to own real problems and ship fast."

## Target roles
Founding Engineer, Member of Technical Staff, Applied AI Engineer, AI/ML Engineer,
Forward Deployed Engineer, Backend Engineer, Full-Stack AI Engineer, Agent/LLM
Infrastructure Engineer.

## Sectors, priority order (all must still pass Gate 1)
1. AI-native infrastructure and devtools (agents, LLM infra, eval, memory, orchestration)
2. Applied AI in a vertical — **edtech ranks highest** (Rankit gives him a real story)
3. AI-first SaaS / B2B
4. AI-first fintech — must be genuinely AI-core, not a fintech that mentions AI
5. Space **software** / geospatial AI

## Stage and size
Pre-seed to Series A, subject to Gate 3. Series B only if under 200 people and hiring hard.
Headcount 5-40; **5-25 is the sweet spot** — small enough that a founder reads their own
inbox, which is what makes cold email work.

## Other hard exclusions (reject permanently)
Services, consulting, agency, IT outsourcing. Recruiting firms. Web3-only / crypto-only.
Frontend-only, mobile-only, SDET, QA. **Pure security / infosec roles.** Large slow MNCs.
Dead: shut down, acquired and absorbed, no product, unreachable domain.

## Soft exclusions (reject with TTL)
- No funding, hiring, product or news signal in 12+ months → recheck 90d
- Fails Gate 3 (comp) → recheck 180d
- Fails Gate 4 (negative signals) → recheck 180d

Gate 2 (location) no longer rejects — see above. It only feeds the -20/-35 scoring
modifiers.

## Already contacted — reject permanently, reason "already in pipeline"
Emergent, GetCrux, LiteLLM, Synth, Infisical, ProhostAI, WarpBuild, Alaan, Wifi Dabba,
Coulomb AI, Pixxel, Cyble, Manufact (YC S25), AgentCollect, Synthio Labs, Berry,
Evam Labs, WisdomAI, Sarvam, Cardboard, Litmus, GoComet, Invariant AI, Vela,
Deployment.inc, Bolna.ai.

Match on the actual company, not a fuzzy name resemblance. **Manufex (manufex.co) is a
DIFFERENT company from Manufact (YC S25)** and is a live candidate. When a name is merely
similar, check the domain before excluding.

## Scoring — base 100
Only score companies that passed all four gates. Weighted for cold outreach: "can I reach
someone who might say yes to a 1-YOE generalist, at a company that can pay me" beats "is
there a posting today."

- **25% Likelihood they'd hire someone with ~1 YOE.** He has been rejected for 1 YOE
  against a 2-3 year bar. Score high for "0-2 years", "early career", "founding engineer,
  we care what you've shipped", new-grad hiring history, or a founder who evaluates on
  projects.
- **20% Ability to pay 25-30+ LPA.** Funding size and recency, revenue, and any published
  salary band. A company that just cleared Gate 3 on a technicality scores low here; a
  well-funded Series A that pays market scores high. **Never treat unfunded as neutral.**
- **15% Reachability.** Can a specific human be identified and emailed — founder or eng
  lead with a findable email, LinkedIn, or X? Tiny team where the founder reads their own
  inbox scores highest. A careers@ black hole scores low.
- **15% Founder and team quality.** He judges this hard and it drives his reply decisions.
  Score on: prior exits or notable employers, technical depth of the founding team,
  whether engineers already there look strong. Weak or thin-looking teams score low even
  when funding is fine. Say *why* in `score_rationale` — "second-time founder, sold Slintel
  to 6sense" beats "strong team".
- **10% Learning and career upside** — technical depth, exposure, what he'd learn.
- **10% Growth potential** — traction, market, investor quality.
- **5% Hiring signal, broadly defined.** A posted role is strongest, but recent funding,
  headcount growth, a new product line, or a founder posting about hiring all count.
  Absence of a posting is not a zero.

## Modifiers, capped at 100
- **+12 founder or senior engineer from IIT Mandi** (his alma mater) or TU Dresden — the
  strongest cold-email opener available
- +8 founder from another IIT, BITS Pilani, IIIT Hyderabad, NIT Trichy/Warangal
- +6 Bangalore-based
- +5 headcount 5-25
- +5 YC-backed or top-tier accelerator (Y Combinator, Antler, Surge, Accel Atoms).
  Scoring preference only — there are deliberately **no accelerator-specific discovery
  sources**, see `config/sources.yaml`.
- +5 domain overlap with his shipped work — edtech/exam-prep, devtools/CLI, agent memory
  or RAG infra
- +8 USD-denominated remote role open to India
- -15 `remote_evidence` inferred rather than stated. Applies ONLY when a genuine signal
  (a)-(d) exists but had to be pieced together. Not a way to enrich a company satisfying
  none of them, and not applicable to India-based companies.
- -20 remote-international/global with no India-specific evidence (Gate 2 soft penalty,
  "remote worldwide" language but nothing naming India/APAC)
- -35 onsite only, anywhere outside Bangalore — India or abroad — with no stated remote
  policy at all (Gate 2 soft penalty, replaces the old hard rejection)
- -20 stale funding (round older than ~24 months with no newer raise)

**A score of 100 should be nearly unreachable.** If a company hits the cap, re-check that
the modifiers are genuinely earned rather than the rubric saturating.

## Tiers
A = 80+   B = 65-79   C = below 65

## Outreach — the primary output
Set `outreach_flag=1` on every enriched company worth emailing — most of them, since the
gates now do the filtering. Set 0 only for a weak Tier C he would not bother writing to.

In `outreach_contact`: the single best human to email — name, role, and how to reach them
(email if findable, else LinkedIn or X). **Never invent an address.**

In `outreach_angle`, 3-4 lines:
1. The specific signal to open with (recent raise with its date, a launch, a founder post,
   a shared IIT Mandi / TU Dresden connection) and where you saw it.
2. The exact role to ask about.
3. Which project to lead with — **Rankit / CLAI / Samsung SELinux pipeline** — and why it
   maps to what they build. Be concrete.
4. Channel and why (founder email > LinkedIn DM > careers form).

## Verification rules
- Every enriched field needs a source URL. Cross-check funding and headcount across two
  sources.
- **Funding needs a date, not just an amount.** See Gate 4.
- Search for negative signals before enriching; record them in `risk_flags`.
- If a fact cannot be verified, write "unknown". Never invent funding figures, headcounts,
  LinkedIn URLs, email addresses or job links. A blank cell beats a fabricated one.
- Set last_verified on every record.
