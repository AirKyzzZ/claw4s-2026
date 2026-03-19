# Research Notes — Maxime Mansiet

## Key Attack Points
- Single point of failure: 1 compromised Grantor is enough
- Machine-speed: thousands of DIDs validated in seconds
- Proof-of-Trust obtained before detection
- Economic defense (slashing) = reactive, not preventive

## Simulation Idea
- Graph: N Grantors, M AI agents
- Scenario 1: 1 compromised Grantor → propagation
- Scenario 2: multi-endorsement (min 3 Grantors) → attack blocked
- Metrics: number of DIDs validated before detection, attack cost

## Open Questions
- What threshold for multi-endorsement? (3? 5?)
- Impact on legitimate validation latency?
- Compatibility with current VPR spec?

## References to Read
- [ ] https://verana-labs.github.io/verifiable-trust-vpr-spec/
- [ ] https://verana-labs.github.io/verifiable-trust-spec/
- [ ] Paper: gov-ai-agents-with-verifiable-trust-1.2.pdf (sent by Fabrice, Verana CTO)
