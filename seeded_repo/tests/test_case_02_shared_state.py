import pytest
from cache import UserSessionCache

def test_session_isolation_a():
    """
    Test Case 02: Shared / Leaked Test State (Part A)
    Sets up a session in the shared class store.
    """
    cache = UserSessionCache()
    cache.set_session("user_101", {"name": "Alice", "role": "admin"})
    assert cache.count() >= 1

def test_fresh_session_count_b():
    """
    Test Case 02: Shared / Leaked Test State (Part B)
    Taxonomy: shared_leaked_state
    Expects brand new cache instance to start empty (count == 0).
    Fails when run after test_session_isolation_a because _STORE is class-level.
    """
    cache = UserSessionCache()
    assert cache.count() == 0, (
        f"Leaked state detected! UserSessionCache should be empty for new test, but found {cache.count()} entries"
    )
