#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lee el archivo Excel SORTIS_FLOOR_PLAN.xlsx y genera:
  1. floor_plan_data.json  (datos completos para referencia)
  2. floor_plan.html       (mapa interactivo autocontenido con SharePoint + edicion)
"""

import json
import os
from datetime import datetime
import openpyxl

EXCEL_PATH = r"C:\Users\david.arjona\OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN\SORTIS_FLOOR_PLAN.xlsx"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, "floor_plan_data.json")
HTML_PATH = os.path.join(SCRIPT_DIR, "floor_plan.html")

GRID_ROWS = 76
GRID_COLS = 27


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


def build_people_directory(seats_with_people, people_sheet):
    seen = {}
    for s in seats_with_people:
        if s["person"] and s["person"]["name"]:
            name = s["person"]["name"]
            if name not in seen:
                seen[name] = {
                    "name": name,
                    "department": s["person"].get("department"),
                    "title": s["person"].get("title"),
                }
    for name, info in people_sheet.items():
        if name not in seen:
            seen[name] = {
                "name": name,
                "department": info.get("department"),
                "title": info.get("title"),
            }
    return sorted(seen.values(), key=lambda x: x["name"])


def build_brigadistas(seats_with_people):
    brig = {}
    for s in seats_with_people:
        b = s.get("brigadista")
        if b:
            if b not in brig:
                brig[b] = 0
            brig[b] += 1
    return sorted(brig.keys())


def generate_html(data_json):
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
  display: flex; align-items: center; gap: 10px;
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
  font-size: 12px; background: rgba(255,255,255,0.15);
  padding: 4px 12px; border-radius: 12px; white-space: nowrap;
}
#sp-status {
  font-size: 11px; padding: 3px 8px; border-radius: 8px;
  background: rgba(76,175,80,0.3); border: 1px solid rgba(76,175,80,0.5);
  white-space: nowrap; display: none;
}
#sp-status.connected { display: inline-block; }
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
  max-width: 480px; width: 92%; overflow: hidden;
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
#modal-body { padding: 20px; max-height: 60vh; overflow-y: auto; }
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
.modal-actions {
  display: flex; gap: 10px; margin-top: 16px; padding-top: 16px;
  border-top: 1px solid #eee;
}
.btn {
  padding: 8px 16px; border-radius: 6px; font-size: 13px;
  font-weight: 600; cursor: pointer; border: none; transition: all 0.15s;
}
.btn-primary { background: #1a237e; color: #fff; }
.btn-primary:hover { background: #283593; }
.btn-danger { background: #c62828; color: #fff; }
.btn-danger:hover { background: #b71c1c; }
.btn-secondary { background: #e0e0e0; color: #333; }
.btn-secondary:hover { background: #bdbdbd; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.autocomplete-wrap { position: relative; }
.autocomplete-input {
  width: 100%; padding: 10px 12px; border: 2px solid #ddd;
  border-radius: 6px; font-size: 14px; outline: none;
}
.autocomplete-input:focus { border-color: #1a237e; }
.autocomplete-list {
  position: absolute; top: 100%; left: 0; right: 0;
  background: #fff; border: 1px solid #ddd; border-radius: 0 0 6px 6px;
  max-height: 200px; overflow-y: auto; z-index: 10;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: none;
}
.autocomplete-list.open { display: block; }
.autocomplete-item {
  padding: 8px 12px; cursor: pointer; font-size: 13px;
  border-bottom: 1px solid #f0f0f0;
}
.autocomplete-item:hover { background: #e8eaf6; }
.autocomplete-item .ac-dept {
  font-size: 11px; color: #888; margin-left: 6px;
}
.autocomplete-item.selected { background: #c5cae9; font-weight: 600; }
#confirm-overlay {
  display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4); z-index: 2000;
  justify-content: center; align-items: center;
}
#confirm-overlay.active { display: flex; }
#confirm-box {
  background: #fff; border-radius: 10px; padding: 24px;
  max-width: 360px; width: 90%; text-align: center;
  box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}
#confirm-box h3 { margin-bottom: 12px; font-size: 16px; }
#confirm-box p { margin-bottom: 20px; color: #666; font-size: 14px; }
#confirm-box .modal-actions { justify-content: center; border: none; padding: 0; }
#toast {
  position: fixed; bottom: 20px; right: 20px; padding: 12px 20px;
  border-radius: 8px; font-size: 13px; font-weight: 500;
  z-index: 3000; transform: translateY(100px); opacity: 0;
  transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
#toast.show { transform: translateY(0); opacity: 1; }
#toast.success { background: #2e7d32; color: #fff; }
#toast.error { background: #c62828; color: #fff; }
#toast.info { background: #1565c0; color: #fff; }
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
    <label>Brigadista:</label>
    <select id="filter-brig"><option value="all">Todos</option></select>
    <input type="text" id="search" placeholder="Buscar persona...">
    <span id="counter">Cargando...</span>
    <span id="sp-status" class="connected">Conectado a SharePoint</span>
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
<div id="confirm-overlay">
  <div id="confirm-box">
    <h3 id="confirm-title">Confirmar</h3>
    <p id="confirm-msg"></p>
    <div class="modal-actions">
      <button class="btn btn-secondary" id="confirm-cancel">Cancelar</button>
      <button class="btn btn-danger" id="confirm-ok">Confirmar</button>
    </div>
  </div>
</div>
<div id="toast"></div>
<div id="tooltip"></div>
<script>
var DEPT_COLORS = {
  Finance: '#c8e6c9', IT: '#bbdefb', ENS: '#ffe0b2', Title: '#e1bee7',
  IBC: '#fff9c4', CaseAware: '#f8bbd0', VS360: '#b2dfdb', 'Firm Solutions': '#dcedc8'
};
var ROOM_COLORS = {
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

var SHAREPOINT_SITE = '';
var DATA_FILE_PATH = '/sites/YOURSITE/Shared Documents/FloorPlan/data.json';

var DATA = ''' + data_json + ''';
var LOCAL_DATA = JSON.parse(JSON.stringify(DATA));
var isSharePoint = SHAREPOINT_SITE.length > 0;
var hasChanges = false;

function getDeptColor(d) { return d && DEPT_COLORS[d] ? DEPT_COLORS[d] : '#e0e0e0'; }
function getRoomColor(name) {
  if (!name) return '#ddd';
  var n = name.trim();
  for (var k in ROOM_COLORS) {
    if (n.indexOf(k) >= 0) return ROOM_COLORS[k];
  }
  return '#e0e0e0';
}

function toast(msg, type) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show ' + (type || 'info');
  setTimeout(function() { t.className = ''; }, 3000);
}

function getSeatByNo(no) {
  for (var i = 0; i < LOCAL_DATA.seats.length; i++) {
    if (LOCAL_DATA.seats[i].seat_no === no) return LOCAL_DATA.seats[i];
  }
  return null;
}

function getSeatByRC(r, c) {
  for (var i = 0; i < LOCAL_DATA.seats.length; i++) {
    if (LOCAL_DATA.seats[i].row === r && LOCAL_DATA.seats[i].col === c) return LOCAL_DATA.seats[i];
  }
  return null;
}

function refreshGrid() {
  var grid = document.getElementById('grid');
  grid.innerHTML = '';
  buildGrid();
  applyFilters();
  updateCounter();
}

function buildGrid() {
  var grid = document.getElementById('grid');
  var seatMap = {};
  LOCAL_DATA.seats.forEach(function(s) { seatMap[s.row + ',' + s.col] = s; });
  var roomOrigin = {};
  var covered = {};
  LOCAL_DATA.rooms.forEach(function(r) {
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
}

function showModal(seat) {
  var overlay = document.getElementById('modal-overlay');
  var body = document.getElementById('modal-body');
  document.getElementById('modal-title').textContent = 'Puesto #' + seat.seat_no;
  var p = seat.person;
  var h = '';
  if (p && p.name) {
    var dept = p.department || 'Sin departamento';
    var dc = getDeptColor(p.department);
    h += fl('Nombre', p.name);
    h += fl('Departamento', dept, '<span class="dept-badge" style="background:' + dc + '">' + dept + '</span>');
    h += fl('Cargo / T\\u00edtulo', p.title);
    h += fl('Brigadista', seat.brigadista || (p ? p.brigadista : ''));
    h += fl('Notas de Salud', p.notas);
    h += '<div class="modal-actions">';
    h += '<button class="btn btn-primary" onclick="startReassign(\\'' + seat.seat_no + '\\')">Reasignar</button>';
    h += '<button class="btn btn-danger" onclick="confirmUnassign(\\'' + seat.seat_no + '\\')">Desasignar</button>';
    h += '</div>';
  } else {
    h += fl('Estado', 'Sin asignar', '<span style="color:#aaa;font-style:italic">Puesto vac\\u00edo</span>');
    if (seat.brigadista) h += fl('Brigadista', seat.brigadista);
    h += '<div class="modal-actions">';
    h += '<button class="btn btn-primary" onclick="startAssign(\\'' + seat.seat_no + '\\')">Asignar Persona</button>';
    h += '</div>';
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

function startAssign(seatNo) {
  document.getElementById('modal-overlay').classList.remove('active');
  var body = document.getElementById('modal-body');
  document.getElementById('modal-title').textContent = 'Asignar Puesto #' + seatNo;
  var h = '<div class="field"><div class="field-label">Seleccionar Persona</div>';
  h += '<div class="autocomplete-wrap">';
  h += '<input type="text" class="autocomplete-input" id="ac-input" placeholder="Escriba nombre para buscar..." autocomplete="off">';
  h += '<div class="autocomplete-list" id="ac-list"></div>';
  h += '</div></div>';
  h += '<div class="modal-actions">';
  h += '<button class="btn btn-secondary" onclick="closeModal()">Cancelar</button>';
  h += '<button class="btn btn-primary" id="btn-save-assign" disabled onclick="saveAssign(\\'' + seatNo + '\\')">Guardar</button>';
  h += '</div>';
  body.innerHTML = h;
  document.getElementById('modal-overlay').classList.add('active');
  setupAutocomplete(seatNo, false);
}

function startReassign(seatNo) {
  document.getElementById('modal-overlay').classList.remove('active');
  var body = document.getElementById('modal-body');
  document.getElementById('modal-title').textContent = 'Reasignar Puesto #' + seatNo;
  var h = '<div class="field"><div class="field-label">Nueva Persona</div>';
  h += '<div class="autocomplete-wrap">';
  h += '<input type="text" class="autocomplete-input" id="ac-input" placeholder="Escriba nombre para buscar..." autocomplete="off">';
  h += '<div class="autocomplete-list" id="ac-list"></div>';
  h += '</div></div>';
  h += '<div class="modal-actions">';
  h += '<button class="btn btn-secondary" onclick="closeModal()">Cancelar</button>';
  h += '<button class="btn btn-primary" id="btn-save-assign" disabled onclick="saveAssign(\\'' + seatNo + '\\')">Guardar</button>';
  h += '</div>';
  body.innerHTML = h;
  document.getElementById('modal-overlay').classList.add('active');
  setupAutocomplete(seatNo, true);
}

var selectedPerson = null;

function setupAutocomplete(seatNo, isReassign) {
  selectedPerson = null;
  var input = document.getElementById('ac-input');
  var list = document.getElementById('ac-list');
  var btn = document.getElementById('btn-save-assign');
  input.focus();

  function renderList(filter) {
    var html = '';
    var people = LOCAL_DATA.people_directory || [];
    var count = 0;
    for (var i = 0; i < people.length && count < 30; i++) {
      var p = people[i];
      if (filter && p.name.toLowerCase().indexOf(filter.toLowerCase()) < 0) continue;
      var dept = p.department || '';
      html += '<div class="autocomplete-item" data-name="' + p.name.replace(/"/g, '&quot;') + '">';
      html += p.name;
      if (dept) html += '<span class="ac-dept">' + dept + '</span>';
      html += '</div>';
      count++;
    }
    if (count === 0) html = '<div class="autocomplete-item" style="color:#999">No se encontraron resultados</div>';
    list.innerHTML = html;
    list.classList.add('open');

    var items = list.querySelectorAll('.autocomplete-item[data-name]');
    items.forEach(function(item) {
      item.addEventListener('click', function() {
        selectedPerson = this.getAttribute('data-name');
        input.value = selectedPerson;
        list.classList.remove('open');
        btn.disabled = false;
        items.forEach(function(i2) { i2.classList.remove('selected'); });
        this.classList.add('selected');
      });
    });
  }

  input.addEventListener('input', function() {
    selectedPerson = null;
    btn.disabled = true;
    renderList(this.value);
  });
  input.addEventListener('focus', function() { renderList(this.value); });
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.autocomplete-wrap')) list.classList.remove('open');
  });
}

function saveAssign(seatNo) {
  if (!selectedPerson) return;
  var seat = getSeatByNo(seatNo);
  if (!seat) return;
  var brig = seat.brigadista;
  seat.person = {
    name: selectedPerson,
    brigadista: brig,
    notas: null,
    department: null,
    title: null
  };
  var pd = LOCAL_DATA.people_directory || [];
  for (var i = 0; i < pd.length; i++) {
    if (pd[i].name === selectedPerson) {
      seat.person.department = pd[i].department;
      seat.person.title = pd[i].title;
      break;
    }
  }
  hasChanges = true;
  closeModal();
  refreshGrid();
  toast('Puesto #' + seatNo + ' asignado a ' + selectedPerson, 'success');
  autoSave();
}

function confirmUnassign(seatNo) {
  var seat = getSeatByNo(seatNo);
  if (!seat || !seat.person) return;
  var name = seat.person.name;
  document.getElementById('modal-overlay').classList.remove('active');
  document.getElementById('confirm-title').textContent = 'Desasignar Puesto #' + seatNo;
  document.getElementById('confirm-msg').textContent = 'Remover a ' + name + ' del puesto #' + seatNo + '?';
  document.getElementById('confirm-overlay').classList.add('active');
  document.getElementById('confirm-ok').onclick = function() {
    doUnassign(seatNo);
    document.getElementById('confirm-overlay').classList.remove('active');
  };
  document.getElementById('confirm-cancel').onclick = function() {
    document.getElementById('confirm-overlay').classList.remove('active');
  };
}

function doUnassign(seatNo) {
  var seat = getSeatByNo(seatNo);
  if (!seat) return;
  seat.person = null;
  hasChanges = true;
  refreshGrid();
  toast('Puesto #' + seatNo + ' desasignado', 'info');
  autoSave();
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('active');
}

var saveTimeout = null;
function autoSave() {
  if (!isSharePoint) return;
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(function() { saveToSharePoint(); }, 2000);
}

function saveToSharePoint() {
  if (!isSharePoint) return;
  LOCAL_DATA.timestamp = new Date().toISOString();
  var url = SHAREPOINT_SITE + "_api/web/GetFileByServerRelativeUrl('" + DATA_FILE_PATH + "')/$value";
  var digest = document.querySelector('#__REQUESTDIGEST');
  var digestVal = digest ? digest.value : '';
  fetch(url, {
    method: 'POST',
    headers: {
      'X-RequestDigest': digestVal,
      'Content-Type': 'application/json',
      'IF-MATCH': '*',
      'X-HTTP-Method': 'MERGE'
    },
    body: JSON.stringify(LOCAL_DATA)
  }).then(function(r) {
    if (r.ok) {
      toast('Cambios guardados en SharePoint', 'success');
      document.getElementById('sp-timestamp').textContent = 'Actualizado: ' + new Date().toLocaleString('es-PA');
    } else {
      toast('Error al guardar en SharePoint', 'error');
    }
  }).catch(function() {
    toast('Error de conexion con SharePoint', 'error');
  });
}

function loadFromSharePoint() {
  if (!isSharePoint) return;
  var url = SHAREPOINT_SITE + "_api/web/GetFileByServerRelativeUrl('" + DATA_FILE_PATH + "')/$value";
  fetch(url).then(function(r) { return r.json(); }).then(function(data) {
    LOCAL_DATA = data;
    refreshGrid();
    if (data.timestamp) {
      document.getElementById('sp-timestamp').textContent = 'Actualizado: ' + new Date(data.timestamp).toLocaleString('es-PA');
    }
    toast('Datos cargados desde SharePoint', 'success');
  }).catch(function() {
    toast('No se pudo conectar a SharePoint, usando datos locales', 'info');
  });
}

function updateCounter() {
  var total = LOCAL_DATA.seats.length;
  var occupied = 0;
  LOCAL_DATA.seats.forEach(function(s) { if (s.person) occupied++; });
  var visible = document.querySelectorAll('.cell.seat:not(.dimmed)').length;
  document.getElementById('counter').textContent = visible + ' de ' + total + ' | Ocupados: ' + occupied + ' | Vac\\u00edos: ' + (total - occupied);
}

function applyFilters() {
  var seats = document.querySelectorAll('.cell.seat');
  var filterDept = document.getElementById('filter-dept').value;
  var filterBrig = document.getElementById('filter-brig').value;
  var search = document.getElementById('search').value.toLowerCase();
  seats.forEach(function(d) {
    var seatNo = d.querySelector('.seat-label').textContent;
    var s = getSeatByNo(seatNo);
    var show = true;
    if (filterDept !== 'all') {
      if (s && s.person && s.person.department !== filterDept) show = false;
      if (s && !s.person) show = false;
    }
    if (filterBrig !== 'all') {
      if (s && s.brigadista !== filterBrig) show = false;
    }
    if (search) {
      var found = false;
      if (s && s.person && s.person.name && s.person.name.toLowerCase().indexOf(search) >= 0) found = true;
      if (s && s.person && s.person.department && s.person.department.toLowerCase().indexOf(search) >= 0) found = true;
      if (s && s.brigadista && s.brigadista.toLowerCase().indexOf(search) >= 0) found = true;
      if (!found) show = false;
    }
    if (show) d.classList.remove('dimmed');
    else d.classList.add('dimmed');
  });
  updateCounter();
}

function initFilters() {
  var selDept = document.getElementById('filter-dept');
  LOCAL_DATA.departments.forEach(function(d) {
    var o = document.createElement('option');
    o.value = d; o.textContent = d;
    selDept.appendChild(o);
  });
  var selBrig = document.getElementById('filter-brig');
  var brigadistas = LOCAL_DATA.brigadistas || [];
  brigadistas.forEach(function(b) {
    var o = document.createElement('option');
    o.value = b; o.textContent = b;
    selBrig.appendChild(o);
  });
  selDept.addEventListener('change', applyFilters);
  selBrig.addEventListener('change', applyFilters);
  document.getElementById('search').addEventListener('input', applyFilters);
}

function initLegend() {
  var leg = document.getElementById('legend');
  var lh = '<span style="font-weight:600;color:#555">Departamentos:</span>';
  LOCAL_DATA.departments.forEach(function(d) {
    lh += '<span class="item"><span class="swatch" style="background:' + getDeptColor(d) + '"></span>' + d + '</span>';
  });
  lh += '<span class="item"><span class="swatch" style="background:#e0e0e0"></span>Sin asignar</span>';
  leg.innerHTML = lh;
}

function initModalClose() {
  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('modal-overlay').addEventListener('click', function(e) {
    if (e.target === e.currentTarget) closeModal();
  });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeModal();
      document.getElementById('confirm-overlay').classList.remove('active');
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  buildGrid();
  initFilters();
  initLegend();
  initModalClose();
  updateCounter();
  if (isSharePoint) {
    document.getElementById('sp-status').classList.add('connected');
    loadFromSharePoint();
  }
});
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

    people_directory = build_people_directory(seats_with_people, people)
    brigadistas = build_brigadistas(seats_with_people)
    timestamp = datetime.now().isoformat()

    output = {
        "rooms": room_cells,
        "seats": seats_with_people,
        "departments": sorted(departments),
        "brigadistas": brigadistas,
        "people_directory": people_directory,
        "total_seats": len(seats_with_people),
        "occupied_seats": occupied,
        "timestamp": timestamp,
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nJSON: {JSON_PATH} ({os.path.getsize(JSON_PATH):,} bytes)")

    data_json = json.dumps(output, ensure_ascii=False)
    html = generate_html(data_json)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML: {HTML_PATH} ({os.path.getsize(HTML_PATH):,} bytes)")
    print(f"Timestamp: {timestamp}")
    print(f"Personas en directorio: {len(people_directory)}")
    print(f"Brigadistas: {len(brigadistas)}")


if __name__ == "__main__":
    main()
