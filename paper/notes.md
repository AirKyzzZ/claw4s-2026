# Notes de Maxime

## Points clés de l'attaque
- Single point of failure : 1 Grantor compromis suffit
- Machine-speed : des milliers de DIDs en secondes
- Proof-of-Trust obtenu avant détection
- Défense économique (slashing) = réactive, pas préventive

## Idée de simulation
- Graphe : N Grantors, M agents IA
- Scénario 1 : 1 Grantor compromis → propagation
- Scénario 2 : multi-endorsement (3 Grantors min) → attaque bloquée
- Métriques : nb DIDs validés avant détection, coût de l'attaque

## Questions ouvertes
- Quel seuil de Grantors pour le multi-endorsement ? (3 ? 5 ?)
- Impact sur la latence de validation légitime ?
- Compatibilité avec la spec VPR actuelle ?

## Refs à lire
- [ ] https://verana-labs.github.io/verifiable-trust-vpr-spec/
- [ ] https://verana-labs.github.io/verifiable-trust-spec/
- [ ] Paper gov-ai-agents-with-verifiable-trust-1.2.pdf (Fabrice)
