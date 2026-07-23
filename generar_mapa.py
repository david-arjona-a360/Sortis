#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lee el archivo Excel SORTIS_FLOOR_PLAN.xlsx y genera floor_plan_data.json
con toda la información necesaria para el mapa interactivo.
"""

import json
import os
import openpyxl

EXCEL_PATH = r"C:\Users\david.arjona\OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN\SORTIS_FLOOR_PLAN.xlsx"
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "floor_plan_data.json")

GRID_ROWS = 76
GRID_COLS = 27


def fix_encoding(s):
    """Fix mojibake: UTF-8 bytes decoded as Latin-1/CP1252."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s


def normalize_seat_no(val):
    """Convert seat number to a consistent string key."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return str(int(val))
    return str(val).strip()


def read_floor_plan(wb):
    """Parse the Floor plan sheet into a grid structure."""
    ws = wb["Floor plan"]

    # Build merged cell map: (row, col) -> merge info
    merged_map = {}
    room_cells = []  # list of room definitions
    for mc in ws.merged_cells.ranges:
        val = ws.cell(mc.min_row, mc.min_col).value
        if val is not None:
            val = fix_encoding(str(val).strip())
        info = {
            "name": val,
            "min_row": mc.min_row,
            "min_col": mc.min_col,
            "max_row": mc.max_row,
            "max_col": mc.max_col,
        }
        for r in range(mc.min_row, mc.max_row + 1):
            for c in range(mc.min_col, mc.max_col + 1):
                merged_map[(r, c)] = info
        if val:
            room_cells.append(info)

    # Build grid
    grid = []
    seat_positions = []

    for row in range(1, GRID_ROWS + 1):
        for col in range(1, GRID_COLS + 1):
            cell = ws.cell(row, col)
            val = cell.value
            key = (row, col)

            entry = {
                "row": row,
                "col": col,
                "type": "empty",
                "value": None,
                "room_name": None,
                "seat_no": None,
                "is_origin": False,
            }

            if key in merged_map:
                mi = merged_map[key]
                entry["room_name"] = mi["name"]
                entry["type"] = "room"
                entry["is_origin"] = (row == mi["min_row"] and col == mi["min_col"])
                entry["span_rows"] = mi["max_row"] - mi["min_row"] + 1
                entry["span_cols"] = mi["max_col"] - mi["min_col"] + 1
            elif val is not None:
                # Check if it's a seat number
                try:
                    seat_num = int(val)
                    entry["type"] = "seat"
                    entry["seat_no"] = str(seat_num)
                    seat_positions.append(entry.copy())
                except (ValueError, TypeError):
                    # Could be text like "     " or something else
                    sval = str(val).strip()
                    if sval:
                        entry["value"] = sval
                        entry["type"] = "label"
                    # whitespace-only or empty: leave as empty

            grid.append(entry)

    return grid, room_cells, seat_positions


def read_seats_allocation(wb):
    """Parse Seats Allocation sheet into a dict keyed by seat_no string."""
    ws = wb["Seats Allocation"]
    seats = {}
    for row in range(2, ws.max_row + 1):
        seat_no_raw = ws.cell(row, 1).value
        name = ws.cell(row, 2).value
        brigadista = ws.cell(row, 3).value
        notas = ws.cell(row, 4).value

        seat_key = normalize_seat_no(seat_no_raw)
        if seat_key is None:
            continue

        seats[seat_key] = {
            "seat_no_raw": seat_no_raw,
            "name": fix_encoding(str(name).strip()) if name else None,
            "brigadista": fix_encoding(str(brigadista).strip()) if brigadista else None,
            "notas": fix_encoding(str(notas).strip()) if notas else None,
        }
    return seats


def read_sheet1(wb):
    """Parse Sheet1 into a dict keyed by name -> {department, title}."""
    ws = wb["Sheet1"]
    people = {}
    for row in range(1, ws.max_row + 1):
        name = ws.cell(row, 1).value
        dept = ws.cell(row, 2).value
        title = ws.cell(row, 3).value
        if name:
            key = fix_encoding(str(name).strip())
            people[key] = {
                "department": fix_encoding(str(dept).strip()) if dept else None,
                "title": fix_encoding(str(title).strip()) if title else None,
            }
    return people


def join_data(seat_positions, seats_alloc, people):
    """Enrich each seat on the grid with person data from other sheets."""
    result = []
    for sp in seat_positions:
        seat_no = sp["seat_no"]
        info = seats_alloc.get(seat_no, None)
        person = None
        if info and info["name"] and info["name"] != "-":
            # Look up department/title from Sheet1
            p = people.get(info["name"], None)
            person = {
                "name": info["name"],
                "brigadista": info["brigadista"],
                "notas": info["notas"],
                "department": p["department"] if p else None,
                "title": p["title"] if p else None,
            }
        result.append({
            "row": sp["row"],
            "col": sp["col"],
            "seat_no": seat_no,
            "person": person,
            "brigadista": info["brigadista"] if info else None,
        })
    return result


def main():
    print(f"Leyendo archivo Excel: {EXCEL_PATH}")
    wb = openpyxl.load_workbook(EXCEL_PATH)

    print("Parseando plano de oficina...")
    grid, room_cells, seat_positions = read_floor_plan(wb)
    print(f"  Grid: {GRID_ROWS}x{GRID_COLS} = {len(grid)} celdas")
    print(f"  Salas/áreas: {len(room_cells)}")
    print(f"  Puestos encontrados en plano: {len(seat_positions)}")

    print("Parseando asignación de puestos...")
    seats_alloc = read_seats_allocation(wb)
    print(f"  Registros en Seats Allocation: {len(seats_alloc)}")

    print("Parseando datos de personas (Sheet1)...")
    people = read_sheet1(wb)
    print(f"  Personas en Sheet1: {len(people)}")

    print("Uniendo datos...")
    seats_with_people = join_data(seat_positions, seats_alloc, people)
    occupied = sum(1 for s in seats_with_people if s["person"] is not None)
    print(f"  Puestos con persona asignada: {occupied}/{len(seats_with_people)}")

    # Collect unique departments
    departments = set()
    for s in seats_with_people:
        if s["person"] and s["person"]["department"]:
            departments.add(s["person"]["department"])

    output = {
        "grid": grid,
        "rooms": room_cells,
        "seats": seats_with_people,
        "departments": sorted(departments),
        "total_seats": len(seats_with_people),
        "occupied_seats": occupied,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nArchivo generado: {OUTPUT_PATH}")
    print(f"Tamano: {os.path.getsize(OUTPUT_PATH):,} bytes")


if __name__ == "__main__":
    main()
