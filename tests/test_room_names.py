"""
Room name persistence and generation tests.

Tests the Excel Room Names worksheet read/write layer and the
generar_mapa.py room name override pipeline.

Run:
    python tests/test_room_names.py

Exit code:
    0 -- All tests passed
    1 -- Some tests failed
"""

import json
import os
import shutil
import sys
import tempfile

import openpyxl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.excel_utils import (
    read_room_names,
    write_room_name,
    room_names_from_positions,
    _SHEET_NAME,
    _HEADERS,
)

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


def _make_workbook(path, sheets=None):
    """Create a minimal .xlsx with optional sheets and data."""
    wb = openpyxl.Workbook()
    if sheets:
        for name, headers, rows in sheets:
            ws = wb.create_sheet(name)
            if headers:
                ws.append(headers)
            for row in rows:
                ws.append(row)
    wb.save(path)
    wb.close()


def _make_workbook_with_room_names(path, entries=None):
    """Create a workbook with a Room Names sheet."""
    wb = openpyxl.Workbook()
    ws = wb.create_sheet(_SHEET_NAME)
    ws.append(_HEADERS)
    if entries:
        for entry in entries:
            ws.append(entry)
    wb.save(path)
    wb.close()


def test_01_read_room_names_empty_when_no_sheet():
    print("\n1. read_room_names returns empty when sheet missing")
    tmp = tempfile.mkdtemp(prefix="sortis_roomnames_")
    try:
        path = os.path.join(tmp, "test.xlsx")
        _make_workbook(path)
        result = read_room_names(path)
        report("Empty dict when no Room Names sheet", result == {}, str(result))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_02_read_room_names_empty_when_no_file():
    print("\n2. read_room_names returns empty when file missing")
    result = read_room_names("/nonexistent/path.xlsx")
    report("Empty dict when file missing", result == {})


def test_03_read_room_names_empty_when_no_data():
    print("\n3. read_room_names returns empty when sheet has headers only")
    tmp = tempfile.mkdtemp(prefix="sortis_roomnames_")
    try:
        path = os.path.join(tmp, "test.xlsx")
        _make_workbook_with_room_names(path)
        result = read_room_names(path)
        report("Empty dict when no data rows", result == {}, str(result))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_04_read_room_names_with_data():
    print("\n4. read_room_names reads entries correctly")
    tmp = tempfile.mkdtemp(prefix="sortis_roomnames_")
    try:
        path = os.path.join(tmp, "test.xlsx")
        entries = [
            [7, 11, 15, 16, "MEETING ROOM A"],
            [1, 6, 3, 24, "OPEN WORKSPACE"],
        ]
        _make_workbook_with_room_names(path, entries)
        result = read_room_names(path)
        report("Two entries read", len(result) == 2, str(len(result)))
        report("First entry correct",
               result.get((7, 11, 15, 16)) == "MEETING ROOM A",
               str(result.get((7, 11, 15, 16))))
        report("Second entry correct",
               result.get((1, 6, 3, 24)) == "OPEN WORKSPACE",
               str(result.get((1, 6, 3, 24))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_05_read_room_names_skips_empty_names():
    print("\n5. read_room_names skips entries with empty names")
    tmp = tempfile.mkdtemp(prefix="sortis_roomnames_")
    try:
        path = os.path.join(tmp, "test.xlsx")
        entries = [
            [7, 11, 15, 16, "MEETING ROOM"],
            [1, 6, 3, 24, ""],
            [10, 12, 1, 2, None],
        ]
        _make_workbook_with_room_names(path, entries)
        result = read_room_names(path)
        report("Only one entry (empty names skipped)",
               len(result) == 1, str(len(result)))
        report("Correct entry kept",
               result.get((7, 11, 15, 16)) == "MEETING ROOM")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_06_write_room_name_creates_sheet():
    print("\n6. write_room_name creates Room Names sheet if missing")
    tmp = tempfile.mkdtemp(prefix="sortis_roomnames_")
    try:
        path = os.path.join(tmp, "test.xlsx")
        _make_workbook(path)
        write_room_name(path, 7, 11, 15, 16, "NEW NAME")
        result = read_room_names(path)
        report("Sheet created and entry written",
               len(result) == 1, str(len(result)))
        report("Entry correct",
               result.get((7, 11, 15, 16)) == "NEW NAME")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_07_write_room_name_updates_existing():
    print("\n7. write_room_name updates existing entry")
    tmp = tempfile.mkdtemp(prefix="sortis_roomnames_")
    try:
        path = os.path.join(tmp, "test.xlsx")
        entries = [[7, 11, 15, 16, "OLD NAME"]]
        _make_workbook_with_room_names(path, entries)
        write_room_name(path, 7, 11, 15, 16, "UPDATED NAME")
        result = read_room_names(path)
        report("Entry updated",
               result.get((7, 11, 15, 16)) == "UPDATED NAME",
               str(result))
        report("Still only one entry",
               len(result) == 1, str(len(result)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_08_write_room_name_appends_new():
    print("\n8. write_room_name appends new entry")
    tmp = tempfile.mkdtemp(prefix="sortis_roomnames_")
    try:
        path = os.path.join(tmp, "test.xlsx")
        entries = [[7, 11, 15, 16, "EXISTING"]]
        _make_workbook_with_room_names(path, entries)
        write_room_name(path, 1, 6, 3, 24, "NEW ROOM")
        result = read_room_names(path)
        report("Two entries after append",
               len(result) == 2, str(len(result)))
        report("Existing entry preserved",
               result.get((7, 11, 15, 16)) == "EXISTING")
        report("New entry added",
               result.get((1, 6, 3, 24)) == "NEW ROOM")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_09_room_names_from_positions():
    print("\n9. room_names_from_positions extracts room geometry dict")
    data = {
        "rooms": [
            {"name": "COMEDOR", "min_row": 1, "max_row": 6, "min_col": 1, "max_col": 2},
            {"name": "", "min_row": 15, "max_row": 15, "min_col": 25, "max_col": 26},
        ]
    }
    result = room_names_from_positions(data)
    report("Two rooms extracted", len(result) == 2, str(len(result)))
    report("Named room correct",
           result.get((1, 6, 1, 2)) == "COMEDOR")
    report("Unnamed room has empty string",
           result.get((15, 15, 25, 26)) == "")


def test_10_read_room_names_ignores_bad_rows():
    print("\n10. read_room_names ignores rows with invalid data")
    tmp = tempfile.mkdtemp(prefix="sortis_roomnames_")
    try:
        path = os.path.join(tmp, "test.xlsx")
        wb = openpyxl.Workbook()
        ws = wb.create_sheet(_SHEET_NAME)
        ws.append(_HEADERS)
        ws.append([7, 11, 15, 16, "VALID ROOM"])
        ws.append(["bad", "data", "row", "ignored", "X"])
        ws.append([None, None, None, None, None])
        ws.append([1, 6, 3, 24, "ANOTHER VALID"])
        wb.save(path)
        wb.close()
        result = read_room_names(path)
        report("Two valid entries (bad rows skipped)",
               len(result) == 2, str(len(result)))
        report("Valid entry 1",
               result.get((7, 11, 15, 16)) == "VALID ROOM")
        report("Valid entry 2",
               result.get((1, 6, 3, 24)) == "ANOTHER VALID")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("  Room Names persistence tests")
    print("=" * 60)

    try:
        test_01_read_room_names_empty_when_no_sheet()
        test_02_read_room_names_empty_when_no_file()
        test_03_read_room_names_empty_when_no_data()
        test_04_read_room_names_with_data()
        test_05_read_room_names_skips_empty_names()
        test_06_write_room_name_creates_sheet()
        test_07_write_room_name_updates_existing()
        test_08_write_room_name_appends_new()
        test_09_room_names_from_positions()
        test_10_read_room_names_ignores_bad_rows()
    finally:
        pass

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
