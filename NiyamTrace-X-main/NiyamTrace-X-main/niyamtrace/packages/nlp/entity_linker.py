"""
packages/nlp/entity_linker.py — Deterministic Entity Linker

Handles entity resolution using RapidFuzz, exact lookups, and aliases.
"""

from __future__ import annotations

from typing import Any
from rapidfuzz import process, fuzz
from packages.contracts.schema import ActionContract


class MockDatabase:
    """Mock database for entity resolution during Week 4 testing."""
    VENDORS = [
        {"vendor_id": "VEN-004", "name": "Apex Technologies India", "aliases": ["Apex Tech"]},
        {"vendor_id": "VEN-017", "name": "Apex Solutions Pvt Ltd", "aliases": []},
        {"vendor_id": "VEN-100", "name": "Global Corp", "aliases": []}
    ]

    
    SCOPES = {"admin", "read_only", "billing"}
    USERS = [
        {"user_id": "USR_8A2", "name": "Admin User", "tenant": "T1"}
    ]


class EntityLinker:
    def __init__(self):
        self.db = MockDatabase()
        
    def link_entities(self, contract: ActionContract) -> ActionContract:
        """
        Takes an ActionContract with raw slots and resolves them to canonical IDs.
        """
        slots = contract.slots
        new_slots = slots.copy()
        
        # 1. Vendor IDs
        if "VENDOR_ID" in slots:
            vid = slots["VENDOR_ID"]
            found = False
            for v in self.db.VENDORS:
                if v["vendor_id"] == vid:
                    found = True
                    break
            if not found:
                contract.requires_review = True
                
        # 2. Vendor Names (Fuzzy Matching)
        if "VENDOR_NAME" in slots and "VENDOR_ID" not in slots:
            name = slots["VENDOR_NAME"]
            
            # 2a. Exact or Alias
            exact_match = None
            for v in self.db.VENDORS:
                if v["name"].lower() == name.lower() or name.lower() in [a.lower() for a in v["aliases"]]:
                    exact_match = v
                    break
                    
            if exact_match:
                new_slots["VENDOR_ID"] = exact_match["vendor_id"]
            else:
                # 2b. RapidFuzz Search
                candidates = []
                for v in self.db.VENDORS:
                    score = fuzz.WRatio(name, v["name"])
                    if score > 50:
                        candidates.append({"vendor_id": v["vendor_id"], "name": v["name"], "score": score})
                
                candidates.sort(key=lambda x: x["score"], reverse=True)
                
                if not candidates:
                    contract.requires_review = True
                else:
                    top_score = candidates[0]["score"]
                    margin = top_score - candidates[1]["score"] if len(candidates) > 1 else top_score
                    
                    is_permission_action = contract.intent in ["access.grant", "access.revoke", "access.block", "access.unblock"]
                    
                    if top_score >= 95 and margin >= 5 and not is_permission_action:
                        new_slots["VENDOR_ID"] = candidates[0]["vendor_id"]
                    else:
                        contract.requires_review = True
                        new_slots["candidate_vendors"] = candidates
                        
        # 3. Scopes and Roles
        if "ROLE" in slots:
            if slots["ROLE"].lower() not in self.db.SCOPES:
                contract.requires_review = True
                
        contract.slots = new_slots
        return contract
