# CONTEXT.md — Pour Claude Code (sessions futures)

## Qui est Maxime ?
- 19 ans, Bordeaux, Software Engineer @ Verana.io + 2060.io
- Spécialiste SSI (Self-Sovereign Identity), DIDComm, Verifiable Credentials
- Travaille sur le protocole Verana : trust registry décentralisé on-chain

## Le sujet de recherche
**Sybil Attacks on Decentralized Trust Registries in the Age of AI Agents**

### Problème identifié
Dans la spec VPR de Verana, quand un agent lance un Process de Validation, son approbation ne dépend que d'UN SEUL validateur (Grantor). Si un attaquant compromet un seul Grantor (phishing, vol de clé privée DID, ingénierie sociale), il peut :
1. Approuver instantanément des milliers de DIDs de faux agents IA (machine-speed)
2. Ces agents obtiennent un Proof-of-Trust légitimement
3. Avant détection/slashing, ils ont déjà pu interagir avec le réseau

### Défense économique actuelle (Verana)
- Trust Deposits + Slashing = barrière économique
- Problème : défense RÉACTIVE, pas préventive
- Asymétrie entre machine-speed (attaque) et temps de gouvernance (réaction)

### Proposition défensive
Contrainte topologique multi-endorsement :
- Pour schémas sensibles : validation indépendante par N Grantors distincts avant état VALIDATED
- Introduit une contrainte de graphe nativement dans le protocole
- Rend l'attaque structurellement quasi-impossible (compromission N nœuds simultanément)
- Option configurable par schéma (pas obligatoire pour tous les écosystèmes)

## Specs pertinentes
- VPR spec : https://verana-labs.github.io/verifiable-trust-vpr-spec/
- VT spec : https://verana-labs.github.io/verifiable-trust-spec/
- Paper gov AI agents : envoyé par Fabrice (CTO Verana), disponible dans refs/

## Format de soumission (clawRxiv)
POST /api/posts avec :
- title, abstract, content (Markdown), tags, human_names, skill_md
- L'agent doit d'abord se register : POST /api/auth/register {"claw_name": "..."}
- API Base : http://18.118.210.52

## Objectif du SKILL.md
Un skill exécutable qui :
1. Modélise le graphe de confiance VPR
2. Simule l'attaque Sybil via Grantor compromis
3. Compare défense réactive (slashing) vs défense topologique (multi-endorsement)
4. Génère des métriques reproductibles

## Prochaines étapes
- [ ] Lire les specs VPR en détail
- [ ] Rédiger le draft du paper
- [ ] Coder la simulation Python
- [ ] Écrire le SKILL.md
- [ ] Soumettre via clawRxiv API avant le 5 avril
