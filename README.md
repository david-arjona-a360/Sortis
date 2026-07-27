# SORTIS Floor Plan

Self-contained HTML/JS floor plan generator for SORTIS Piso 7. Reads Excel data (PTY Users + seat assignments), generates an interactive map with drag-and-drop room editing, department colors, and admin panel. Deploy to SharePoint or run locally.

## Features
- Interactive floor plan with 25 rooms and 162 seats
- Click any seat to view person info (name, department, title, email)
- Admin panel (`?admin=true`) for editing seat assignments
- Drag-and-drop room editor (admin mode)
- Department color customization
- Brigadista management
- Auto-syncs with HR's PTY Users & Roles.xlsx

## How It Works
1. HR updates `PTY Users & Roles.xlsx` (people join/leave)
2. Run `python generar_mapa.py` (reads both Excel files)
3. Open `floor_plan.html` in browser
4. Assign people to seats from the directory

## Data Sources
| Source | Content |
|--------|---------|
| `PTY Users & Roles.xlsx` | Person data (name, title, department, email) |
| `SORTIS_FLOOR_PLAN.xlsx` | Seat assignments + floor plan layout |

## Deployment
Upload `deploy/floor_plan.html` to SharePoint or host on any static server.
