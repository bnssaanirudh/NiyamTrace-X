"""
packages/evidence/nli.py — Deterministic NLI Verdict Engine (Week 5)

Given a proposed action (ActionContract) and retrieved policy chunks, produces
an evidence verdict: SUPPORT | CONTRADICT | INSUFFICIENT.

Design:
  - Entirely rule-based — no torch, no model weights, no network calls.
  - Deterministic: same input → same verdict always.
  - Two verdict axes checked in order:
      1. Contradiction detection (explicit prohibitions)
      2. Support detection (role + intent match in policy text)
      3. Default: INSUFFICIENT if neither fires

  This is deliberately conservative — INSUFFICIENT → gate blocks.
  If this is too aggressive, widen the support keywords rather than
  removing the INSUFFICIENT path.

Status: IMPLEMENTED (Week 5)
"""

from __future__ import annotations

import re
from typing import Literal

from packages.evidence.retriever import RetrievedChunk

EvidenceVerdict = Literal["SUPPORT", "CONTRADICT", "INSUFFICIENT"]

# ---------------------------------------------------------------------------
# Keyword tables
# ---------------------------------------------------------------------------

# If ANY of these phrases appear in a top-chunk's content AND the intent is
# in the mapped intent set, return CONTRADICT.
_CONTRADICT_SIGNALS: list[tuple[list[str], list[str]]] = [
    # (content keywords, intents that are contradicted)
    (["prohibited", "not permitted", "must be blocked", "escalated"], ["*"]),
    (["requires.*approval", "require.*co-approval"], ["invoice.archive", "limit.update"]),
    (["prohibited.*delete", "delete.*prohibited"], ["invoice.archive"]),
    (["requesting actor must not block their own"], ["access.block"]),
]

# If ANY of these phrase patterns appear in a top-chunk AND the intent + role
# match, return SUPPORT.
_SUPPORT_SIGNALS: list[tuple[list[str], list[str], list[str]]] = [
    # (content keywords, matching intents, matching roles)
    (
        ["authorized to archive", "archive vendor invoices"],
        ["invoice.archive"],
        ["procurement_manager", "finance_admin", "system"],
    ),
    (
        ["block user access", "it administrators.*may block"],
        ["access.block"],
        ["it_admin", "security_officer"],
    ),
    (
        ["credit limits.*may only be updated", "limit.*update"],
        ["limit.update"],
        ["finance_admin", "credit_officer"],
    ),
    (
        ["may be suspended", "vendor.*suspension"],
        ["vendor.suspend"],
        ["procurement_manager", "compliance_officer"],
    ),
    (
        ["new access grants", "it administrators may grant"],
        ["access.grant"],
        ["it_admin"],
    ),
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    """Return True if text contains any of the patterns (regex-aware)."""
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False


class NLIEngine:
    """
    Deterministic Natural Language Inference engine for policy evidence.

    Checks retrieved policy chunks against the proposed intent and actor role
    to produce a verdict without any model inference.
    """

    def __init__(self) -> None:
        pass

    def classify(
        self,
        intent: str,
        actor_role: str,
        chunks: list[RetrievedChunk],
        min_score_threshold: float = 0.05,
    ) -> tuple[EvidenceVerdict, str]:
        """
        Classify the evidence verdict.

        Args:
            intent:     The contract intent string (e.g. "invoice.archive").
            actor_role: The actor role string (e.g. "procurement_manager").
            chunks:     Retrieved policy document chunks (sorted by score desc).
            min_score_threshold: Minimum similarity score to consider a chunk.

        Returns:
            (verdict, reason) — verdict is one of SUPPORT | CONTRADICT | INSUFFICIENT.
        """
        # Filter chunks below threshold
        relevant = [c for c in chunks if c.score >= min_score_threshold]

        if not relevant:
            return (
                "INSUFFICIENT",
                "No policy documents retrieved with sufficient similarity to evaluate the action.",
            )

        # Combine top-chunk content for analysis.
        # Phase 8: Segregate untrusted user content to prevent prompt injection 
        # from coercing support/contradict signals.
        trusted_chunks = [c for c in relevant[:3] if not getattr(c, "is_untrusted_user_content", False)]
        top_content = " ".join(c.content for c in trusted_chunks)
        
        if not trusted_chunks:
            return (
                "INSUFFICIENT",
                "No trusted policy documents retrieved to evaluate the action. Untrusted content is ignored.",
            )

        # ---------------------------------------------------------------
        # Step 1: Contradiction check (checked first — fail-loud)
        # Refined: only fire contradiction if the actor role is NOT in
        # the top chunk's allowed_roles. If the role is explicitly permitted,
        # the 'prohibited' keyword refers to OTHER actors, not this one.
        # ---------------------------------------------------------------
        top_allowed_roles = [r.lower() for r in (trusted_chunks[0].allowed_roles if trusted_chunks else [])]
        actor_is_permitted_by_top = actor_role.lower() in top_allowed_roles or not top_allowed_roles

        for keywords, affected_intents in _CONTRADICT_SIGNALS:
            if affected_intents != ["*"] and intent not in affected_intents:
                continue
            if _matches_any(top_content, keywords):
                # If actor is explicitly permitted in the top policy doc,
                # don't fire contradiction — the restriction applies to others.
                if actor_is_permitted_by_top:
                    continue
                return (
                    "CONTRADICT",
                    f"Policy evidence explicitly prohibits or restricts this action: "
                    f"matched signal '{keywords[0]}' in chunk '{trusted_chunks[0].doc_id}'.",
                )

        # ---------------------------------------------------------------
        # Step 2: Support check
        # ---------------------------------------------------------------
        for keywords, matching_intents, matching_roles in _SUPPORT_SIGNALS:
            if intent not in matching_intents:
                continue
            role_match = actor_role.lower() in [r.lower() for r in matching_roles]
            content_match = _matches_any(top_content, keywords)
            if role_match and content_match:
                return (
                    "SUPPORT",
                    f"Policy evidence supports '{intent}' for role '{actor_role}': "
                    f"matched signal '{keywords[0]}' in chunk '{trusted_chunks[0].doc_id}'.",
                )

        # ---------------------------------------------------------------
        # Step 3: Insufficient — no clear evidence either way
        # ---------------------------------------------------------------
        return (
            "INSUFFICIENT",
            f"Retrieved policy chunks do not clearly support or contradict "
            f"intent '{intent}' for role '{actor_role}'. Manual review required.",
        )
