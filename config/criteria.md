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
