#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-time migration: Read Excel and create records in SharePoint Lists.

Usage:
  1. Create SharePoint Lists "People" and "Seats" first (see README)
  2. Set SHAREPOINT_SITE below
  3. Run: python migrate_to_sharepoint.py

Authentication: Uses NTLM (Windows Integrated Auth) or cookie-based auth.
"""

import json
import os
import sys
import requests
from requests_ntlm import HttpNtlmAuth
import openpyxl

# ============================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================
EXCEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SORTIS_FLOOR_PLAN.xlsx")
SHAREPOINT_SITE = "https://a360inc.sharepoint.com/sites/YOURSITE"  # UPDATE THIS

# Authentication - choose one:
AUTH_METHOD = "ntlm"  # "ntlm" for Windows Integrated Auth
# AUTH_METHOD = "cookie"  # For browser cookie auth

# NTLM credentials (if AUTH_METHOD = "ntlm")
NTLM_USERNAME = os.environ.get("USERNAME", "")
NTLM_DOMAIN = os.environ.get("USERDOMAIN", "")

# ============================================================


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


def read_excel(excel_path):
    """Read all data from Excel."""
    print(f"Reading Excel: {excel_path}")
    wb = openpyxl.load_workbook(excel_path)

    # Read Seats Allocation (with new Departamento column E)
    ws_seats = wb["Seats Allocation"]
    seats = []
    for row in range(2, ws_seats.max_row + 1):
        seat_no = ws_seats.cell(row, 1).value
        name = ws_seats.cell(row, 2).value
        brigadista = ws_seats.cell(row, 3).value
        notas = ws_seats.cell(row, 4).value
        department = ws_seats.cell(row, 5).value

        seat_key = normalize_seat_no(seat_no)
        if seat_key is None:
            continue

        seats.append({
            "seat_no": seat_key,
            "name": fix_encoding(str(name).strip()) if name else None,
            "brigadista": fix_encoding(str(brigadista).strip()) if brigadista else None,
            "notas": fix_encoding(str(notas).strip()) if notas else None,
            "department": fix_encoding(str(department).strip()) if department else None,
        })

    # Read Sheet1 (additional person data)
    ws_people = wb["Sheet1"]
    people = {}
    for row in range(1, ws_people.max_row + 1):
        name = ws_people.cell(row, 1).value
        dept = ws_people.cell(row, 2).value
        title = ws_people.cell(row, 3).value
        if name:
            key = fix_encoding(str(name).strip())
            people[key] = {
                "department": fix_encoding(str(dept).strip()) if dept else None,
                "title": fix_encoding(str(title).strip()) if title else None,
            }

    # Read Brigadistas
    ws_brig = wb["Brigadistas"]
    brigadistas = []
    for row in range(2, ws_brig.max_row + 1):
        seat_no = ws_brig.cell(row, 1).value
        name = ws_brig.cell(row, 2).value
        dept = ws_brig.cell(row, 3).value
        if name:
            brigadistas.append({
                "seat_no": normalize_seat_no(seat_no),
                "name": fix_encoding(str(name).strip()),
                "department": fix_encoding(str(dept).strip()) if dept else None,
            })

    wb.close()
    print(f"  Seats: {len(seats)}")
    print(f"  People (Sheet1): {len(people)}")
    print(f"  Brigadistas: {len(brigadistas)}")
    return seats, people, brigadistas


def get_auth():
    """Get authentication handler for SharePoint."""
    if AUTH_METHOD == "ntlm":
        print(f"  Auth: NTLM ({NTLM_DOMAIN}\\{NTLM_USERNAME})")
        return HttpNtlmAuth(f"{NTLM_DOMAIN}\\{NTLM_USERNAME}", "")
    else:
        print("  Auth: Cookie (session)")
        return None


def get_form_digest(session, site_url, auth):
    """Get SharePoint form digest for POST requests."""
    url = f"{site_url}/_api/contextinfo"
    headers = {
        "Accept": "application/json;odata=verbose",
        "Content-Type": "application/json;odata=verbose",
    }
    resp = session.post(url, headers=headers, auth=auth)
    resp.raise_for_status()
    data = resp.json()
    return data["d"]["GetContextWebInformation"]["FormDigestValue"]


def create_list_item(session, site_url, auth, list_name, item_data, digest):
    """Create a single item in a SharePoint list."""
    url = f"{site_url}/_api/web/lists/getbytitle('{list_name}')/items"
    headers = {
        "Accept": "application/json;odata=verbose",
        "Content-Type": "application/json;odata=verbose",
        "X-RequestDigest": digest,
    }
    resp = session.post(url, headers=headers, json=item_data, auth=auth)
    if resp.status_code in (200, 201):
        return resp.json()["d"]
    else:
        print(f"    ERROR {resp.status_code}: {resp.text[:200]}")
        return None


def migrate_people(session, site_url, auth, seats, people, digest):
    """Create People list items from combined seat + sheet1 data."""
    print("\n--- Migrating People ---")
    seen = {}
    for s in seats:
        if s["name"] and s["name"] != "-":
            name = s["name"]
            if name not in seen:
                p = people.get(name, {})
                seen[name] = {
                    "Title": name,
                    "Department": s.get("department") or p.get("department") or "",
                    "JobTitle": p.get("title") or "",
                    "Status": "Active",
                }
    # Also add people from Sheet1 not in seats
    for name, info in people.items():
        if name not in seen:
            seen[name] = {
                "Title": name,
                "Department": info.get("department") or "",
                "JobTitle": info.get("title") or "",
                "Status": "Active",
            }

    created = 0
    for name, data in sorted(seen.items()):
        result = create_list_item(session, site_url, auth, "People", data, digest)
        if result:
            created += 1
            print(f"  + {name}")
    print(f"  Created: {created}/{len(seen)}")
    return created


def migrate_seats(session, site_url, auth, seats, digest):
    """Create Seats list items."""
    print("\n--- Migrating Seats ---")
    created = 0
    for s in seats:
        if not s["name"] or s["name"] == "-":
            continue
        data = {
            "Title": s["seat_no"],
            "PersonName": s["name"],
            "Brigadista": s.get("brigadista") or "",
            "Notas": s.get("notas") or "",
        }
        result = create_list_item(session, site_url, auth, "Seats", data, digest)
        if result:
            created += 1
            print(f"  + Seat #{s['seat_no']} -> {s['name']}")
    print(f"  Created: {created}")
    return created


def main():
    print("=" * 60)
    print("SORTIS - SharePoint Lists Migration")
    print("=" * 60)

    if "YOURSITE" in SHAREPOINT_SITE:
        print("\nERROR: Update SHAREPOINT_SITE in this script first!")
        print("Current value:", SHAREPOINT_SITE)
        sys.exit(1)

    seats, people, brigadistas = read_excel(EXCEL_PATH)

    print(f"\nSharePoint Site: {SHAREPOINT_SITE}")
    print(f"Auth Method: {AUTH_METHOD}")

    session = requests.Session()
    auth = get_auth()

    print("\nGetting form digest...")
    try:
        digest = get_form_digest(session, SHAREPOINT_SITE, auth)
        print(f"  Digest: {digest[:30]}...")
    except Exception as e:
        print(f"\nERROR: Could not connect to SharePoint: {e}")
        print("Make sure you are connected to the corporate network.")
        sys.exit(1)

    migrate_people(session, SHAREPOINT_SITE, auth, seats, people, digest)
    migrate_seats(session, SHAREPOINT_SITE, auth, seats, digest)

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("Next: Update floor_plan.html to use SharePoint Lists API")
    print("=" * 60)


if __name__ == "__main__":
    main()
