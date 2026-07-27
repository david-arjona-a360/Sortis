# SORTIS - Interactive Office Map Piso 7

## Objective
Create an interactive web app (self-contained HTML/JS) that displays the SORTIS Piso 7 office floor plan, showing person info at each seat on click. Managers can edit assignments and person data from the app. Excel is the source of truth — user edits Excel, runs `python generar_mapa.py`, uploads to SharePoint.

## GitHub
https://github.com/david-arjona-a360/Sortis

## Source Files
- **Excel (local copy)**: `C:\PY_projects\SORTIS\SORTIS_FLOOR_PLAN.xlsx` (copy of OneDrive original)
- **Excel (OneDrive original)**: `C:\Users\david.arjona\OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN\SORTIS_FLOOR_PLAN.xlsx` (do NOT edit directly)
- **PDF** (analyzed, NOT used): `A02_DISTRIBUCIÓN_OSO (2).pdf`

## Architecture

### Single-Source Model (current)
- **Excel is the source of truth** — user edits Excel, runs `python generar_mapa.py`
- `generar_mapa.py` reads Excel → generates JSON + HTML with embedded data
- HTML works with `file://`, SharePoint, or any static server
- To update data: edit Excel → run `python generar_mapa.py` → upload to SharePoint

### Data Architecture
```
Excel Sheets:
  Floor Plan        → Room definitions + seat grid positions (static)
  Seats Allocation  → Person assignments, department, title, brigadista, notas (single source of truth)
  Brigadistas       → Brigadista names (backup, also read from Seats Allocation)

Static Data (embedded in HTML):
  - rooms: 25 room definitions with positions
  - seat_positions: 162 seat grid positions

Dynamic Data (embedded in HTML):
  - seats: array of seats with assigned people
  - departments: list of unique departments
  - brigadistas: list of unique brigadistas
  - people_directory: directory of all persons (name, dept, title)
```

Admin Mode (`?admin=true`):
  - Edit person data (name, department, title, notes)
  - Add new person to empty seat
  - Manage brigadistas (add/remove)
  - Draw/edit/delete rooms on the floor plan
  - Customize department colors (localStorage)
  - Data saved to HTML (regenerate from Excel to reset)

## Excel Structure

### Sheet "Floor plan" (76 rows x 27 columns, A-AA)
Visual grid of the office. Merged cells = rooms/areas. Individual cells = numbered seats 1-167.

**Main areas:**
COMEDOR, RECEPCION, SALA DE REUNIONES, SALA DE ENTRENAMIENTO, OFICINA DE IT, OFICINA GERENCIA 01-06, CUARTO DE IT, ARCHIVE, WAR ROOM, BAÑOS, LOCKERS, CUARTO A/C, CUARTO ELECTRICO, HR162, Supervisors 163-165

### Sheet "Seats Allocation" (210 rows)
Columns: A=Seat No., B=Name, C=Brigadista, D=Notas-Salud, E=Department, F=Title

### Sheet "Sheet1" (47 rows)
Columns: A=Name, B=Department, C=Title
Departments: Finance, IT, ENS, Title, IBC, CaseAware, VS360, Firm Solutions

### Sheet "Brigadistas" (13 rows)
Columns: A=Seat No, B=Nombre, C=Departamento

## Features

### Visualization
- CSS Grid 27x76 replicates Excel layout
- Department color coding
- Tooltip on hover with name + department
- Modal on click with full info
- Filter by department, brigadista, and name search
- Counter: displayed / occupied / empty seats

### Editing (SharePoint mode)
- Click empty seat → autocomplete dropdown to assign person
- Click occupied seat → info + "Reassign" and "Unassign" buttons
- Confirmation before unassigning
- Auto-save every 2 seconds after change
- Toast notifications for feedback
- Timestamp of last update visible

### Admin Features (URL: `?admin=true`)
- Admin panel with "Add Person" and "Manage Brigadistas" buttons
- Edit Person modal: name, department, job title
- Add New Person modal: creates person in People directory
- Manage Brigadistas modal: add/remove brigadistas

### SharePoint Lists Integration
- **People List**: CRUD operations for person data
- **Seats List**: CRUD operations for seat assignments
- Reads on page load, writes on auto-save
- "Connected to SharePoint" indicator in topbar
- Falls back to local data if SharePoint unavailable
- Uses cookie auth (no Azure AD app registration)

## Data Displayed per Seat
| Field | Source |
|-------|--------|
| Name | Seats List → PersonName |
| Department | People List → Department |
| Job Title | People List → JobTitle |
| Brigadista | Seats List → Brigadista |
| Notes | Seats List → Notas |

## Files
| File | Description |
|------|-------------|
| `generar_mapa.py` | Reads Excel, generates JSON + HTML |
| `floor_plan.html` | Interactive map (auto-generated) |
| `compare_grid.py` | Data verification script |
| `.gitignore` | Excludes JSON, xlsx, cache |
| `CHANGELOG.md` | Version history |
| `PROGRESO.md` | This document |

## Generated Data (in HTML)
- rooms: array of room definitions with positions (static)
- seat_positions: array of seat grid positions (static)
- seats: array of seats with assigned people (dynamic)
- departments: list of unique departments
- brigadistas: list of unique brigadistas
- people_directory: directory of all persons (name, dept, title)
- total_seats: total number of seats
- occupied_seats: occupied seats count
- timestamp: last generation date/time

## Status
- [x] Complete Excel analysis (4 sheets, merged cells, colors, positions)
- [x] PDF analysis (concluded: structural blueprint, not usable)
- [x] generar_mapa.py with people_directory, timestamp, brigadistas
- [x] floor_plan.html with edit, brigadista filter
- [x] .gitignore updated
- [x] Departamento column support in Seats Allocation
- [x] Title column (F) in Seats Allocation
- [x] Admin panel with edit person, add person, manage brigadistas
- [x] Single-source model: Seats Allocation only (Sheet1 eliminated)
- [x] Room editor (draw/edit/delete rooms)
- [x] Department color customization
- [x] Auto-detect grid dimensions from Excel
- [x] Deploy folder for SharePoint
- [x] SharePoint Lists integration removed (simplified)
- [ ] Test with managers
- [ ] Upload to SharePoint
