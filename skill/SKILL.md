---
name: decentralized-agent-trust-protocol
description: >
  Interactive lab (TP interactif) demonstrating a minimal DIDComm-inspired protocol
  for decentralized agent-to-agent trust using did:key (Ed25519) and W3C Verifiable
  Credentials. The executing agent participates as Agent B (Analyzer) in a mutual
  trust handshake with a simulated Agent A (DataFetcher), then collaboratively
  produces a signed scientific artifact. Supports mock (offline), live (arXiv API),
  and attack (impersonation detection) modes.
allowed-tools: Bash(python3 *), Bash(pip3 *), WebFetch
license: MIT
metadata:
  skill-author: Maxime Mansiet & Claw
  skill-category: Multi-Agent Systems / Decentralized Trust
  tags: [did-key, didcomm, verifiable-credentials, agent-trust, ed25519, multi-agent, ssi]
---

# Decentralized Agent-to-Agent Trust Protocol

## Overview

This skill implements and demonstrates a **minimal protocol for two previously unknown AI agents to establish mutual cryptographic trust** without any central authority or pre-shared secrets. It uses:

- **did:key** (Ed25519) for self-sovereign agent identity
- **W3C Verifiable Credentials** for capability attestation and data signing
- **A 2-round-trip handshake** for mutual authentication

The executing agent doesn't just observe — it **participates** as Agent B (Analyzer) in the trust establishment, verifies Agent A's credentials, processes signed data, and produces its own signed output. This is an interactive lab, not a passive demo.

### Why This Matters

All current multi-agent frameworks (AutoGen, CrewAI, LangGraph) rely on a central orchestrator that trusts agents implicitly. This creates:
1. A single point of failure (orchestrator compromise = full pipeline compromise)
2. No cryptographic proof of who said what in the pipeline
3. Impossibility of truly decentralized collaboration between agents from different organizations

This protocol demonstrates that **2 round trips and <5ms of crypto overhead** are sufficient to establish verifiable mutual trust between unknown agents.

## When to Use This Skill

Use this skill when:

- You want to understand how decentralized agent trust works in practice
- You need to evaluate whether two agents can establish trust without a coordinator
- You are researching provenance and auditability in multi-agent scientific pipelines
- You want to test impersonation attack detection in agent-to-agent communication
- You are exploring alternatives to centralized orchestration for multi-agent systems

## Prerequisites

**Single dependency**: the `cryptography` Python package (widely available, provides Ed25519).

```bash
pip3 install cryptography
```

No external services, no API keys, no network access required for mock mode.

## Reproduction Steps

### Step 1: Environment Setup

Install the required dependency and verify the protocol script is available.

```bash
pip3 install cryptography
```

```bash
python3 -c "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; print('Ed25519 available: OK')"
```

### Step 2: Run the Protocol in Mock Mode (Offline)

This is the primary execution mode. It uses fixture data (5 curated arXiv paper records) and requires zero network access. This mode demonstrates the full protocol:

1. **Agent Identity Generation** — Two agents generate did:key identities (Ed25519 keypairs)
2. **Mutual Trust Handshake** — Agent A presents a signed Capability Credential; Agent B verifies it. Agent B responds with its own; Agent A verifies. Trust established in 2 round trips.
3. **Signed Data Exchange** — Agent A signs the fetched dataset as a Verifiable Credential. Agent B verifies the signature and issuer DID before processing.
4. **Collaborative Analysis** — Agent B analyzes the verified papers and signs its analysis report as a VC.
5. **Audit Chain Verification** — All VCs in the pipeline are verified end-to-end.

```bash
python3 skill/trust_protocol.py --mode mock
```

**Expected output**: Trust established, 2 round trips, <5ms overhead, all audit checks passing.

To get structured JSON output for programmatic analysis:

```bash
python3 skill/trust_protocol.py --mode mock --json
```

### Step 3: Run the Attack Simulation

This mode runs the full protocol first, then simulates an **impersonation attack**: a fake agent claims Agent A's DID but signs with different keys. The protocol must detect and reject this.

```bash
python3 skill/trust_protocol.py --mode attack
```

**Expected output**: Same successful protocol run as mock, PLUS attack detection — the fake agent's signature fails verification against the claimed DID because the keys don't match. `attack_detected: True`.

This demonstrates that the did:key binding (DID ↔ public key) is cryptographically enforced — you cannot claim someone else's identity without their private key.

### Step 4: Run with Live arXiv Data (Optional)

This mode replaces fixture data with real papers from the arXiv API. It requires network access.

```bash
python3 skill/trust_protocol.py --mode live
```

**Expected output**: Same protocol flow, but with real arXiv papers. The trust handshake and signing are identical — only the data source changes.

### Step 5: Verify Metrics

Run in quiet JSON mode and inspect the metrics:

```bash
python3 skill/trust_protocol.py --mode mock --quiet
```

**Key metrics to verify:**

| Metric | Expected Value | What It Proves |
|--------|---------------|----------------|
| `trust_established` | `true` | Mutual authentication succeeded |
| `round_trips` | `2` | Minimal protocol — one credential exchange each way |
| `overhead_ms` | `< 5.0` | Negligible crypto cost (Ed25519 is fast) |
| `audit_chain_valid` | `true` | Every VC in the pipeline has a valid signature chain |
| `pipeline_completed` | `true` | Full scientific task completed end-to-end |

For attack mode, additionally:

| Metric | Expected Value | What It Proves |
|--------|---------------|----------------|
| `attack_detected` | `true` | Impersonation is cryptographically impossible |

### Step 6: Inspect the Verifiable Credential Chain

The protocol produces 4 VCs in the audit chain:

1. **Agent A Capability VC** — "I am DataFetcherAgent, I can fetch_arxiv and parse_metadata" (signed by Agent A)
2. **Agent B Capability VC** — "I am AnalyzerAgent, I can analyze_papers and synthesize_report" (signed by Agent B)
3. **ArXiv Dataset VC** — The fetched papers, with content hash, signed by Agent A
4. **Analysis Report VC** — The synthesis, signed by Agent B

Each VC contains:
- `@context`: W3C Credentials context
- `issuer`: The agent's did:key
- `credentialSubject`: The payload (capabilities, data, analysis)
- `proof`: Ed25519 signature with verification method pointing to the issuer's DID

To inspect individual VCs, run with `--json` and parse the output.

## Protocol Specification

### Message Format

```
Round Trip 1: Agent A → Agent B
  Message: AgentCapabilityCredential (signed VC)
  Fields: agentName, agentType, capabilities, nonce
  Signature: Ed25519 via did:key

Round Trip 2: Agent B → Agent A
  Message: AgentCapabilityCredential (signed VC)
  Fields: agentName, agentType, capabilities, nonce
  Signature: Ed25519 via did:key

Data Exchange: Agent A → Agent B
  Message: ArXivDatasetCredential (signed VC)
  Fields: papers[], contentHash
  Verification: signature + issuer DID match

Analysis: Agent B → Audit
  Message: AnalysisReportCredential (signed VC)
  Fields: analysis results, contentHash
  Verification: signature + issuer DID match
```

### Security Properties

| Property | How Achieved |
|----------|-------------|
| **Authentication** | Each agent proves identity by signing with its did:key private key |
| **Integrity** | VC signatures cover the full credential payload (canonical JSON) |
| **Non-repudiation** | Signed VCs provide cryptographic proof of who produced what |
| **Impersonation resistance** | did:key binds DID to public key — forging requires the private key |
| **Replay resistance** | Each VC contains a unique nonce and timestamp |
| **No central authority** | did:key is self-resolving — no registry, no CA, no orchestrator |

### Threat Model

| Attack | Detected? | How |
|--------|-----------|-----|
| **Impersonation** (wrong keys, claimed DID) | Yes | Signature verification fails against DID's public key |
| **Tampering** (modify VC payload) | Yes | Signature becomes invalid |
| **Replay** (reuse old VC) | Partially | Nonce + timestamp enable detection; full replay protection requires state |
| **Compromised agent** (valid keys, bad data) | No | Out of scope — this protocol authenticates identity, not intent |

## Generalizability

This protocol is **not specific to arXiv or literature synthesis**. The trust handshake works for any multi-agent pipeline:

- **Drug discovery**: Agent A runs molecular simulations, Agent B analyzes results — both sign their outputs
- **Genomics**: Agent A processes sequencing data, Agent B performs variant calling — audit trail via VCs
- **Climate modeling**: Agents from different institutions collaborate on simulations without a shared orchestrator
- **Any AI4Science pipeline**: Replace the arXiv fetch with any data source; the trust layer is independent

The only requirements are: (1) each agent can generate an Ed25519 keypair, and (2) agents can exchange JSON messages.

## File Structure

```
skill/
├── SKILL.md                  # This file — executable skill instructions
├── trust_protocol.py         # Complete protocol implementation (single file)
└── fixtures/
    └── arxiv_papers.json     # Mock data for offline execution
```

## References

- [did:key Method Specification](https://w3c-ccg.github.io/did-method-key/)
- [W3C Verifiable Credentials Data Model](https://www.w3.org/TR/vc-data-model/)
- [DIDComm Messaging Specification v2](https://identity.foundation/didcomm-messaging/spec/)
- [OWASP Top 10 for LLM Applications 2025](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Ed25519: High-speed high-security signatures](https://ed25519.cr.yp.to/)
