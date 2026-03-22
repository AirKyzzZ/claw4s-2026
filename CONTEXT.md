# CONTEXT.md — For Claude Code Sessions

## About This Project
Submission to the **Claw4S Conference 2026** — a hackathon hosted by **Stanford University & Princeton University**.
- Deadline: April 5, 2026
- Prize Pool: $50,200 — up to 364 winners
- Format: executable SKILL.md + research paper submitted to clawRxiv (http://18.118.210.52)
- Scoring: Executability (25pts) + Reproducibility (25pts) + Scientific Rigor (20pts) + Generalizability (15pts) + Clarity for Agents (15pts)

## About Maxime
- 19 years old, Bordeaux (France), Software Engineer @ Verana.io + 2060.io
- Expert in SSI (Self-Sovereign Identity), DIDComm, W3C Verifiable Credentials, DIDs
- Built Concieragent: orchestrator of 6 MCP servers via encrypted DIDComm, multi-LLM
- Strong in TypeScript, Python, Next.js, blockchain (COSMOS SDK)
- NOT a biology expert — the research topic must stay in his domain of expertise

## ✅ LOCKED: Research Direction

### Title (working)
**"Trustless Scientific Collaboration: A Minimal DIDComm Protocol for Decentralized Agent-to-Agent Trust in Multi-Agent Research Pipelines"**

### The Core Problem
All current multi-agent frameworks (AutoGen, CrewAI, LangGraph) rely on a **central orchestrator** — a single coordinator that tells agents what to do and trusts them implicitly. This creates:
1. A single point of failure (orchestrator compromise = full pipeline compromise)
2. No cryptographic proof of *who* said *what* in the pipeline
3. Impossibility of truly decentralized collaboration between agents from different organizations

### The Research Question (Direction 1 — LOCKED)
> "Can two previously unknown AI agents establish mutual cryptographic trust and collaboratively produce a scientific artifact, without relying on any central authority or pre-shared secrets — and what is the minimal protocol required?"

This is about **demonstrating feasibility** and **defining the minimal protocol**, NOT claiming it's "better" than centralized approaches (that would require bio expertise we don't have).

### The Contribution
1. A **formal minimal protocol** for agent-to-agent trust bootstrapping using DID:key + DIDComm
2. An **executable TP (interactive lab)** where the agent running the skill PARTICIPATES in the trust establishment — it's not a passive observer
3. **Measurable metrics**: number of protocol round-trips, overhead in ms, success/failure of trust verification
4. The first **agent-native, interactive tutorial** on decentralized agent trust for scientific workflows

### Why This is Novel
- OWASP 2025: "No strong provenance assurances exist in published models"
- All SSI/DID work focuses on human identity, not agent-to-agent runtime trust
- The "TP interactif" format is unique on clawRxiv — no other paper does this
- Zero competition on clawRxiv (0 papers on SSI/DID/agent-trust)

### The Scientific Task (use case)
**Collaborative literature synthesis on arXiv** — two agents analyze papers from arXiv API (free, no signup) and produce a joint report. Agent A fetches + parses. Agent B analyzes + synthesizes. They establish DIDComm trust BEFORE exchanging any data.

Why arXiv: free API, no signup, agent-native, meta-referential for a research conference, reproducible by anyone.

## The "TP Interactif" Format
The SKILL.md is designed as an **interactive lab** where the executing agent:
1. Plays the role of "Agent B" (the analyzer)
2. Receives a DID handshake request from a mock "Agent A" (DataFetcher)
3. Verifies the credential, establishes the secure channel
4. Executes the collaborative task
5. Signs and returns its own output

This means the agent running the skill *experiences* the protocol, not just observes it.

## SKILL.md Architecture (draft)
```
Agents:
- AgentA (DataFetcher): did:key:z6MkAgentA — fetches arXiv papers, signs output VC
- AgentB (Analyzer): did:key:z6MkAgentB — verifies AgentA's VC, analyzes, signs output
- AuditLog: verifies full chain at end

Modes:
- --mode mock: fully offline, fixture JSON, no external deps (for full score)
- --mode live: real arXiv API calls
- --mode attack: AgentA replaced by FakeAgent with wrong DID → detected

Tools needed: Bash(python3 *), WebFetch (for live mode only)

Measurable outputs:
- trust_established: bool
- round_trips: int
- overhead_ms: float
- audit_chain: list of signed VCs
- attack_detected: bool (in attack mode)
```

## Key Decisions Log
- ❌ Eliminated: Sybil attacks on Verana VPR (too niche, not AI4Science enough)
- ❌ Eliminated: Drug discovery with ChEMBL (bio expertise required, metrics tautological)
- ❌ Eliminated: Reproducibility audit of clawRxiv (jury already has this)
- ✅ Chosen: Decentralized agent trust protocol, TP interactif format, arXiv use case
- 🎬 Bonus (time permitting): Short YouTube video walkthrough of the TP

## Submission Format (clawRxiv)
POST http://18.118.210.52/api/posts with:
- title, abstract, content (Markdown + LaTeX), tags, human_names, skill_md
- Register first: POST /api/auth/register {"claw_name": "clawdbot-maxime"}

## Relevant Resources
- VPR spec: https://verana-labs.github.io/verifiable-trust-vpr-spec/
- VT spec: https://verana-labs.github.io/verifiable-trust-spec/
- arXiv API: https://arxiv.org/help/api/
- did:key spec: https://w3c-ccg.github.io/did-key-draft/
- DIDComm spec: https://identity.foundation/didcomm-messaging/spec/

## Next Steps
- [ ] Finalize protocol design (exact message format for DID handshake)
- [ ] Implement mock agents in Python (did:key + Ed25519 signing)
- [ ] Write paper draft
- [ ] Build SKILL.md with all 3 modes (mock/live/attack)
- [ ] Submit to clawRxiv before April 5
- [ ] (Bonus) Record YouTube walkthrough
