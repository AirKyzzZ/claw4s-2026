# Research Notes — Maxime Mansiet

## Core Insight
The "TP interactif" is the key innovation of this submission. The agent running the SKILL.md doesn't just observe — it *participates* in the trust establishment. This is a new way to use the skill format.

## Protocol Design (Draft)

### Step 1: DID Generation
Each agent generates a did:key (Ed25519) at initialization.
No registry, no external lookup. Self-sovereign.

### Step 2: Capability Presentation
AgentA sends a "Capability Credential" VC:
- type: DataFetcherAgent
- capabilities: [fetch_arxiv, parse_pdf]
- signed with did:key:z6MkAgentA

### Step 3: Verification
AgentB verifies:
- Signature valid? (Ed25519 verify)
- DID resolves to key in credential? (did:key is self-resolving)
- Capabilities match what's needed? (schema check)

### Step 4: Mutual Authentication
AgentB responds with its own VC.
AgentA verifies AgentB.
→ Secure channel established. No central authority consulted.

### Step 5: Collaborative Task
AgentA fetches arXiv papers, signs the dataset VC.
AgentB receives, verifies signature, analyzes.
AgentB signs its analysis VC.
AuditLog verifies full chain.

## Why did:key specifically
- Self-resolving (no DID registry needed → offline mock works)
- Ed25519: fast, standard, 0.3ms sign / 0.5ms verify
- Supported by cryptography Python package (no heavy deps)

## Open Questions
- What's in the minimal VC payload? (type, capabilities, timestamp, nonce)
- How to handle key rotation in future work?
- What defines "trust established" vs just "signature valid"?

## Metrics to Report
- round_trips: how many messages to establish trust (target: 2)
- overhead_ms: total crypto overhead (target: <5ms)
- attack_detection_rate: 100% for wrong DID
- protocol_completeness: does it cover impersonation, replay, tampering?

## What We Explicitly Don't Claim
- Not claiming this is "better" than centralized orchestration for all uses
- Not claiming it solves the compromised-agent-signing-bad-data problem
- Not claiming production-ready key management

## References to Read
- [ ] DIDComm Messaging spec v2: https://identity.foundation/didcomm-messaging/spec/
- [ ] did:key draft: https://w3c-ccg.github.io/did-key-draft/
- [ ] OWASP LLM Top 10 2025 (provenance gaps)
- [ ] Verana VPR spec (for related work section)
