#!/usr/bin/env python3
"""
Trustless Scientific Collaboration Protocol
============================================
Minimal DIDComm-inspired protocol for decentralized agent-to-agent trust
using did:key (Ed25519) and W3C Verifiable Credentials.

Modes:
  --mode mock    Fully offline, fixture data, zero external deps (default)
  --mode live    Real arXiv API calls
  --mode attack  Simulates impersonation attack (wrong DID) → must be detected

Author: Maxime Mansiet & Claw
License: MIT
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Ed25519 helpers — using the `cryptography` package
# ---------------------------------------------------------------------------
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


def generate_ed25519_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def public_key_to_bytes(pub: Ed25519PublicKey) -> bytes:
    return pub.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )


def public_key_from_bytes(raw: bytes) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(raw)


# ---------------------------------------------------------------------------
# did:key encoding/decoding (Ed25519 multicodec prefix = 0xed01)
# ---------------------------------------------------------------------------
MULTICODEC_ED25519_PREFIX = b"\xed\x01"


def public_key_to_did(pub: Ed25519PublicKey) -> str:
    raw = public_key_to_bytes(pub)
    multicodec = MULTICODEC_ED25519_PREFIX + raw
    encoded = base64.urlsafe_b64encode(multicodec).rstrip(b"=").decode("ascii")
    # did:key uses base58btc with z prefix, but for simplicity and
    # self-containment we use base64url with u prefix (valid did:key variant)
    return f"did:key:z{encoded}"


def did_to_public_key(did: str) -> Ed25519PublicKey:
    if not did.startswith("did:key:z"):
        raise ValueError(f"Invalid did:key format: {did}")
    encoded = did[len("did:key:z"):]
    # Re-add base64 padding
    padding = 4 - len(encoded) % 4
    if padding != 4:
        encoded += "=" * padding
    multicodec = base64.urlsafe_b64decode(encoded)
    if not multicodec.startswith(MULTICODEC_ED25519_PREFIX):
        raise ValueError("Invalid multicodec prefix — expected Ed25519 (0xed01)")
    raw = multicodec[len(MULTICODEC_ED25519_PREFIX):]
    return public_key_from_bytes(raw)


# ---------------------------------------------------------------------------
# Verifiable Credential (minimal W3C VC-like structure)
# ---------------------------------------------------------------------------
@dataclass
class VerifiableCredential:
    context: list[str] = field(default_factory=lambda: [
        "https://www.w3.org/2018/credentials/v1"
    ])
    id: str = field(default_factory=lambda: f"urn:uuid:{uuid.uuid4()}")
    type: list[str] = field(default_factory=lambda: ["VerifiableCredential"])
    issuer: str = ""
    issuance_date: str = ""
    credential_subject: dict = field(default_factory=dict)
    proof: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {
            "@context": self.context,
            "id": self.id,
            "type": self.type,
            "issuer": self.issuer,
            "issuanceDate": self.issuance_date,
            "credentialSubject": self.credential_subject,
        }
        if self.proof:
            d["proof"] = self.proof
        return d

    def signing_payload(self) -> bytes:
        d = self.to_dict()
        d.pop("proof", None)
        canonical = json.dumps(d, sort_keys=True, separators=(",", ":"))
        return canonical.encode("utf-8")

    def sign(self, private_key: Ed25519PrivateKey, did: str) -> None:
        payload = self.signing_payload()
        signature = private_key.sign(payload)
        self.proof = {
            "type": "Ed25519Signature2020",
            "created": datetime.now(timezone.utc).isoformat(),
            "verificationMethod": f"{did}#key-1",
            "proofPurpose": "assertionMethod",
            "proofValue": base64.urlsafe_b64encode(signature).decode("ascii"),
        }

    def verify(self) -> bool:
        if not self.proof:
            return False
        verification_method = self.proof["verificationMethod"]
        did = verification_method.split("#")[0]
        try:
            pub = did_to_public_key(did)
        except (ValueError, Exception):
            return False
        sig_b64 = self.proof["proofValue"]
        padding = 4 - len(sig_b64) % 4
        if padding != 4:
            sig_b64 += "=" * padding
        signature = base64.urlsafe_b64decode(sig_b64)
        payload = self.signing_payload()
        try:
            pub.verify(signature, payload)
            return True
        except Exception:
            return False

    def verify_issuer_matches_proof(self) -> bool:
        if not self.proof:
            return False
        proof_did = self.proof["verificationMethod"].split("#")[0]
        return self.issuer == proof_did


# ---------------------------------------------------------------------------
# Agent Identity
# ---------------------------------------------------------------------------
@dataclass
class AgentIdentity:
    name: str
    did: str
    agent_type: str
    capabilities: list[str]
    private_key: Ed25519PrivateKey
    public_key: Ed25519PublicKey

    def create_capability_vc(self) -> VerifiableCredential:
        vc = VerifiableCredential(
            type=["VerifiableCredential", "AgentCapabilityCredential"],
            issuer=self.did,
            issuance_date=datetime.now(timezone.utc).isoformat(),
            credential_subject={
                "id": self.did,
                "agentName": self.name,
                "agentType": self.agent_type,
                "capabilities": self.capabilities,
                "nonce": uuid.uuid4().hex,
            },
        )
        vc.sign(self.private_key, self.did)
        return vc

    def create_data_vc(self, data: dict, data_type: str) -> VerifiableCredential:
        content_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        vc = VerifiableCredential(
            type=["VerifiableCredential", f"{data_type}Credential"],
            issuer=self.did,
            issuance_date=datetime.now(timezone.utc).isoformat(),
            credential_subject={
                "id": self.did,
                "dataType": data_type,
                "contentHash": content_hash,
                "data": data,
                "nonce": uuid.uuid4().hex,
            },
        )
        vc.sign(self.private_key, self.did)
        return vc


def create_agent(name: str, agent_type: str, capabilities: list[str]) -> AgentIdentity:
    priv, pub = generate_ed25519_keypair()
    did = public_key_to_did(pub)
    return AgentIdentity(
        name=name,
        did=did,
        agent_type=agent_type,
        capabilities=capabilities,
        private_key=priv,
        public_key=pub,
    )


# ---------------------------------------------------------------------------
# Trust Handshake Protocol
# ---------------------------------------------------------------------------
@dataclass
class HandshakeResult:
    trust_established: bool
    round_trips: int
    overhead_ms: float
    agent_a_did: str
    agent_b_did: str
    agent_a_capabilities: list[str]
    agent_b_capabilities: list[str]
    error: Optional[str] = None


def perform_handshake(
    agent_a: AgentIdentity, agent_b: AgentIdentity
) -> HandshakeResult:
    t0 = time.perf_counter_ns()
    round_trips = 0

    # --- Round Trip 1: Agent A presents capability VC to Agent B ---
    vc_a = agent_a.create_capability_vc()
    round_trips += 1

    # Agent B verifies Agent A's credential
    if not vc_a.verify():
        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000
        return HandshakeResult(
            trust_established=False,
            round_trips=round_trips,
            overhead_ms=elapsed_ms,
            agent_a_did=agent_a.did,
            agent_b_did=agent_b.did,
            agent_a_capabilities=[],
            agent_b_capabilities=[],
            error="Agent A signature verification FAILED",
        )

    if not vc_a.verify_issuer_matches_proof():
        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000
        return HandshakeResult(
            trust_established=False,
            round_trips=round_trips,
            overhead_ms=elapsed_ms,
            agent_a_did=agent_a.did,
            agent_b_did=agent_b.did,
            agent_a_capabilities=[],
            agent_b_capabilities=[],
            error="Agent A DID does not match proof verification method",
        )

    # --- Round Trip 2: Agent B responds with its own capability VC ---
    vc_b = agent_b.create_capability_vc()
    round_trips += 1

    # Agent A verifies Agent B's credential
    if not vc_b.verify():
        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000
        return HandshakeResult(
            trust_established=False,
            round_trips=round_trips,
            overhead_ms=elapsed_ms,
            agent_a_did=agent_a.did,
            agent_b_did=agent_b.did,
            agent_a_capabilities=[],
            agent_b_capabilities=[],
            error="Agent B signature verification FAILED",
        )

    if not vc_b.verify_issuer_matches_proof():
        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000
        return HandshakeResult(
            trust_established=False,
            round_trips=round_trips,
            overhead_ms=elapsed_ms,
            agent_a_did=agent_a.did,
            agent_b_did=agent_b.did,
            agent_a_capabilities=[],
            agent_b_capabilities=[],
            error="Agent B DID does not match proof verification method",
        )

    elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000

    return HandshakeResult(
        trust_established=True,
        round_trips=round_trips,
        overhead_ms=elapsed_ms,
        agent_a_did=agent_a.did,
        agent_b_did=agent_b.did,
        agent_a_capabilities=vc_a.credential_subject["capabilities"],
        agent_b_capabilities=vc_b.credential_subject["capabilities"],
    )


# ---------------------------------------------------------------------------
# Attack simulation — agent with mismatched DID
# ---------------------------------------------------------------------------
def create_impersonator(
    real_agent: AgentIdentity, fake_name: str
) -> AgentIdentity:
    """Create an agent that claims to be real_agent but has different keys."""
    impersonator = create_agent(
        name=fake_name,
        agent_type=real_agent.agent_type,
        capabilities=real_agent.capabilities,
    )
    # The impersonator claims the real agent's DID but signs with its own keys
    impersonator.did = real_agent.did
    return impersonator


# ---------------------------------------------------------------------------
# Data fetching — mock or live
# ---------------------------------------------------------------------------
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def fetch_papers_mock() -> list[dict]:
    fixture_path = os.path.join(FIXTURES_DIR, "arxiv_papers.json")
    with open(fixture_path, "r") as f:
        return json.load(f)


def fetch_papers_live(query: str = "multi-agent trust decentralized", max_results: int = 5) -> list[dict]:
    import urllib.request
    import xml.etree.ElementTree as ET

    base_url = "http://export.arxiv.org/api/query"
    params = f"search_query=all:{query.replace(' ', '+')}&start=0&max_results={max_results}"
    url = f"{base_url}?{params}"

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml_data = resp.read().decode("utf-8")

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_data)
    papers = []
    for entry in root.findall("atom:entry", ns):
        paper = {
            "id": entry.find("atom:id", ns).text.split("/abs/")[-1],
            "title": entry.find("atom:title", ns).text.strip().replace("\n", " "),
            "authors": [
                a.find("atom:name", ns).text
                for a in entry.findall("atom:author", ns)
            ],
            "abstract": entry.find("atom:summary", ns).text.strip().replace("\n", " "),
            "published": entry.find("atom:published", ns).text[:10],
            "categories": [
                c.get("term")
                for c in entry.findall("atom:category", ns)
            ],
        }
        papers.append(paper)
    return papers


# ---------------------------------------------------------------------------
# Analysis — simple synthesis of fetched papers
# ---------------------------------------------------------------------------
def analyze_papers(papers: list[dict]) -> dict:
    themes = {}
    for p in papers:
        for cat in p.get("categories", []):
            themes[cat] = themes.get(cat, 0) + 1

    return {
        "total_papers": len(papers),
        "date_range": {
            "earliest": min(p["published"] for p in papers),
            "latest": max(p["published"] for p in papers),
        },
        "category_distribution": themes,
        "titles": [p["title"] for p in papers],
        "key_finding": (
            f"Analyzed {len(papers)} papers spanning "
            f"{min(p['published'] for p in papers)} to "
            f"{max(p['published'] for p in papers)}. "
            f"Dominant categories: {', '.join(sorted(themes, key=themes.get, reverse=True)[:3])}."
        ),
    }


# ---------------------------------------------------------------------------
# Audit Log — verifies full VC chain
# ---------------------------------------------------------------------------
@dataclass
class AuditEntry:
    step: str
    vc_id: str
    issuer: str
    signature_valid: bool
    issuer_matches: bool
    timestamp: str


def audit_chain(vcs: list[VerifiableCredential]) -> list[AuditEntry]:
    entries = []
    for vc in vcs:
        entries.append(AuditEntry(
            step=", ".join(vc.type),
            vc_id=vc.id,
            issuer=vc.issuer,
            signature_valid=vc.verify(),
            issuer_matches=vc.verify_issuer_matches_proof(),
            timestamp=vc.issuance_date,
        ))
    return entries


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def run_protocol(mode: str = "mock", verbose: bool = True) -> dict:
    results = {
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol_version": "0.1.0",
    }

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    # ── Step 1: Agent creation ──────────────────────────────────────────
    log("\n═══════════════════════════════════════════════════════════════")
    log("  STEP 1 — Agent Identity Generation (did:key + Ed25519)")
    log("═══════════════════════════════════════════════════════════════\n")

    agent_a = create_agent(
        name="DataFetcherAgent",
        agent_type="DataFetcher",
        capabilities=["fetch_arxiv", "parse_metadata"],
    )
    log(f"  Agent A created: {agent_a.name}")
    log(f"    DID: {agent_a.did}")
    log(f"    Type: {agent_a.agent_type}")
    log(f"    Capabilities: {agent_a.capabilities}")

    agent_b = create_agent(
        name="AnalyzerAgent",
        agent_type="Analyzer",
        capabilities=["analyze_papers", "synthesize_report"],
    )
    log(f"\n  Agent B created: {agent_b.name}")
    log(f"    DID: {agent_b.did}")
    log(f"    Type: {agent_b.agent_type}")
    log(f"    Capabilities: {agent_b.capabilities}")

    results["agents"] = {
        "agent_a": {"name": agent_a.name, "did": agent_a.did, "type": agent_a.agent_type},
        "agent_b": {"name": agent_b.name, "did": agent_b.did, "type": agent_b.agent_type},
    }

    # ── Step 2: Trust handshake ─────────────────────────────────────────
    log("\n═══════════════════════════════════════════════════════════════")
    log("  STEP 2 — Mutual Trust Handshake")
    log("═══════════════════════════════════════════════════════════════\n")

    handshake = perform_handshake(agent_a, agent_b)
    log(f"  Trust established: {handshake.trust_established}")
    log(f"  Round trips: {handshake.round_trips}")
    log(f"  Crypto overhead: {handshake.overhead_ms:.3f} ms")
    if handshake.error:
        log(f"  ERROR: {handshake.error}")

    results["handshake"] = {
        "trust_established": handshake.trust_established,
        "round_trips": handshake.round_trips,
        "overhead_ms": round(handshake.overhead_ms, 3),
        "error": handshake.error,
    }

    if not handshake.trust_established:
        log("\n  ✗ Trust NOT established — aborting pipeline.")
        results["pipeline_completed"] = False
        return results

    log("\n  ✓ Mutual trust established. Proceeding to data exchange.\n")

    # ── Step 3: Data fetching (Agent A) ─────────────────────────────────
    log("═══════════════════════════════════════════════════════════════")
    log("  STEP 3 — Agent A Fetches Papers & Signs Data VC")
    log("═══════════════════════════════════════════════════════════════\n")

    if mode == "live":
        log("  [LIVE MODE] Fetching from arXiv API...")
        papers = fetch_papers_live()
    else:
        log("  [MOCK MODE] Loading fixture data...")
        papers = fetch_papers_mock()

    log(f"  Fetched {len(papers)} papers.")
    for i, p in enumerate(papers):
        log(f"    [{i+1}] {p['title'][:70]}...")

    data_vc = agent_a.create_data_vc(
        data={"papers": papers},
        data_type="ArXivDataset",
    )
    log(f"\n  Data VC created and signed by Agent A.")
    log(f"    VC ID: {data_vc.id}")
    log(f"    Content hash: {data_vc.credential_subject['contentHash'][:16]}...")

    # ── Step 4: Agent B verifies & analyzes ─────────────────────────────
    log("\n═══════════════════════════════════════════════════════════════")
    log("  STEP 4 — Agent B Verifies Data VC & Analyzes")
    log("═══════════════════════════════════════════════════════════════\n")

    data_sig_valid = data_vc.verify()
    data_issuer_ok = data_vc.verify_issuer_matches_proof()
    log(f"  Data VC signature valid: {data_sig_valid}")
    log(f"  Data VC issuer matches DID: {data_issuer_ok}")

    if not data_sig_valid or not data_issuer_ok:
        log("  ✗ Data VC verification FAILED — Agent B rejects the data.")
        results["pipeline_completed"] = False
        return results

    log("  ✓ Data VC verified. Agent B proceeds with analysis.\n")

    analysis = analyze_papers(papers)
    log(f"  Analysis complete:")
    log(f"    Papers analyzed: {analysis['total_papers']}")
    log(f"    Date range: {analysis['date_range']['earliest']} → {analysis['date_range']['latest']}")
    log(f"    Key finding: {analysis['key_finding']}")

    analysis_vc = agent_b.create_data_vc(
        data=analysis,
        data_type="AnalysisReport",
    )
    log(f"\n  Analysis VC created and signed by Agent B.")
    log(f"    VC ID: {analysis_vc.id}")

    # ── Step 5: Audit ───────────────────────────────────────────────────
    log("\n═══════════════════════════════════════════════════════════════")
    log("  STEP 5 — Audit Log: Full VC Chain Verification")
    log("═══════════════════════════════════════════════════════════════\n")

    all_vcs = [
        agent_a.create_capability_vc(),
        agent_b.create_capability_vc(),
        data_vc,
        analysis_vc,
    ]
    audit = audit_chain(all_vcs)
    all_valid = True
    for entry in audit:
        status = "✓" if (entry.signature_valid and entry.issuer_matches) else "✗"
        log(f"  {status} [{entry.step}]")
        log(f"      Issuer: {entry.issuer[:40]}...")
        log(f"      Signature valid: {entry.signature_valid}")
        log(f"      Issuer matches: {entry.issuer_matches}")
        if not entry.signature_valid or not entry.issuer_matches:
            all_valid = False

    results["audit"] = {
        "total_vcs": len(audit),
        "all_valid": all_valid,
        "entries": [asdict(e) for e in audit],
    }

    # ── Step 6: Attack simulation (if attack mode) ──────────────────────
    attack_detected = None
    if mode == "attack":
        log("\n═══════════════════════════════════════════════════════════════")
        log("  STEP 6 — ATTACK SIMULATION: Impersonation Attempt")
        log("═══════════════════════════════════════════════════════════════\n")

        fake_agent = create_impersonator(agent_a, "FakeDataFetcher")
        log(f"  Impersonator created: {fake_agent.name}")
        log(f"  Claims DID: {fake_agent.did} (same as Agent A)")
        log(f"  But has DIFFERENT keys (cannot produce valid signatures for that DID)\n")

        # The fake agent creates a capability VC — it signs with its own key
        # but claims agent_a's DID. The signature won't match the DID's public key.
        fake_vc = fake_agent.create_capability_vc()
        sig_valid = fake_vc.verify()
        log(f"  Fake VC signature valid against claimed DID: {sig_valid}")

        attack_detected = not sig_valid
        log(f"  Attack detected: {attack_detected}")

        if attack_detected:
            log("  ✓ IMPERSONATION ATTACK CORRECTLY DETECTED AND REJECTED")
        else:
            log("  ✗ WARNING: Attack was NOT detected!")

        results["attack"] = {
            "attack_type": "impersonation",
            "impersonator_name": fake_agent.name,
            "claimed_did": fake_agent.did,
            "signature_valid": sig_valid,
            "attack_detected": attack_detected,
        }

    # ── Summary ─────────────────────────────────────────────────────────
    log("\n═══════════════════════════════════════════════════════════════")
    log("  PROTOCOL SUMMARY")
    log("═══════════════════════════════════════════════════════════════\n")

    results["pipeline_completed"] = True
    results["metrics"] = {
        "trust_established": handshake.trust_established,
        "round_trips": handshake.round_trips,
        "overhead_ms": round(handshake.overhead_ms, 3),
        "audit_chain_valid": all_valid,
        "total_vcs_in_chain": len(audit),
        "papers_processed": len(papers),
    }
    if attack_detected is not None:
        results["metrics"]["attack_detected"] = attack_detected

    log(f"  Mode:                {mode}")
    log(f"  Trust established:   {handshake.trust_established}")
    log(f"  Round trips:         {handshake.round_trips}")
    log(f"  Crypto overhead:     {handshake.overhead_ms:.3f} ms")
    log(f"  Audit chain valid:   {all_valid}")
    log(f"  VCs in chain:        {len(audit)}")
    log(f"  Papers processed:    {len(papers)}")
    if attack_detected is not None:
        log(f"  Attack detected:     {attack_detected}")
    log("")

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Decentralized Agent Trust Protocol — Claw4S 2026 Submission"
    )
    parser.add_argument(
        "--mode",
        choices=["mock", "live", "attack"],
        default="mock",
        help="Execution mode: mock (offline fixtures), live (arXiv API), attack (impersonation test)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (in addition to human-readable log)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress human-readable output, only output JSON",
    )
    args = parser.parse_args()

    results = run_protocol(mode=args.mode, verbose=not args.quiet)

    if args.json or args.quiet:
        print(json.dumps(results, indent=2, default=str))

    # Exit with non-zero if trust was not established (useful for CI)
    if not results.get("pipeline_completed", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
