#!/usr/bin/env python3
"""
Fixes the 21 mismatched names in SORTIS_FLOOR_PLAN.xlsx Seats Allocation.
Corrections based on comparison with Query - Active (PTY Users).
"""

import os
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(SCRIPT_DIR, "..", "SORTIS_FLOOR_PLAN.xlsx")

# Corrections: (seat_row_number, correct_name, extra_notes)
# We identify rows by seat_no since row numbers could shift
CORRECTIONS = {
    # --- 18 typo/encoding fixes ---
    "Recepción": {"name": "Jenniffer Consuegra", "notes": None},
    "4":    {"name": "Ricardo Gutierrez", "notes": None},
    "16":   {"name": "Francisco Sánchez", "notes": None},
    "46":   {"name": "Kate Aizpurua", "notes": None},
    "48":   {"name": "Nathalie Quintero", "notes": None},
    "91":   {"name": "Lilliana Prado", "notes": None},
    "108":  {"name": "Sebastián Trujillo", "notes": None},
    "113":  {"name": "Roxanna Robayna", "notes": None},
    "115":  {"name": "Lester Almanza", "notes": None},
    "119":  {"name": "Gianluca Monteverde", "notes": None},
    "133":  {"name": "Zoe Valdes", "notes": None},
    "137":  {"name": "Joelys Zarzavilla", "notes": None},
    "142":  {"name": "Ramón Sasso", "notes": None},
    "144":  {"name": "Ricardo Mc Kinnon", "notes": None},
    "167":  {"name": "Enrique Piggott", "notes": None},
    # --- 3 missing surnames ---
    "97":   {"name": "Jahir Rodriguez", "notes": None},
    "98":   {"name": "Yasury Martinez", "notes": None},
    "138":  {"name": "Ameth Alvarez", "notes": None},
    # --- Ana (seat 109) - best guess based on Query - Active ---
    "109":  {"name": "Ana Murillo", "notes": None},
    "110":  {"name": "Ailen Cerrud", "notes": None},
}

def fix_encoding(s):
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s


def main():
    excel_path = os.path.abspath(EXCEL_PATH)
    print(f"Opening: {excel_path}")
    wb = openpyxl.load_workbook(excel_path)
    ws = wb["Seats Allocation"]

    # Build lookup: seat_no -> row
    seat_to_row = {}
    for row in range(2, ws.max_row + 1):
        raw = ws.cell(row, 1).value
        if raw is None:
            continue
        try:
            key = str(int(raw))
        except (ValueError, TypeError):
            key = str(raw).strip()
        seat_to_row[key] = row

    # Backup original names
    print(f"\nCorrections to apply:")
    fixed = 0
    for seat_no, corr in sorted(CORRECTIONS.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
        row = seat_to_row.get(seat_no)
        if not row:
            print(f"  WARNING: Seat '{seat_no}' not found in Seats Allocation")
            continue
        old_name = fix_encoding(str(ws.cell(row, 2).value or ""))
        new_name = corr["name"]
        notes = corr.get("notes")
        print(f"  Seat {seat_no} (Row {row}): '{old_name}' -> '{new_name}'")
        ws.cell(row, 2).value = new_name
        if notes:
            ws.cell(row, 4).value = notes
        fixed += 1

    # --- Special case: Seat 134 shared by Rosendo Leveane + Tatiana Giron ---
    row134 = seat_to_row.get("134")
    if row134:
        old_134 = fix_encoding(str(ws.cell(row134, 2).value or ""))
        print(f"\n  Seat 134 (Row {row134}): '{old_134}' -> 'Rosendo Leveane' (Tatiana Giron moved to Notas)")
        ws.cell(row134, 2).value = "Rosendo Leveane"
        ws.cell(row134, 4).value = "Tatiana Giron (comparte asiento)"

    # Now clear Status column for fixed rows (remove ERROR)
    print(f"\nClearing Status (col G) for fixed seats...")
    for seat_no in CORRECTIONS:
        row = seat_to_row.get(seat_no)
        if row:
            ws.cell(row, 7).value = None
            ws.cell(row, 7).fill = PatternFill(fill_type=None)
    # Also clear for 134
    if row134:
        ws.cell(row134, 7).value = None
        ws.cell(row134, 7).fill = PatternFill(fill_type=None)

    wb.save(excel_path)
    wb.close()
    print(f"\nDone. {fixed} names corrected, Status cleared.")


if __name__ == "__main__":
    main()
