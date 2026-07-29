#!/usr/bin/env python3
"""
Reads SORTIS_FLOOR_PLAN.xlsx and PTY Users & Roles.xlsx, then outputs
positions.json to the OneDrive FLOOR PLAN folder for the SORTIS Desktop app.
"""

import json
import os
import sys
from datetime import datetime, timezone

import openpyxl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.core.path_config import get_floor_plan_path


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(SCRIPT_DIR, "..", "SORTIS_FLOOR_PLAN.xlsx")
PTY_USERS_PATH = r"C:\Users\david.arjona\OneDrive - a360inc\PTY Files - PTY Users\PTY Users & Roles.xlsx"


def fix_encoding(s):
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s


def normalize_seat_no(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return str(int(val))
    return str(val).strip()


def read_pty_users():
    if not os.path.exists(PTY_USERS_PATH):
        print(f"  WARNING: PTY Users not found at {PTY_USERS_PATH}")
        return {}
    wb = openpyxl.load_workbook(PTY_USERS_PATH, read_only=True, data_only=True)
    ws = wb["PTY Users"]
    people = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        first, last, title, div, email = row[0], row[1], row[2], row[3], row[4]
        if not first or not last:
            continue
        name = fix_encoding(f"{first} {last}".strip())
        dept = fix_encoding(str(div).strip()) if div else None
        title_str = fix_encoding(str(title).strip()) if title else None
        email_str = fix_encoding(str(email).strip()) if email else None
        people[name] = {"department": dept, "title": title_str, "email": email_str}
    wb.close()
    return people


def read_seats_allocation(wb):
    ws = wb["Seats Allocation"]
    seats = {}
    for row in range(2, ws.max_row + 1):
        seat_no_raw = ws.cell(row, 1).value
        name = ws.cell(row, 2).value
        brigadista = ws.cell(row, 3).value
        notas = ws.cell(row, 4).value
        department = ws.cell(row, 5).value
        title = ws.cell(row, 6).value
        name_str = fix_encoding(str(name).strip()) if name else None
        seat_key = normalize_seat_no(seat_no_raw)
        if seat_key is None:
            continue
        seats[seat_key] = {
            "name": name_str if name_str and name_str != "-" else None,
            "brigadista": fix_encoding(str(brigadista).strip()) if brigadista else None,
            "notas": fix_encoding(str(notas).strip()) if notas else None,
            "department": fix_encoding(str(department).strip()) if department else None,
            "title": fix_encoding(str(title).strip()) if title else None,
        }
    return seats


def read_floor_plan(wb):
    ws = wb["Floor plan"]
    merged_map = {}
    rooms = []
    for mc in ws.merged_cells.ranges:
        val = ws.cell(mc.min_row, mc.min_col).value
        if val is not None:
            val = fix_encoding(str(val).strip())
        info = {
            "name": val or "",
            "min_row": mc.min_row,
            "min_col": mc.min_col,
            "max_row": mc.max_row,
            "max_col": mc.max_col,
        }
        for r in range(mc.min_row, mc.max_row + 1):
            for c in range(mc.min_col, mc.max_col + 1):
                merged_map[(r, c)] = info
        if val:
            rooms.append(info)

    seats = []
    for row in range(1, ws.max_row + 1):
        for col in range(1, ws.max_column + 1):
            key = (row, col)
            if key in merged_map:
                continue
            val = ws.cell(row, col).value
            if val is not None:
                try:
                    seat_num = int(val)
                    seats.append({
                        "row": row,
                        "col": col,
                        "seat_no": str(seat_num),
                    })
                except (ValueError, TypeError):
                    pass

    max_row = 1
    max_col = 1
    for info in rooms:
        max_row = max(max_row, info["max_row"])
        max_col = max(max_col, info["max_col"])
    for s in seats:
        max_row = max(max_row, s["row"])
        max_col = max(max_col, s["col"])

    return rooms, seats, max_row, max_col


def build_output(rooms, grid_seats, seats_alloc, pty_users):
    departments = set()
    output_seats = []
    for gs in grid_seats:
        seat_no = gs["seat_no"]
        alloc = seats_alloc.get(seat_no, {})
        person_name = alloc.get("name")
        person = None
        if person_name:
            pty = pty_users.get(person_name, {})
            dept = pty.get("department") or alloc.get("department")
            if dept:
                departments.add(dept)
            person = {
                "name": person_name,
                "department": dept,
                "title": pty.get("title") or alloc.get("title"),
                "email": pty.get("email"),
            }
        output_seats.append({
            "seat_no": seat_no,
            "row": gs["row"],
            "col": gs["col"],
            "person": person,
            "brigadista": alloc.get("brigadista"),
            "notas": alloc.get("notas"),
        })

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "grid": {"rows": max(s["row"] for s in grid_seats) if grid_seats else 0,
                 "cols": max(s["col"] for s in grid_seats) if grid_seats else 0},
        "rooms": rooms,
        "seats": output_seats,
        "departments": sorted(departments),
    }


def main():
    excel_path = os.path.abspath(EXCEL_PATH)
    if not os.path.exists(excel_path):
        print(f"ERROR: Excel not found at {excel_path}")
        sys.exit(1)

    print(f"Reading: {excel_path}")
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    rooms, grid_seats, max_row, max_col = read_floor_plan(wb)
    print(f"  Rooms: {len(rooms)}, Seats on grid: {len(grid_seats)}")
    print(f"  Grid: {max_row}x{max_col}")

    seats_alloc = read_seats_allocation(wb)
    wb.close()
    print(f"  Seats allocation entries: {len(seats_alloc)}")

    print(f"Reading PTY Users...")
    pty_users = read_pty_users()
    print(f"  PTY Users entries: {len(pty_users)}")

    data = build_output(rooms, grid_seats, seats_alloc, pty_users)
    data["grid"]["rows"] = max_row
    data["grid"]["cols"] = max_col

    output_dir = get_floor_plan_path()
    if not output_dir:
        print("ERROR: FLOOR PLAN directory not found via OneDrive path.")
        sys.exit(1)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "positions.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nWritten: {output_path}")
    print(f"  Seats: {len(data['seats'])}, Departments: {len(data['departments'])}")


if __name__ == "__main__":
    main()
