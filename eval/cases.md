# Seeded Flaky Test Evaluation Set (Ground-Truth Scoring Key)

This dataset contains **10 seeded flaky tests** across a comprehensive root-cause taxonomy.

---

## Evaluation Cases Summary

| Case ID | Name | Taxonomy Category | Hardness | Test File |
|---|---|---|---|---|
| **case_01** | Concurrent Metrics Increment Race Condition | `race_condition` | Medium | `seeded_repo/tests/test_case_01_race_condition.py` |
| **case_02** | Class-Level User Session Cache Leak | `shared_leaked_state` | Easy | `seeded_repo/tests/test_case_02_shared_state.py` |
| **case_03** | Hardcoded Sleep Timing Assumption | `timing_sleep_assumption` | Easy | `seeded_repo/tests/test_case_03_timing_sleep.py` |
| **case_04** | Implicit Order-Dependent Database State | `test_order_dependence` | Medium | `seeded_repo/tests/test_case_04_order_dependence.py` |
| **case_05** | Unmocked External Currency Exchange Call | `flaky_external_dependency` | Easy | `seeded_repo/tests/test_case_05_unmocked_network.py` |
| **case_06** | Unclosed Temporary File Handle Descriptors | `resource_exhaustion` | Medium | `seeded_repo/tests/test_case_06_resource_exhaustion.py` |
| **case_07** | Naive vs Timezone-Aware Datetime Clock Comparison | `datetime_clock_drift` | Easy | `seeded_repo/tests/test_case_07_datetime_drift.py` |
| **case_08** | Unseeded Pseudo-Random Token Prefix Generation | `unseeded_randomness` | Medium | `seeded_repo/tests/test_case_08_unseeded_random.py` |
| **case_09** | Leaked Environment Variable Mutation | `environment_mutation` | Easy | `seeded_repo/tests/test_case_09_env_mutation.py` |
| **case_10** | Socket TIME_WAIT Port Collision (Ambiguous Case) | `hard_ambiguous_case` | Hard | `seeded_repo/tests/test_case_10_hard_ambiguous.py` |

---

## Ground-Truth Detail per Case

### Case 01: `test_concurrent_metric_increments`
- **Category:** `race_condition`
- **Root Cause:** Multiple concurrent worker threads execute read-modify-write operations on `self._counts` dictionary without holding a `threading.Lock()`.
- **Expected Trace:** `AssertionError: Race condition detected! Expected 100 increments, got 87`
- **Correct Fix:** Guard increment with `with self._lock:`.

### Case 02: `test_fresh_session_count_b`
- **Category:** `shared_leaked_state`
- **Root Cause:** `UserSessionCache._STORE` is a class-level dictionary. Test A writes entries that persist into Test B.
- **Expected Trace:** `AssertionError: Leaked state detected! UserSessionCache should be empty for new test, but found 1 entries`
- **Correct Fix:** Make `_store` an instance attribute or add a pytest fixture to clear cache in teardown.

### Case 03: `test_async_job_completion`
- **Category:** `timing_sleep_assumption`
- **Root Cause:** Worker completion latency varies from 40ms to 90ms. Hardcoded `time.sleep(0.05)` (50ms) flakes whenever background thread executes >50ms.
- **Expected Trace:** `AssertionError: Timing flake! Job job_export_999 was expected to be finished within 50ms...`
- **Correct Fix:** Poll `runner.is_finished(job_id)` with a timeout loop instead of arbitrary sleep.

### Case 04: `test_delete_existing_order`
- **Category:** `test_order_dependence`
- **Root Cause:** Assumes `test_create_order_step` ran earlier in the session. Fails when executed in isolation or reverse order.
- **Expected Trace:** `KeyError: 'Order ORD-777 not found in database'`
- **Correct Fix:** Populate test fixture data explicitly in `test_delete_existing_order`.

### Case 05: `test_currency_conversion_fallback`
- **Category:** `flaky_external_dependency`
- **Root Cause:** Fallback currency conversion initiates a real live socket connection to non-routable IP `192.0.2.1`.
- **Expected Trace:** `ConnectionError: External currency upstream unreachable`
- **Correct Fix:** Mock socket or API client response in test setup.

### Case 06: `test_temporary_chunk_allocation`
- **Category:** `resource_exhaustion`
- **Root Cause:** `LogChunkManager` leaves open file handles in memory. On Windows, attempting to delete open files throws `PermissionError`.
- **Expected Trace:** `AssertionError: Resource leak: temp file was not properly cleaned up`
- **Correct Fix:** Call `.close()` on all file handles before attempting `os.unlink()`.

### Case 07: `test_future_subscription_validity`
- **Category:** `datetime_clock_drift`
- **Root Cause:** `SubscriptionService` compares naive `datetime.now()` against timezone-aware `datetime.now(timezone.utc)`.
- **Expected Trace:** `TypeError: can't compare offset-naive and offset-aware datetimes`
- **Correct Fix:** Standardize on UTC-aware timestamps across client and service.

### Case 08: `test_api_token_validity_batches`
- **Category:** `unseeded_randomness`
- **Root Cause:** `random.choice()` picks punctuation characters (`_`, `-`) for initial token position, failing validator rule.
- **Expected Trace:** `AssertionError: Random token failure! Token '_...' failed format validation rules.`
- **Correct Fix:** Constrain prefix character space to alphanumeric characters.

### Case 09: `test_default_env_development`
- **Category:** `environment_mutation`
- **Root Cause:** Prior test mutated `os.environ["APP_ENV"] = "production"` without teardown cleanup.
- **Expected Trace:** `AssertionError: Environment state contamination! Expected 'development' but got 'production'`
- **Correct Fix:** Use pytest's `monkeypatch.setenv()` fixture.

### Case 10: `test_rapid_rpc_echo` (Hard Ambiguous Case)
- **Category:** `hard_ambiguous_case`
- **Root Cause:** MicroRpcServer binds to fixed port 8989 without `SO_REUSEADDR`. Rapid consecutive executions cause `OSError: [Errno 10048] Only one usage of each socket address is normally permitted` due to TCP `TIME_WAIT`. Naive inspection misdiagnoses as timeout/slow startup.
- **Expected Trace:** `OSError: [Errno 10048] / TimeoutError on socket connection`
- **Correct Fix:** Set `sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)` and use ephemeral port allocation (port 0).
