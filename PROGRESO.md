# SORTIS - Interactive Office Map Piso 7

## Objective
Create an interactive web app (self-contained HTML/JS) that displays the SORTIS Piso 7 office floor plan, showing person info at each seat on click. Managers can edit assignments and person data from the app. The app is the source of truth (not Excel).

## GitHub
https://github.com/david-arjona-a360/Sortis

## Source Files
- **Excel**: `C:\Users\david.arjona\OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN\SORTIS_FLOOR_PLAN.xlsx`
- **PDF** (analyzed, NOT used): `A02_DISTRIBUCIÓN_OSO (2).pdf`

## Architecture

### Local Mode (no SharePoint)
- `generar_mapa.py` reads Excel → generates JSON + HTML with embedded data
- HTML works with `file://` or any static server

### SharePoint Mode (production)
- HTML is embedded in SharePoint Site Page via Embed web part
- **SharePoint Lists** store all data (People + Seats)
- HTML reads/writes via SharePoint Lists REST API (cookie auth, no Azure AD)
- Changes reflect immediately
- SharePoint handles version history automatically

### Data Architecture
```
Static Data (embedded in HTML):
  - rooms: 26 room definitions with positions
  - seat_positions: 162 seat grid positions

Dynamic Data (loaded from SharePoint Lists):
  - People List: name, department, job title, status
  - Seats List: seat number, person name, brigadista, notes
```

### To activate SharePoint Mode
In `floor_plan.html`, update:
```javascript
var SHAREPOINT_SITE = '/sites/YOURSITE/';
var PEOPLE_LIST = 'People';
var SEATS_LIST = 'Seats';
```

## Excel Structure

### Sheet "Floor plan" (76 rows x 27 columns, A-AA)
Visual grid of the office. Merged cells = rooms/areas. Individual cells = numbered seats 1-167.

**Main areas:**
COMEDOR, RECEPCION, SALA DE REUNIONES, SALA DE ENTRENAMIENTO, OFICINA DE IT, OFICINA GERENCIA 01-06, CUARTO DE IT, ARCHIVE, WAR ROOM, BAÑOS, LOCKERS, CUARTO A/C, CUARTO ELECTRICO, HR162, Supervisors 163-165

### Sheet "Seats Allocation" (176 rows)
Columns: A=Seat No., B=Name, C=Brigadista, D=Notas-Salud, E=Department

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
| `migrate_to_sharepoint.py` | One-time migration: Excel → SharePoint Lists |
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
- [x] Original plan approved and executed
- [x] generar_mapa.py with people_directory, timestamp, brigadistas
- [x] floor_plan.html with edit, SharePoint REST API, brigadista filter
- [x] .gitignore updated
- [x] Departamento column support in Seats Allocation
- [x] SharePoint Lists migration script
- [x] HTML migrated to SharePoint Lists API
- [x] Admin panel with edit person, add person, manage brigadistas
- [ ] Create SharePoint Lists (People, Seats)
- [ ] Run migration script
- [ ] Configure SHAREPOINT_SITE in HTML
- [ ] Test with managers
