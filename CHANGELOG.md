# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-07-23

### Added
- **Departamento column support**: `generar_mapa.py` now reads column E (Departamento) from Seats Allocation sheet, prioritizing it over Sheet1 data
- **SharePoint Lists migration script** (`migrate_to_sharepoint.py`): One-time script to populate SharePoint Lists from Excel
- **SharePoint Lists API integration**: HTML now reads/writes to SharePoint Lists (People, Seats) instead of JSON file
- **Admin panel**: Hidden admin UI accessible via `?admin=true` URL parameter
  - Edit Person modal (name, department, job title)
  - Add New Person modal
  - Manage Brigadistas modal (add/remove)
- **Static data separation**: Room layouts and seat positions are now embedded as static data (never changes), while people/assignments are loaded dynamically

### Changed
- **Data architecture**: Migrated from single JSON file to SharePoint Lists (People + Seats)
- **HTML structure**: Split static data (rooms, seat_positions) from dynamic data (people, assignments)
- **SharePoint integration**: Replaced file-based REST API with Lists REST API (CRUD operations)

### Removed
- **JSON file dependency**: No longer reads/writes `data.json` in SharePoint mode

### Migration Steps
1. Add column E "Departamento" to Seats Allocation sheet in Excel
2. Create SharePoint Lists "People" and "Seats" (see README)
3. Run `python migrate_to_sharepoint.py` (one-time)
4. Update `SHAREPOINT_SITE` in `floor_plan.html`
5. Re-run `python generar_mapa.py`
6. Embed HTML in SharePoint Site Page

### SharePoint Lists Schema

**People List:**
| Column | Type | Description |
|--------|------|-------------|
| Title | Single line of text | Person's full name |
| Department | Choice | Finance, IT, ENS, Title, IBC, CaseAware, VS360, Firm Solutions |
| JobTitle | Single line of text | Job title/position |
| Status | Choice | Active, Inactive |

**Seats List:**
| Column | Type | Description |
|--------|------|-------------|
| Title | Single line of text | Seat number |
| PersonName | Single line of text | Assigned person's name |
| Brigadista | Single line of text | Emergency brigadista |
| Notas | Multiple lines of text | Health notes |

### Admin Features
- Access admin panel: Append `?admin=true` to URL
- Edit person: Click seat → click "Edit Person" button (admin only)
- Add person: Click "+ Add Person" in admin panel
- Manage brigadistas: Click "Manage Brigadistas" in admin panel

## [0.1.0] - 2026-07-23

### Added
- Initial release
- Interactive floor plan grid (76x27)
- Department color coding
- Seat assignment/reassignment
- SharePoint JSON file integration
- Brigadista filter
- Search by name/department
- Auto-save to SharePoint
