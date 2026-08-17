# Research criteria

## How this pipeline is actually used
The primary channel is **cold outreach**, not applying to posted jobs. The goal of a run
is a ranked list of small, promising companies worth emailing a founder at — whether or
not they have an open listing. A posted role is a bonus, not a prerequisite.

This means: **"no open roles right now" is NOT a rejection.** It is a normal outreach
target. Only reject for the hard/soft exclusions listed below.

## Candidate profile
- **Satyam Patil.** Research Engineer, Samsung Research Institute Noida, since June 2025
  (~1 YOE). Based in Noida; **target city Bangalore, willing to relocate.**
- **Education: IIT Mandi, B.Tech CSE (2021-2025)**, plus an exchange semester at
  **TU Dresden**. This matters twice: as pedigree, and because an IIT Mandi or TU Dresden
  founder is a warm-intro path worth flagging.
- Positioning: **backend + AI engineer, generalist builder, fast learner.** NOT a security
  specialist — he does not want pure-security roles despite the SELinux work.
- Shipped work worth leading a cold email with:
  - **Rankit** (co-founder, full-stack) — AI-powered JEE mock-test platform, live with real
    users at a coaching institute. FastAPI + PostgreSQL + Vite + LLM analysis; currently
    building a LangGraph post-exam insights pipeline. → the edtech / applied-AI / "I ship
    products with real users" story.
  - **CLAI** — context-aware CLI AI assistant with local RAG and persistent memory; built
    his own LLM abstraction layer before discovering LiteLLM. → the devtools / agent-infra
    / "I build the tools I need" story.
  - **Samsung SELinux automation pipeline** — classifies incoming policy issues, generates
    and validates rules, prepares change lists; eliminated manual work for routine cases.
    → the "automated a real workflow end-to-end inside a big org" story.
  - **Consistify** — Flow/Cadence habit tracker with a custom fungible token. → only useful
    for crypto-adjacent companies; do not lead with it otherwise.
- Achievements that differentiate: **NASA CanSat global Top 21**, **ISRO finalist**,
  IIT Roorkee hackathon winner. Strong hook for space/deep-tech companies specifically.
- Stack: Python, FastAPI, PostgreSQL, async systems, LLM APIs, RAG, LangGraph, MCP, tool
  calling, Neo4j/Cypher, C++, DSA (~560 LeetCode), system design.
- Motivation, in his words: "bored at slow-paced MNC, want to own real problems and ship
  fast." Prefers small fast teams. Wants to maximize income early.

## Target roles
Founding Engineer, Member of Technical Staff, Applied AI Engineer, AI/ML Engineer,
Forward Deployed Engineer, Backend Engineer, Full-Stack AI Engineer, Agent/LLM
Infrastructure Engineer.

## Geography — TWO co-primary targets
Either one qualifies. Do not reject a company for failing the other.

**(A) India-based.** Bangalore is the bullseye; anywhere in India counts. An India-based
company needs **no remote evidence at all** — he will relocate or commute. Never reject an
India-based company for "no remote evidence" or "in-office preferred". Record its office
city in `hq_location` and move on.

**(B) Remote-international.** For a company with **no India presence**, require at least
one of:
  (a) a job post saying remote worldwide / global / APAC / India
  (b) an existing employee based in India or APAC on LinkedIn
  (c) a stated EOR or contractor setup (Deel, Remote.com, Rippling, Oyster)
  (d) a public founder statement about hiring globally
Record which signal, quoted, in `remote_evidence`. No such evidence → reject with reason
"no remote evidence", recheck 90d. Evidence that is pieced together indirectly rather than
cleanly quoted still counts, but takes the -15 modifier (see below).

## Sectors, priority order
1. AI-native infrastructure and devtools (agents, LLM infra, eval, memory, orchestration)
2. Applied AI in a vertical — **edtech ranks highest here** (Rankit gives him a real story)
3. AI-first SaaS / B2B
4. AI-first fintech
5. Space / deep tech with a software or AI core (CanSat + ISRO give him a rare hook)

## Stage and size
Pre-seed to Series A. Series B only if under 200 people and hiring hard.
Headcount 5-40; **5-25 is the sweet spot** — small enough that a founder reads their own
inbox, which is what makes cold email work.

## Compensation
25-30+ LPA India equivalent. USD-denominated remote roles preferred.

## Hard exclusions (reject permanently)
- Services, consulting, agency, IT outsourcing
- Web3-only / crypto-only
- Frontend-only, mobile-only, SDET, QA
- **Pure security / infosec roles** — he is explicitly not pursuing security as an identity
- Large slow MNCs
- Requires US/EU work authorization with no remote path **and** no India presence
- Dead: shut down, acquired and absorbed, or no product

## Soft exclusions (reject with TTL)
- No funding, hiring, product or news signal in 12+ months → recheck 90d (genuinely dormant)
- No remote evidence, **non-India companies only** → recheck 90d

**Explicitly NOT a rejection any more:** "no open roles right now." Enrich it, set
`outreach_flag=1`, and write the angle. That is the point of the pipeline.

## Already contacted — reject permanently, reason "already in pipeline"
Emergent, GetCrux, LiteLLM, Synth, Infisical, ProhostAI, WarpBuild, Alaan, Wifi Dabba,
Coulomb AI, Pixxel, Cyble, Manufact, AgentCollect, Synthio Labs, Berry, Evam Labs,
WisdomAI, Sarvam, Cardboard, Litmus, GoComet, Invariant AI, Vela, Deployment.inc,
Bolna.ai.

## Scoring — base 100
Weighted for cold outreach: "can I reach a decision-maker who might say yes to a 1-YOE
generalist" matters more than "is there a posting today."

- **30% Likelihood they'd hire someone with ~1 YOE.** The binding constraint; he has been
  rejected for 1 YOE against a 2-3 year bar. Score high for "0-2 years", "early career",
  "founding engineer, we care what you've shipped", new-grad hiring history, or a founder
  who evaluates on projects.
- **15% Reachability.** Can a specific human be identified and emailed — founder or eng
  lead with a findable email, LinkedIn, or X? Tiny team where the founder reads their own
  inbox scores highest. A company behind a careers@ black hole scores low.
- **15% Learning and career upside** — technical depth, founder calibre, exposure.
- **10% Hiring signal, broadly defined.** A posted role is the strongest, but recent
  funding, headcount growth, a new product line, or a founder posting about building the
  team all count. Absence of a posting is not a zero.
- **10% Growth potential** — traction, market, investor quality.
- **10% Funding and runway**; raised in last 18 months scores highest.
- **10% Ownership and exposure** — small team, founder access, real scope, equity.

## Modifiers, capped at 100
- **+12 founder or senior engineer from IIT Mandi** — his alma mater; the single strongest
  cold-email opener available. Also applies to TU Dresden.
- +8 founder from another IIT, BITS Pilani, IIIT Hyderabad, NIT Trichy/Warangal
- +6 India-based, Bangalore especially — no visa/remote friction at all
- +5 headcount 5-25
- +5 YC-backed or top-tier accelerator (Y Combinator, Antler, Surge). Note: this is a
  scoring preference only — there are deliberately **no YC-specific discovery sources**,
  see `config/sources.yaml`.
- +5 domain overlap with his shipped work — edtech/exam-prep, devtools/CLI, agent memory
  or RAG infra, or space/deep tech. Overlap gives the cold email a concrete hook.
- +8 USD-denominated remote role open to India
- -15 `remote_evidence` inferred rather than stated. Applies ONLY when a genuine signal
  (a)-(d) exists but had to be pieced together from indirect language rather than a clean
  quote. It is NOT a way to enrich a company that satisfies none of (a)-(d): a careers page
  listing specific countries (UK, Poland, Brazil...) without naming India/APAC or saying
  worldwide/global is not evidence at all — that is a hard reject with reason "no remote
  evidence". **Does not apply to India-based companies**, which need no remote evidence.

## Tiers
A = 80+   B = 65-79   C = below 65

## Outreach — the primary output
Set `outreach_flag=1` on **every enriched company he should actually email**, which is
most of them. Set it to 0 only when the company is a weak fit he would not bother writing
to (roughly, Tier C with no hook).

Having an open role does not clear the flag — a cold email to a founder often beats an
application into a form, especially at 5-25 person companies.

In `outreach_contact`, record the single best human to email: name, role, and however they
can be reached (email if findable, else LinkedIn or X). Never invent an address — if no
email is findable, say so and give the LinkedIn.

In `outreach_angle`, write the actual pitch in 3-4 lines:
1. The specific signal to open with (their recent raise, a launch, a founder post, a shared
   IIT Mandi / TU Dresden connection) and where you saw it.
2. The exact role to ask about.
3. Which project to lead with — **Rankit / CLAI / Samsung SELinux pipeline / CanSat** — and
   why it maps to what they are building. Be concrete: "they're building eval infra, lead
   with the KG memory eval harness," not "lead with relevant experience."
4. Channel and why (founder email > LinkedIn DM > careers form).

## Verification rules
- Every enriched field needs a source URL. Cross-check funding and headcount across two
  sources.
- If a fact cannot be verified, write "unknown". Never invent funding figures, headcounts,
  LinkedIn URLs, email addresses or job links. A blank cell beats a fabricated one.
- Set last_verified on every record.
