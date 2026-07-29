"""
Phase 0 -- OneDrive Concurrency Prototype.

Validates that individual request files work correctly with OneDrive Sync
under concurrent write load from multiple simulated users.

Run:
    python tests/test_onedrive_concurrency.py

Requires:
    - OneDrive - a360inc synced locally
    - PTY Files - Documents/FLOOR PLAN folder exists

Exit code:
    0 -- All tests passed
    1 -- Some tests failed
"""

import os
import sys
import json
import time
import multiprocessing as mp
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.path_config import get_floor_plan_path
from src.core.file_utils import atomic_write_json, ensure_directory
from src.core.request_store import RequestStore


# -- Configuration ----------------------------------------------------------
TEST_DIR_NAME = "concurrency_test_" + datetime.now().strftime("%Y%m%d_%H%M%S")
USERS = 3
REQUESTS_PER_USER = 50
TIMEOUT_SECONDS = 60


# -- Helpers ----------------------------------------------------------------
PASS = 0
FAIL = 0
ERRORS = []


def report(test_name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {test_name}")
    else:
        FAIL += 1
        ERRORS.append((test_name, detail))
        print(f"  [FAIL] {test_name} -- {detail}")


def make_request(user_id, seq):
    now = datetime.now(timezone.utc)
    date = now.strftime("%Y%m%d")
    uid = f"{user_id}{seq:04d}"
    return {
        "id": f"REQ-{date}-{uid}",
        "date": now.strftime("%Y-%m-%d"),
        "requestor_name": f"User {user_id}",
        "requestor_email": f"user{user_id}@test.com",
        "department": "TEST",
        "position": str(100 + seq),
        "current_employee": f"Employee {seq % 10}",
        "proposed_employee": f"Candidate {user_id}-{seq}",
        "created_at": now.isoformat() + "Z",
        "version": 1,
    }


# -- Test runner for child processes ----------------------------------------
def worker_write(args):
    test_dir, user_id, count = args
    from src.core.request_store import RequestStore
    from src.models.request import Request
    store = RequestStore(test_dir)
    results = []
    for i in range(count):
        req = Request(
            requestor_name=f"User {user_id}",
            requestor_email=f"user{user_id}@test.com",
            department="TEST",
            position=str(100 + i),
            current_employee=f"Employee {i % 10}",
            proposed_employee=f"Candidate {user_id}-{i}",
        )
        try:
            store.save(req)
            results.append((req.id, True))
        except Exception as e:
            results.append((req.id, False, str(e)))
    return results


# -- Tests ------------------------------------------------------------------
def test_01_setup():
    print("\n1. Setup test directory")
    base = get_floor_plan_path()
    if not base:
        print("  [FAIL] OneDrive FLOOR PLAN folder not found.")
        print("    Ensure OneDrive is synced and PTY Files - Documents/FLOOR PLAN exists.")
        return False
    test_dir = os.path.join(base, TEST_DIR_NAME)
    ensure_directory(test_dir)
    print(f"  [DIR] Test directory: {test_dir}")
    return True


def test_02_single_user():
    print("\n2. Single-user sequential writes")
    base = get_floor_plan_path()
    test_dir = os.path.join(base, TEST_DIR_NAME)
    store = RequestStore(test_dir)
    req = make_request("SINGLE", 1)
    try:
        atomic_write_json(test_dir, f"{req['id']}.json", req)
        report("Write single request", True)
    except Exception as e:
        report("Write single request", False, str(e))

    retrieved = store.get(req["id"])
    report("Read single request back", retrieved is not None)
    if retrieved:
        report("Request ID matches", retrieved.id == req["id"])
        report("Requestor name matches", retrieved.requestor_name == req["requestor_name"])
        report("Department matches", retrieved.department == req["department"])


def test_03_sequential_writes():
    print("\n3. Sequential writes (1 user, 50 requests)")
    base = get_floor_plan_path()
    test_dir = os.path.join(base, TEST_DIR_NAME)
    store = RequestStore(test_dir)
    start = time.time()
    for i in range(50):
        req = make_request("SEQ", i)
        atomic_write_json(test_dir, f"{req['id']}.json", req)
    elapsed = time.time() - start
    count = store.count()
    report(f"50 sequential writes in {elapsed:.2f}s", count >= 50, f"Found {count} files")
    report("Average write < 100ms", elapsed / 50 < 0.1, f"Avg: {(elapsed/50)*1000:.1f}ms")


def test_04_concurrent_writes():
    print(f"\n4. Concurrent writes ({USERS} users, {REQUESTS_PER_USER} requests each)")
    base = get_floor_plan_path()
    test_dir = os.path.join(base, TEST_DIR_NAME)
    pool = mp.Pool(USERS)
    args = [(test_dir, i, REQUESTS_PER_USER) for i in range(USERS)]
    start = time.time()
    try:
        all_results = pool.map(worker_write, args)
    except Exception as e:
        report("Concurrent write execution", False, str(e))
        return
    finally:
        pool.close()
        pool.join()
    elapsed = time.time() - start
    total_written = sum(len(r) for r in all_results)
    report(f"Concurrent writes completed in {elapsed:.2f}s",
           total_written == USERS * REQUESTS_PER_USER,
           f"Expected {USERS * REQUESTS_PER_USER}, got {total_written}")

    successes = sum(all(r[1] for r in results) for results in all_results)
    report("No write failures", successes == USERS,
           f"{USERS - successes} workers reported errors")


def test_05_file_integrity():
    print("\n5. File integrity check")
    base = get_floor_plan_path()
    test_dir = os.path.join(base, TEST_DIR_NAME)
    store = RequestStore(test_dir)
    start = time.time()
    all_requests = store.list_all()
    elapsed = time.time() - start
    expected = 1 + 50 + USERS * REQUESTS_PER_USER
    report(f"List all {len(all_requests)} requests in {elapsed:.2f}s",
           len(all_requests) == expected,
           f"Expected {expected}, got {len(all_requests)}")

    corrupt = 0
    for f in os.listdir(test_dir):
        if not f.endswith(".json"):
            continue
        path = os.path.join(test_dir, f)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not all(k in data for k in ("id", "requestor_name", "department")):
                corrupt += 1
        except (json.JSONDecodeError, IOError):
            corrupt += 1
    report("No corrupt files", corrupt == 0, f"{corrupt} corrupt files found")


def test_06_conflict_detection():
    print("\n6. OneDrive conflict file detection")
    base = get_floor_plan_path()
    test_dir = os.path.join(base, TEST_DIR_NAME)
    store = RequestStore(test_dir)
    conflicts = store.find_conflict_files()
    report("No OneDrive conflict files (_conflict)", len(conflicts) == 0,
           f"Found conflict files: {conflicts[:5]}" if conflicts else "")


def test_07_read_performance():
    print("\n7. Read performance (all requests sequential)")
    base = get_floor_plan_path()
    test_dir = os.path.join(base, TEST_DIR_NAME)
    store = RequestStore(test_dir)
    all_requests = store.list_all()
    ids = [r.id for r in all_requests]
    expected_ids = sorted(ids, reverse=True)
    report("List sorted by date (newest first)",
           ids == expected_ids,
           f"First: {ids[:3]}, Expected first: {expected_ids[:3]}")


def test_08_cleanup():
    print("\n8. Cleanup test directory (best-effort)")
    base = get_floor_plan_path()
    test_dir = os.path.join(base, TEST_DIR_NAME)
    import shutil
    import time
    for attempt in range(3):
        try:
            shutil.rmtree(test_dir)
            report("Test directory removed", not os.path.exists(test_dir))
            return
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                report("Test directory removed (ignored -- OneDrive syncing)",
                       True, f"Gave up after 3 attempts: {e}")


# -- Main -------------------------------------------------------------------
def main():
    print("=" * 60)
    print("  Phase 0 -- OneDrive Concurrency Prototype")
    print("=" * 60)
    print(f"  Users: {USERS}, Requests per user: {REQUESTS_PER_USER}")
    print(f"  Test dir: {TEST_DIR_NAME}")
    print("=" * 60)

    if not test_01_setup():
        sys.exit(1)

    test_02_single_user()
    test_03_sequential_writes()
    test_04_concurrent_writes()
    test_05_file_integrity()
    test_06_conflict_detection()
    test_07_read_performance()
    test_08_cleanup()

    print("\n" + "=" * 60)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    if FAIL:
        print("  Failures:")
        for name, detail in ERRORS:
            print(f"    - {name}: {detail}")
    print("=" * 60)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
