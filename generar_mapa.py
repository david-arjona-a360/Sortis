#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lee el archivo Excel SORTIS_FLOOR_PLAN.xlsx y genera:
  1. floor_plan_data.json  (datos completos para referencia)
  2. floor_plan.html       (mapa interactivo autocontenido)
"""

import json
import os
import openpyxl

EXCEL_PATH = r"C:\Users\david.arjona\OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN\SORTIS_FLOOR_PLAN.xlsx"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, "floor_plan_data.json")
HTML_PATH = os.path.join(SCRIPT_DIR, "floor_plan.html")

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
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return str(int(val))
    return str(val).strip()


def read_floor_plan(wb):
    ws = wb["Floor plan"]
    merged_map = {}
    room_cells = []
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

    seat_positions = []
    for row in range(1, GRID_ROWS + 1):
        for col in range(1, GRID_COLS + 1):
            key = (row, col)
            if key in merged_map:
                continue
            val = ws.cell(row, col).value
            if val is not None:
                try:
                    seat_num = int(val)
                    seat_positions.append({
                        "row": row,
                        "col": col,
                        "seat_no": str(seat_num),
                    })
                except (ValueError, TypeError):
                    pass

    return room_cells, seat_positions


def read_seats_allocation(wb):
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
            "name": fix_encoding(str(name).strip()) if name else None,
            "brigadista": fix_encoding(str(brigadista).strip()) if brigadista else None,
            "notas": fix_encoding(str(notas).strip()) if notas else None,
        }
    return seats


def read_sheet1(wb):
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
    result = []
    for sp in seat_positions:
        seat_no = sp["seat_no"]
        info = seats_alloc.get(seat_no, None)
        person = None
        if info and info["name"] and info["name"] != "-":
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


def generate_html(data_json):
    """Generate self-contained HTML with embedded data."""
    return '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SORTIS - Mapa de Oficina Piso 7</title>
<style>
:root {
  --cell-w: 42px;
  --cell-h: 26px;
  --gap: 1px;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: #f5f5f5;
  color: #333;
  overflow: hidden;
  height: 100vh;
}
#topbar {
  background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
  color: #fff;
  padding: 8px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  z-index: 100;
  position: relative;
}
#topbar h1 { font-size: 18px; font-weight: 600; white-space: nowrap; }
#topbar .controls {
  display: flex; align-items: center; gap: 12px;
  flex-wrap: wrap; margin-left: auto;
}
#topbar label { font-size: 12px; opacity: 0.85; }
#topbar select, #topbar input {
  padding: 5px 10px; border: 1px solid rgba(255,255,255,0.3);
  border-radius: 4px; background: rgba(255,255,255,0.15);
  color: #fff; font-size: 13px; outline: none;
}
#topbar select option { color: #333; background: #fff; }
#topbar input::placeholder { color: rgba(255,255,255,0.6); }
#topbar input:focus, #topbar select:focus {
  border-color: rgba(255,255,255,0.7); background: rgba(255,255,255,0.25);
}
#counter {
  font-size: 13px; background: rgba(255,255,255,0.15);
  padding: 4px 12px; border-radius: 12px; white-space: nowrap;
}
#legend {
  background: #fff; padding: 6px 20px;
  display: flex; align-items: center; gap: 12px;
  flex-wrap: wrap; border-bottom: 1px solid #ddd; font-size: 11px;
}
#legend .item { display: flex; align-items: center; gap: 4px; white-space: nowrap; }
#legend .swatch {
  width: 14px; height: 14px; border-radius: 3px;
  border: 1px solid rgba(0,0,0,0.15); flex-shrink: 0;
}
#grid-container {
  overflow: auto; flex: 1;
  height: calc(100vh - 90px); padding: 10px; background: #eee;
}
#grid {
  display: grid;
  grid-template-columns: repeat(''' + str(GRID_COLS) + ''', var(--cell-w));
  grid-template-rows: repeat(''' + str(GRID_ROWS) + ''', var(--cell-h));
  gap: var(--gap);
  width: fit-content;
  margin: 0 auto;
}
.cell {
  border-radius: 2px; display: flex; align-items: center;
  justify-content: center; font-size: 10px; font-weight: 500;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  position: relative; transition: transform 0.1s, box-shadow 0.1s;
}
.cell.empty { background: transparent; border: none; }
.cell.room {
  border: 1px solid rgba(0,0,0,0.12); font-size: 11px;
  font-weight: 600; text-align: center; line-height: 1.2;
  color: #333; padding: 2px 3px;
}
.cell.room.narrow { font-size: 9px; writing-mode: vertical-rl; text-orientation: mixed; }
.cell.seat {
  cursor: pointer; border: 1px solid rgba(0,0,0,0.1);
  font-size: 10px; font-weight: 700; color: #333; z-index: 1;
}
.cell.seat:hover {
  transform: scale(1.3); box-shadow: 0 2px 8px rgba(0,0,0,0.3); z-index: 10;
}
.cell.seat.dimmed {
  opacity: 0.15; transform: none !important; box-shadow: none !important;
}
.cell.seat .seat-label { pointer-events: none; line-height: 1; }
.cell.seat .person-dot {
  position: absolute; bottom: 1px; right: 1px;
  width: 6px; height: 6px; border-radius: 50%;
  background: #4caf50; border: 1px solid #fff;
}
#modal-overlay {
  display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); z-index: 1000;
  justify-content: center; align-items: center;
}
#modal-overlay.active { display: flex; }
#modal {
  background: #fff; border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  max-width: 420px; width: 90%; overflow: hidden;
  animation: modalIn 0.2s ease;
}
@keyframes modalIn { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
#modal-header {
  padding: 16px 20px; background: linear-gradient(135deg, #1a237e, #283593);
  color: #fff; display: flex; justify-content: space-between; align-items: center;
}
#modal-header h2 { font-size: 16px; }
#modal-close {
  background: none; border: none; color: #fff; font-size: 22px;
  cursor: pointer; padding: 0 4px; opacity: 0.8;
}
#modal-close:hover { opacity: 1; }
#modal-body { padding: 20px; }
#modal-body .field { margin-bottom: 12px; }
#modal-body .field-label {
  font-size: 11px; text-transform: uppercase; color: #888;
  letter-spacing: 0.5px; margin-bottom: 2px;
}
#modal-body .field-value { font-size: 14px; color: #222; font-weight: 500; }
#modal-body .field-value.empty { color: #aaa; font-style: italic; }
#modal-body .dept-badge {
  display: inline-block; padding: 3px 10px; border-radius: 12px;
  font-size: 12px; font-weight: 600; margin-top: 2px;
}
#tooltip {
  display: none; position: fixed; background: #333; color: #fff;
  padding: 6px 10px; border-radius: 6px; font-size: 12px;
  pointer-events: none; z-index: 500; white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
#tooltip.visible { display: block; }
</style>
</head>
<body>
<div id="topbar">
  <h1>SORTIS - Mapa de Oficina Piso 7</h1>
  <div class="controls">
    <label>Departamento:</label>
    <select id="filter-dept"><option value="all">Todos</option></select>
    <input type="text" id="search" placeholder="Buscar persona...">
    <span id="counter">Cargando...</span>
  </div>
</div>
<div id="legend"></div>
<div id="grid-container"><div id="grid"></div></div>
<div id="modal-overlay">
  <div id="modal">
    <div id="modal-header">
      <h2 id="modal-title">Detalle del Puesto</h2>
      <button id="modal-close">&times;</button>
    </div>
    <div id="modal-body"></div>
  </div>
</div>
<div id="tooltip"></div>
<script>
const DEPT_COLORS = {
  Finance: '#c8e6c9', IT: '#bbdefb', ENS: '#ffe0b2', Title: '#e1bee7',
  IBC: '#fff9c4', CaseAware: '#f8bbd0', VS360: '#b2dfdb', 'Firm Solutions': '#dcedc8'
};
const ROOM_COLORS = {
  COMEDOR: '#a5d6a7', ARCHIVE: '#bcaaa4', 'CUARTO DE IT': '#81d4fa',
  'BA\\u00d1O DE MUJERES': '#bdbdbd', 'BA\\u00d1O DE HOMBRES': '#bdbdbd',
  LOCKERS: '#cfd8dc', 'SALA DE ENTRENAMIENTO': '#90caf9',
  'SALA DE REUNIONES': '#ce93d8', RECEPCION: '#80cbc4',
  'CUARTO ELECTRICO': '#b0bec5', 'CUARTO DE A/C': '#b0bec5',
  'CUARTO A/C': '#b0bec5', 'OFICINA DE IT': '#b3e5fc',
  'DEPOSITO IT': '#b3e5fc', 'WAR ROOM': '#ef9a9a',
  'OFICINA GERENCIA': '#ffcc80', 'OFICINA DE GERENCIA 03': '#ffab91',
  'OFICINA DE GERENCIA 06': '#ff8a65',
  'HR162': '#a1887f', Supervisor: '#ffe082'
};

const DATA = ''' + data_json + ''';

function getDeptColor(d) { return d && DEPT_COLORS[d] ? DEPT_COLORS[d] : '#e0e0e0'; }

function getRoomColor(name) {
  if (!name) return '#ddd';
  var n = name.trim();
  for (var k in ROOM_COLORS) {
    if (n.indexOf(k) >= 0) return ROOM_COLORS[k];
  }
  return '#e0e0e0';
}

(function buildGrid() {
  var grid = document.getElementById('grid');
  var seatMap = {};
  DATA.seats.forEach(function(s) { seatMap[s.row + ',' + s.col] = s; });

  var roomOrigin = {};
  var covered = {};
  DATA.rooms.forEach(function(r) {
    roomOrigin[r.min_row + ',' + r.min_col] = r;
    for (var rr = r.min_row; rr <= r.max_row; rr++) {
      for (var cc = r.min_col; cc <= r.max_col; cc++) {
        if (rr !== r.min_row || cc !== r.min_col) covered[rr + ',' + cc] = 1;
      }
    }
  });

  for (var row = 1; row <= 76; row++) {
    for (var col = 1; col <= 27; col++) {
      var key = row + ',' + col;
      var d = document.createElement('div');
      d.className = 'cell';

      var origin = roomOrigin[key];
      if (origin) {
        d.className += ' room';
        d.style.background = getRoomColor(origin.name);
        d.style.gridRow = origin.min_row + '/' + (origin.max_row + 1);
        d.style.gridColumn = origin.min_col + '/' + (origin.max_col + 1);
        var w = origin.max_col - origin.min_col + 1;
        var h = origin.max_row - origin.min_row + 1;
        if (w <= 2 && h <= 3) d.className += ' narrow';
        d.textContent = (origin.name || '').trim();
        d.title = (origin.name || '').trim();
        grid.appendChild(d);
        continue;
      }
      if (covered[key]) {
        d.className += ' empty';
        d.style.gridRow = row;
        d.style.gridColumn = col;
        grid.appendChild(d);
        continue;
      }

      var seat = seatMap[key];
      if (seat) {
        var dept = seat.person ? seat.person.department : null;
        d.className += ' seat';
        d.style.background = getDeptColor(dept);
        d.style.gridRow = row;
        d.style.gridColumn = col;
        var lbl = document.createElement('span');
        lbl.className = 'seat-label';
        lbl.textContent = seat.seat_no;
        d.appendChild(lbl);
        if (seat.person) {
          var dot = document.createElement('span');
          dot.className = 'person-dot';
          d.appendChild(dot);
        }
        d.addEventListener('click', (function(s) {
          return function() { showModal(s); };
        })(seat));
        d.addEventListener('mouseenter', (function(s) {
          return function(e) { showTooltip(e, s); };
        })(seat));
        d.addEventListener('mousemove', moveTooltip);
        d.addEventListener('mouseleave', hideTooltip);
        grid.appendChild(d);
        continue;
      }

      d.className += ' empty';
      d.style.gridRow = row;
      d.style.gridColumn = col;
      grid.appendChild(d);
    }
  }
})();

function showModal(seat) {
  var overlay = document.getElementById('modal-overlay');
  var body = document.getElementById('modal-body');
  document.getElementById('modal-title').textContent = 'Puesto #' + seat.seat_no;
  var h = '';
  var p = seat.person;
  if (p && p.name) {
    var dept = p.department || 'Sin departamento';
    var dc = getDeptColor(p.department);
    h += fl('Nombre', p.name);
    h += fl('Departamento', dept, '<span class="dept-badge" style="background:' + dc + '">' + dept + '</span>');
    h += fl('Cargo / T\\u00edtulo', p.title);
    h += fl('Brigadista', seat.brigadista || (p ? p.brigadista : ''));
    h += fl('Notas de Salud', p.notas);
  } else {
    h += fl('Estado', 'Sin asignar', '<span style="color:#aaa;font-style:italic">Puesto vac\\u00edo</span>');
    if (seat.brigadista) h += fl('Brigadista', seat.brigadista);
  }
  h += fl('Puesto', seat.seat_no);
  h += fl('Ubicaci\\u00f3n', 'Fila ' + seat.row + ', Columna ' + seat.col);
  body.innerHTML = h;
  overlay.classList.add('active');
}

function fl(label, value, custom) {
  var empty = !value || value === 'null';
  var v = custom || (empty ? 'No disponible' : value);
  return '<div class="field"><div class="field-label">' + label + '</div><div class="field-value' + (empty ? ' empty' : '') + '">' + v + '</div></div>';
}

function showTooltip(e, seat) {
  var t = document.getElementById('tooltip');
  var txt = 'Puesto #' + seat.seat_no;
  if (seat.person && seat.person.name) {
    txt += ' - ' + seat.person.name;
    if (seat.person.department) txt += ' (' + seat.person.department + ')';
  }
  t.textContent = txt;
  t.classList.add('visible');
  moveTooltip(e);
}
function moveTooltip(e) {
  var t = document.getElementById('tooltip');
  t.style.left = (e.clientX + 12) + 'px';
  t.style.top = (e.clientY - 30) + 'px';
}
function hideTooltip() { document.getElementById('tooltip').classList.remove('visible'); }

var sel = document.getElementById('filter-dept');
DATA.departments.forEach(function(d) {
  var o = document.createElement('option');
  o.value = d; o.textContent = d;
  sel.appendChild(o);
});

var leg = document.getElementById('legend');
var lh = '<span style="font-weight:600;color:#555">Departamentos:</span>';
DATA.departments.forEach(function(d) {
  lh += '<span class="item"><span class="swatch" style="background:' + getDeptColor(d) + '"></span>' + d + '</span>';
});
lh += '<span class="item"><span class="swatch" style="background:#e0e0e0"></span>Sin asignar</span>';
leg.innerHTML = lh;

function applyFilters() {
  var seats = document.querySelectorAll('.cell.seat');
  var visible = 0;
  var filter = document.getElementById('filter-dept').value;
  var search = document.getElementById('search').value.toLowerCase();
  seats.forEach(function(d) {
    var dept = d.querySelector('.person-dot') ? '' : '';
    var seatNo = d.querySelector('.seat-label').textContent;
    var show = true;
    if (filter !== 'all') {
      var s = null;
      DATA.seats.forEach(function(x) { if (x.seat_no === seatNo) s = x; });
      if (s && s.person && s.person.department !== filter) show = false;
      if (s && !s.person && filter !== 'all') show = false;
    }
    if (search) {
      var s2 = null;
      DATA.seats.forEach(function(x) { if (x.seat_no === seatNo) s2 = x; });
      if (s2 && s2.person && s2.person.name && s2.person.name.toLowerCase().indexOf(search) >= 0) {}
      else if (s2 && s2.brigadista && s2.brigadista.toLowerCase().indexOf(search) >= 0) {}
      else show = false;
    }
    if (show) { d.classList.remove('dimmed'); visible++; }
    else d.classList.add('dimmed');
  });
  document.getElementById('counter').textContent = 'Mostrando ' + visible + ' de ' + DATA.total_seats + ' puestos';
}

document.getElementById('filter-dept').addEventListener('change', applyFilters);
document.getElementById('search').addEventListener('input', applyFilters);
document.getElementById('modal-close').addEventListener('click', function() {
  document.getElementById('modal-overlay').classList.remove('active');
});
document.getElementById('modal-overlay').addEventListener('click', function(e) {
  if (e.target === e.currentTarget) e.currentTarget.classList.remove('active');
});
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') document.getElementById('modal-overlay').classList.remove('active');
});

applyFilters();
</script>
</body>
</html>'''


def main():
    print(f"Leyendo: {EXCEL_PATH}")
    wb = openpyxl.load_workbook(EXCEL_PATH)

    print("Parseando plano...")
    room_cells, seat_positions = read_floor_plan(wb)
    print(f"  Salas: {len(room_cells)}, Puestos en plano: {len(seat_positions)}")

    print("Parseando asignacion...")
    seats_alloc = read_seats_allocation(wb)
    print(f"  Registros: {len(seats_alloc)}")

    print("Parseando personas...")
    people = read_sheet1(wb)
    print(f"  Personas: {len(people)}")

    seats_with_people = join_data(seat_positions, seats_alloc, people)
    occupied = sum(1 for s in seats_with_people if s["person"] is not None)
    print(f"  Ocupados: {occupied}/{len(seats_with_people)}")

    departments = set()
    for s in seats_with_people:
        if s["person"] and s["person"]["department"]:
            departments.add(s["person"]["department"])

    output = {
        "rooms": room_cells,
        "seats": seats_with_people,
        "departments": sorted(departments),
        "total_seats": len(seats_with_people),
        "occupied_seats": occupied,
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nJSON: {JSON_PATH} ({os.path.getsize(JSON_PATH):,} bytes)")

    data_json = json.dumps(output, ensure_ascii=False)
    html = generate_html(data_json)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML: {HTML_PATH} ({os.path.getsize(HTML_PATH):,} bytes)")


if __name__ == "__main__":
    main()
