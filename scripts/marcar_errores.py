#!/usr/bin/env python3
"""
Reads SORTIS_FLOOR_PLAN.xlsx Seats Allocation sheet,
compares each name EXACTLY against Query - Active (PTY Users),
adds Status column G with ERROR for non-matching names, and
fills those cells red so the user can see/fix them manually.

The exact-match logic mirrors generar_mapa.py so the same seats
that produce missing data will be highlighted.
"""

import sys
import os
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(SCRIPT_DIR, "..", "SORTIS_FLOOR_PLAN.xlsx")
PTY_USERS_PATH = r"C:\Users\david.arjona\OneDrive - a360inc\PTY Files - PTY Users\PTY Users & Roles.xlsx"

RED_FILL = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
RED_FONT = Font(color="FFFFFF", bold=True)
CENTER = Alignment(horizontal="center", vertical="center")


def fix_encoding(s):
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s


def load_active_names():
    if not os.path.exists(PTY_USERS_PATH):
        print(f"  WARNING: PTY Users file not found at {PTY_USERS_PATH}")
        return {}
    wb = openpyxl.load_workbook(PTY_USERS_PATH, read_only=True, data_only=True)
    ws = wb["Query - Active"]
    names = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        full_name = row[7]
        if full_name:
            name = fix_encoding(str(full_name).strip())
            names[name.lower()] = name
    wb.close()
    return names


def main():
    excel_path = os.path.abspath(EXCEL_PATH)
    if not os.path.exists(excel_path):
        print(f"ERROR: Excel not found at {excel_path}")
        sys.exit(1)

    print(f"Loading active names from PTY Users (exact match)...")
    active_names = load_active_names()
    print(f"  Active users: {len(active_names)}")

    print(f"\nOpening: {excel_path}")
    wb = openpyxl.load_workbook(excel_path)
    ws = wb["Seats Allocation"]

    max_col = ws.max_column
    status_col = max_col + 1

    # Add header
    header_cell = ws.cell(1, status_col)
    header_cell.value = "Status"
    header_cell.font = Font(bold=True)
    header_cell.alignment = CENTER

    errors_found = 0
    total_rows = 0
    grid_rows = 0

    for row in range(2, ws.max_row + 1):
        seat_no = ws.cell(row, 1).value
        name = ws.cell(row, 2).value

        name_str = fix_encoding(str(name).strip()) if name else None
        if not name_str or name_str == "-":
            continue

        total_rows += 1
        nl = name_str.lower().strip()
        exact_match = nl in active_names

        # Check if seat_no is numeric (actual grid seat) vs label (e.g. Oficina 01, Recepcion)
        is_grid_seat = False
        try:
            int(str(seat_no).strip())
            is_grid_seat = True
        except (ValueError, TypeError):
            pass

        if is_grid_seat:
            grid_rows += 1

        if not exact_match:
            cell = ws.cell(row, status_col)
            cell.value = "ERROR"
            cell.fill = RED_FILL
            cell.font = RED_FONT
            cell.alignment = CENTER
            errors_found += 1
            label = "grid" if is_grid_seat else "label"
            print(f"  ERROR [{label}] Row {row}, Seat {seat_no}: '{name_str}' -> no exact match in Query - Active")

    wb.save(excel_path)
    wb.close()
    print(f"\nDone. {errors_found}/{total_rows} rows marked ERROR (column G = Status, red fill).")
    print(f"  Grid seats with person: {grid_rows}")
    print(f"  File saved: {excel_path}")


if __name__ == "__main__":
    main()
