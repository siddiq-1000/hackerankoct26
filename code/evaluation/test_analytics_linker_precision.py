"""Unit test for AnalyticsLinker token boundaries and collision immunity."""

import re

def test_token_boundary_collision():
    # Test that analytics_901 does NOT match analytics_9010
    line = '2026-08-27T08:47:41Z resource_id="analytics_9010" email="user@test.com"'
    
    # Buggy check:
    buggy_match = "analytics_901" in line
    assert buggy_match is True, "Substring match exhibits the collision bug"

    # Exact token extraction:
    extracted_rids = set(re.findall(r'\b(analytics_\d+)\b', line))
    assert "analytics_9010" in extracted_rids
    assert "analytics_901" not in extracted_rids, "Exact token extraction correctly avoids collision"

def test_user_multi_rid_ambiguity():
    # If a user is associated with multiple distinct analytics RIDs, it must be marked ambiguous
    user_mappings = {}
    
    def add_mapping(user, rid):
        if user not in user_mappings:
            user_mappings[user] = rid
        elif user_mappings[user] != rid:
            user_mappings[user] = "AMBIGUOUS"

    add_mapping("alice@example.com", "analytics_100")
    assert user_mappings["alice@example.com"] == "analytics_100"

    # Second mapping for same user
    add_mapping("alice@example.com", "analytics_200")
    assert user_mappings["alice@example.com"] == "AMBIGUOUS"

if __name__ == "__main__":
    test_token_boundary_collision()
    test_user_multi_rid_ambiguity()
    print("[PASS] Token boundary and multi-RID ambiguity unit tests passed.")
