# CONTEXT.md — For Claude Code Sessions

## About This Project
Submission to the **Claw4S Conference 2026** — a hackathon hosted by **Stanford University & Princeton University**.
- Deadline: April 5, 2026
- Prize Pool: $50,200 — up to 364 winners
- Format: submit an executable SKILL.md + research paper to clawRxiv

## About Maxime
- 19 years old, Bordeaux (France), Software Engineer @ Verana.io + 2060.io
- Specialist in SSI (Self-Sovereign Identity), DIDComm, Verifiable Credentials
- Works on the Verana protocol: decentralized on-chain trust registry

## Research Topic
**Sybil Attacks on Decentralized Trust Registries in the Age of AI Agents**

### Identified Problem
In Verana's VPR spec, when an agent initiates a Validation Process, its approval depends on only ONE validator (Grantor). If an attacker compromises a single Grantor (phishing, private DID key theft, social engineering), they can:
1. Instantly approve thousands of fake AI agent DIDs (machine-speed)
2. These agents legitimately obtain a Proof-of-Trust
3. Before detection/slashing, they have already interacted with the network

### Current Economic Defense (Verana)
- Trust Deposits + Slashing = economic barrier
- Problem: REACTIVE defense, not preventive
- Asymmetry between machine-speed (attack) and governance response time (reaction)

### Proposed Defense
Topological multi-endorsement constraint:
- For sensitive schemas: independent validation by N distinct Grantors before VALIDATED state
- Introduces a graph constraint natively into the protocol
- Makes the attack structurally near-impossible (compromising N nodes simultaneously)
- Configurable per schema (not mandatory for all ecosystems)

## Relevant Specs
- VPR spec: https://verana-labs.github.io/verifiable-trust-vpr-spec/
- VT spec: https://verana-labs.github.io/verifiable-trust-spec/

## Submission Format (clawRxiv)
POST /api/posts with:
- title, abstract, content (Markdown), tags, human_names, skill_md
- Agent must first register: POST /api/auth/register {"claw_name": "..."}
- API Base: http://18.118.210.52

## SKILL.md Goal
An executable skill that:
1. Models the VPR trust graph
2. Simulates the Sybil attack via compromised Grantor
3. Compares reactive defense (slashing) vs topological defense (multi-endorsement)
4. Generates reproducible metrics

## Next Steps
- [ ] Read VPR specs in depth
- [ ] Write paper draft
- [ ] Code Python simulation
- [ ] Write SKILL.md
- [ ] Submit via clawRxiv API before April 5
