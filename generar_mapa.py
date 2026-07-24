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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(SCRIPT_DIR, "SORTIS_FLOOR_PLAN.xlsx")
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
        department = ws.cell(row, 5).value
        seat_key = normalize_seat_no(seat_no_raw)
        if seat_key is None:
            continue
        seats[seat_key] = {
            "name": fix_encoding(str(name).strip()) if name else None,
            "brigadista": fix_encoding(str(brigadista).strip()) if brigadista else None,
            "notas": fix_encoding(str(notas).strip()) if notas else None,
            "department": fix_encoding(str(department).strip()) if department else None,
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
                "department": info.get("department") or (p["department"] if p else None),
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


def generate_html(static_json, data_json):
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
.cell.room.narrow { font-size: 7px; }
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
.btn-success { background: #2e7d32; color: #fff; }
.btn-success:hover { background: #1b5e20; }
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
.form-group { margin-bottom: 14px; }
.form-group label {
  display: block; font-size: 12px; font-weight: 600;
  color: #555; margin-bottom: 4px; text-transform: uppercase;
}
.form-group input, .form-group select, .form-group textarea {
  width: 100%; padding: 10px 12px; border: 2px solid #ddd;
  border-radius: 6px; font-size: 14px; outline: none;
  font-family: inherit;
}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus {
  border-color: #1a237e;
}
.form-group textarea { resize: vertical; min-height: 60px; }
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
.admin-panel {
  display: none; background: #fff3e0; padding: 8px 20px;
  border-bottom: 2px solid #ff9800; font-size: 12px;
  align-items: center; gap: 12px;
}
.admin-panel.visible { display: flex; }
.admin-panel .admin-label {
  font-weight: 700; color: #e65100; text-transform: uppercase;
}
.color-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.color-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; background: #f5f5f5; border-radius: 6px; }
.color-item label { font-size: 12px; font-weight: 600; color: #555; flex: 1; min-width: 0; }
.color-item input[type="color"] { width: 36px; height: 28px; border: 2px solid #ddd; border-radius: 4px; cursor: pointer; padding: 0; }
.color-item input[type="color"]::-webkit-color-swatch-wrapper { padding: 2px; }
.color-item input[type="color"]::-webkit-color-swatch { border: none; border-radius: 2px; }
.color-section-title { font-size: 13px; font-weight: 700; color: #333; margin: 14px 0 8px; padding-bottom: 4px; border-bottom: 2px solid #dc1e28; }
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
<div id="admin-panel" class="admin-panel">
  <span class="admin-label">Admin Mode</span>
  <button class="btn btn-primary" onclick="showAddPersonModal()" style="font-size:12px;padding:4px 12px">+ Add Person</button>
  <button class="btn btn-secondary" onclick="showManageBrigadistasModal()" style="font-size:12px;padding:4px 12px">Manage Brigadistas</button>
  <button class="btn btn-secondary" onclick="showColorPickerModal()" style="font-size:12px;padding:4px 12px">Customize Colors</button>
  <button class="btn btn-success" id="btn-seed" onclick="seedSharePointData()" style="font-size:12px;padding:4px 12px;display:none">Seed SharePoint Lists</button>
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
  Finance: '#50505a', IT: '#dc1e28', ENS: '#f5c6cb', Title: '#6c757d',
  IBC: '#d6d8db', CaseAware: '#e78c92', VS360: '#a8323b', 'Firm Solutions': '#bfc1c5'
};
var DEPARTMENTS = ['Finance', 'IT', 'ENS', 'Title', 'IBC', 'CaseAware', 'VS360', 'Firm Solutions'];
var ROOM_COLORS = {
  COMEDOR: '#f5c6cb', ARCHIVE: '#d6d8db', 'CUARTO DE IT': '#e78c92',
  'BA\\u00d1O DE MUJERES': '#bfc1c5', 'BA\\u00d1O DE HOMBRES': '#bfc1c5',
  LOCKERS: '#e8e8ec', 'SALA DE ENTRENAMIENTO': '#dc1e28',
  'SALA DE REUNIONES': '#a8323b', RECEPCION: '#6c757d',
  'CUARTO ELECTRICO': '#d6d8db', 'CUARTO DE A/C': '#d6d8db',
  'CUARTO A/C': '#d6d8db', 'OFICINA DE IT': '#e78c92',
  'DEPOSITO IT': '#e78c92', 'WAR ROOM': '#dc1e28',
  'OFICINA GERENCIA': '#50505a', 'OFICINA DE GERENCIA 03': '#6c757d',
  'OFICINA DE GERENCIA 06': '#6c757d',
  'HR162': '#a8323b', Supervisor: '#50505a'
};

var SHAREPOINT_SITE = '';
var PEOPLE_LIST = 'People';
var SEATS_LIST = 'Seats';

var STATIC_DATA = ''' + static_json + ''';
var DATA = ''' + data_json + ''';

var isSharePoint = SHAREPOINT_SITE.length > 0;
var isAdmin = new URLSearchParams(window.location.search).has('admin');
var LOCAL_DATA = JSON.parse(JSON.stringify(DATA));
var hasChanges = false;
var spPeople = [];
var spSeats = [];

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
  STATIC_DATA.rooms.forEach(function(r) {
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
    if (isAdmin) {
      h += '<button class="btn btn-success" onclick="editPerson(\\'' + p.name.replace(/'/g, "\\'") + '\\')">Edit Person</button> ';
    }
    h += '<button class="btn btn-primary" onclick="startReassign(\\'' + seat.seat_no + '\\')">Reasignar</button> ';
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

// ============================================================
// ADMIN: Edit Person
// ============================================================
function editPerson(personName) {
  document.getElementById('modal-overlay').classList.remove('active');
  var pd = LOCAL_DATA.people_directory || [];
  var person = null;
  for (var i = 0; i < pd.length; i++) {
    if (pd[i].name === personName) { person = pd[i]; break; }
  }
  if (!person) { toast('Person not found', 'error'); return; }

  var body = document.getElementById('modal-body');
  document.getElementById('modal-title').textContent = 'Edit Person';
  var h = '<div class="form-group"><label>Full Name</label>';
  h += '<input type="text" id="edit-name" value="' + (person.name || '').replace(/"/g, '&quot;') + '"></div>';
  h += '<div class="form-group"><label>Department</label>';
  h += '<select id="edit-dept">';
  DEPARTMENTS.forEach(function(d) {
    var sel = person.department === d ? ' selected' : '';
    h += '<option value="' + d + '"' + sel + '>' + d + '</option>';
  });
  h += '</select></div>';
  h += '<div class="form-group"><label>Job Title</label>';
  h += '<input type="text" id="edit-title" value="' + (person.title || '').replace(/"/g, '&quot;') + '"></div>';
  h += '<div class="modal-actions">';
  h += '<button class="btn btn-secondary" onclick="closeModal()">Cancel</button>';
  h += '<button class="btn btn-primary" onclick="savePersonEdit(\\'' + personName.replace(/'/g, "\\'") + '\\')">Save</button>';
  h += '</div>';
  body.innerHTML = h;
  document.getElementById('modal-overlay').classList.add('active');
}

function savePersonEdit(oldName) {
  var newName = document.getElementById('edit-name').value.trim();
  var newDept = document.getElementById('edit-dept').value;
  var newTitle = document.getElementById('edit-title').value.trim();
  if (!newName) { toast('Name is required', 'error'); return; }

  // Update people_directory
  var pd = LOCAL_DATA.people_directory || [];
  for (var i = 0; i < pd.length; i++) {
    if (pd[i].name === oldName) {
      pd[i].name = newName;
      pd[i].department = newDept;
      pd[i].title = newTitle;
      break;
    }
  }

  // Update all seats with this person
  LOCAL_DATA.seats.forEach(function(s) {
    if (s.person && s.person.name === oldName) {
      s.person.name = newName;
      s.person.department = newDept;
      s.person.title = newTitle;
    }
  });

  // Update brigadistas if name changed
  if (oldName !== newName) {
    LOCAL_DATA.seats.forEach(function(s) {
      if (s.brigadista === oldName) s.brigadista = newName;
    });
  }

  hasChanges = true;
  closeModal();
  refreshGrid();
  toast('Person updated: ' + newName, 'success');
  autoSave();
}

// ============================================================
// ADMIN: Add New Person
// ============================================================
function showAddPersonModal() {
  var body = document.getElementById('modal-body');
  document.getElementById('modal-title').textContent = 'Add New Person';
  var h = '<div class="form-group"><label>Full Name</label>';
  h += '<input type="text" id="new-name" placeholder="Enter full name"></div>';
  h += '<div class="form-group"><label>Department</label>';
  h += '<select id="new-dept">';
  DEPARTMENTS.forEach(function(d) {
    h += '<option value="' + d + '">' + d + '</option>';
  });
  h += '</select></div>';
  h += '<div class="form-group"><label>Job Title</label>';
  h += '<input type="text" id="new-title" placeholder="Enter job title"></div>';
  h += '<div class="modal-actions">';
  h += '<button class="btn btn-secondary" onclick="closeModal()">Cancel</button>';
  h += '<button class="btn btn-primary" onclick="saveNewPerson()">Add Person</button>';
  h += '</div>';
  body.innerHTML = h;
  document.getElementById('modal-overlay').classList.add('active');
}

function saveNewPerson() {
  var name = document.getElementById('new-name').value.trim();
  var dept = document.getElementById('new-dept').value;
  var title = document.getElementById('new-title').value.trim();
  if (!name) { toast('Name is required', 'error'); return; }

  // Check duplicate
  var pd = LOCAL_DATA.people_directory || [];
  for (var i = 0; i < pd.length; i++) {
    if (pd[i].name.toLowerCase() === name.toLowerCase()) {
      toast('Person already exists', 'error');
      return;
    }
  }

  pd.push({ name: name, department: dept, title: title });
  pd.sort(function(a, b) { return a.name.localeCompare(b.name); });
  LOCAL_DATA.people_directory = pd;

  hasChanges = true;
  closeModal();
  toast('Person added: ' + name, 'success');
  autoSave();
}

// ============================================================
// ADMIN: Manage Brigadistas
// ============================================================
function showManageBrigadistasModal() {
  var body = document.getElementById('modal-body');
  document.getElementById('modal-title').textContent = 'Manage Brigadistas';
  var brigadistas = LOCAL_DATA.brigadistas || [];
  var h = '<div style="margin-bottom:12px">';
  h += '<div class="form-group"><label>Add Brigadista (from People directory)</label>';
  h += '<div class="autocomplete-wrap">';
  h += '<input type="text" class="autocomplete-input" id="brig-ac-input" placeholder="Search person..." autocomplete="off">';
  h += '<div class="autocomplete-list" id="brig-ac-list"></div>';
  h += '</div></div>';
  h += '<button class="btn btn-primary" id="btn-add-brig" disabled onclick="addBrigadista()" style="font-size:12px">Add</button>';
  h += '</div>';
  h += '<div style="border-top:1px solid #eee;padding-top:12px">';
  h += '<div class="field-label" style="margin-bottom:8px">Current Brigadistas (' + brigadistas.length + ')</div>';
  brigadistas.forEach(function(b) {
    h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;padding:6px 10px;background:#f5f5f5;border-radius:6px">';
    h += '<span style="flex:1;font-size:13px">' + b + '</span>';
    h += '<button class="btn btn-danger" style="font-size:11px;padding:3px 8px" onclick="removeBrigadista(\\'' + b.replace(/'/g, "\\'") + '\\')">Remove</button>';
    h += '</div>';
  });
  if (brigadistas.length === 0) h += '<div style="color:#999;font-style:italic;font-size:13px">No brigadistas assigned</div>';
  h += '</div>';
  h += '<div class="modal-actions">';
  h += '<button class="btn btn-secondary" onclick="closeModal()">Close</button>';
  h += '</div>';
  body.innerHTML = h;
  document.getElementById('modal-overlay').classList.add('active');
  setupBrigadistaAutocomplete();
}

var selectedBrigPerson = null;
function setupBrigadistaAutocomplete() {
  selectedBrigPerson = null;
  var input = document.getElementById('brig-ac-input');
  var list = document.getElementById('brig-ac-list');
  var btn = document.getElementById('btn-add-brig');

  function renderList(filter) {
    var html = '';
    var people = LOCAL_DATA.people_directory || [];
    var brigadistas = LOCAL_DATA.brigadistas || [];
    var count = 0;
    for (var i = 0; i < people.length && count < 20; i++) {
      var p = people[i];
      if (brigadistas.indexOf(p.name) >= 0) continue;
      if (filter && p.name.toLowerCase().indexOf(filter.toLowerCase()) < 0) continue;
      html += '<div class="autocomplete-item" data-name="' + p.name.replace(/"/g, '&quot;') + '">';
      html += p.name + '<span class="ac-dept">' + (p.department || '') + '</span></div>';
      count++;
    }
    if (count === 0) html = '<div class="autocomplete-item" style="color:#999">No available people</div>';
    list.innerHTML = html;
    list.classList.add('open');
    list.querySelectorAll('.autocomplete-item[data-name]').forEach(function(item) {
      item.addEventListener('click', function() {
        selectedBrigPerson = this.getAttribute('data-name');
        input.value = selectedBrigPerson;
        list.classList.remove('open');
        btn.disabled = false;
      });
    });
  }

  input.addEventListener('input', function() {
    selectedBrigPerson = null;
    btn.disabled = true;
    renderList(this.value);
  });
  input.addEventListener('focus', function() { renderList(this.value); });
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.autocomplete-wrap')) list.classList.remove('open');
  });
}

function addBrigadista() {
  if (!selectedBrigPerson) return;
  var brig = LOCAL_DATA.brigadistas || [];
  if (brig.indexOf(selectedBrigPerson) >= 0) { toast('Already a brigadista', 'error'); return; }
  brig.push(selectedBrigPerson);
  brig.sort();
  LOCAL_DATA.brigadistas = brig;
  hasChanges = true;
  showManageBrigadistasModal();
  toast('Brigadista added: ' + selectedBrigPerson, 'success');
  autoSave();
}

function removeBrigadista(name) {
  var brig = LOCAL_DATA.brigadistas || [];
  LOCAL_DATA.brigadistas = brig.filter(function(b) { return b !== name; });
  hasChanges = true;
  showManageBrigadistasModal();
  toast('Brigadista removed: ' + name, 'info');
  autoSave();
}

// ============================================================
// SHAREPOINT LISTS API
// ============================================================
function getDigest() {
  var d = document.querySelector('#__REQUESTDIGEST');
  return d ? d.value : '';
}

function spGet(listName) {
  if (!isSharePoint) return Promise.resolve([]);
  var url = SHAREPOINT_SITE + "_api/web/lists/getbytitle('" + listName + "')/items?$top=5000";
  return fetch(url, {
    headers: { 'Accept': 'application/json;odata=verbose' }
  }).then(function(r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }).then(function(data) {
    return data.d.results || [];
  });
}

function spCreate(listName, itemData) {
  if (!isSharePoint) return Promise.resolve(null);
  var url = SHAREPOINT_SITE + "_api/web/lists/getbytitle('" + listName + "')/items";
  return fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'application/json;odata=verbose',
      'Content-Type': 'application/json;odata=verbose',
      'X-RequestDigest': getDigest()
    },
    body: JSON.stringify(itemData)
  }).then(function(r) { return r.json(); });
}

function spUpdate(listName, itemId, itemData) {
  if (!isSharePoint) return Promise.resolve(null);
  var url = SHAREPOINT_SITE + "_api/web/lists/getbytitle('" + listName + "')/items(" + itemId + ")";
  return fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'application/json;odata=verbose',
      'Content-Type': 'application/json;odata=verbose',
      'X-RequestDigest': getDigest(),
      'IF-MATCH': '*',
      'X-HTTP-Method': 'MERGE'
    },
    body: JSON.stringify(itemData)
  });
}

function spDelete(listName, itemId) {
  if (!isSharePoint) return Promise.resolve(null);
  var url = SHAREPOINT_SITE + "_api/web/lists/getbytitle('" + listName + "')/items(" + itemId + ")";
  return fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'application/json;odata=verbose',
      'X-RequestDigest': getDigest(),
      'IF-MATCH': '*',
      'X-HTTP-Method': 'DELETE'
    }
  });
}

function loadFromSharePointLists() {
  if (!isSharePoint) return;
  document.getElementById('sp-status').classList.add('connected');

  Promise.all([spGet(PEOPLE_LIST), spGet(SEATS_LIST)]).then(function(results) {
    spPeople = results[0];
    spSeats = results[1];

    // Build people_directory from People list
    var peopleDir = [];
    spPeople.forEach(function(item) {
      peopleDir.push({
        name: item.Title || '',
        department: item.Department || '',
        title: item.JobTitle || '',
        _spId: item.Id
      });
    });
    LOCAL_DATA.people_directory = peopleDir;

    // Build brigadistas from People list (filter Status = Brigadista or separate logic)
    // For now, keep existing brigadistas logic

    // Build seats from Seats list + static seat_positions
    var seatMap = {};
    spSeats.forEach(function(item) {
      seatMap[item.Title] = {
        name: item.PersonName || null,
        brigadista: item.Brigadista || null,
        notas: item.Notas || null,
        _spId: item.Id
      };
    });

    LOCAL_DATA.seats = STATIC_DATA.seat_positions.map(function(sp) {
      var seatNo = sp.seat_no;
      var alloc = seatMap[seatNo];
      var person = null;
      if (alloc && alloc.name) {
        var pd = null;
        for (var i = 0; i < peopleDir.length; i++) {
          if (peopleDir[i].name === alloc.name) { pd = peopleDir[i]; break; }
        }
        person = {
          name: alloc.name,
          brigadista: alloc.brigadista,
          notas: alloc.notas,
          department: pd ? pd.department : null,
          title: pd ? pd.title : null
        };
      }
      return {
        row: sp.row,
        col: sp.col,
        seat_no: seatNo,
        person: person,
        brigadista: alloc ? alloc.brigadista : null
      };
    });

    // Update departments
    var depts = {};
    LOCAL_DATA.seats.forEach(function(s) {
      if (s.person && s.person.department) depts[s.person.department] = 1;
    });
    LOCAL_DATA.departments = Object.keys(depts).sort();

    // Update brigadistas
    var brig = {};
    LOCAL_DATA.seats.forEach(function(s) {
      if (s.brigadista) brig[s.brigadista] = 1;
    });
    LOCAL_DATA.brigadistas = Object.keys(brig).sort();

    refreshGrid();
    toast('Data loaded from SharePoint Lists', 'success');
  }).catch(function(err) {
    console.error('SharePoint load error:', err);
    toast('Could not connect to SharePoint, using local data', 'info');
  });
}

function saveToSharePointLists() {
  if (!isSharePoint || !hasChanges) return;

  // Save each seat assignment
  var promises = [];
  LOCAL_DATA.seats.forEach(function(seat) {
    var spSeat = null;
    for (var i = 0; i < spSeats.length; i++) {
      if (spSeats[i].Title === seat.seat_no) { spSeat = spSeats[i]; break; }
    }

    if (seat.person) {
      var data = {
        Title: seat.seat_no,
        PersonName: seat.person.name || '',
        Brigadista: seat.brigadista || '',
        Notas: seat.person.notas || ''
      };
      if (spSeat) {
        promises.push(spUpdate(SEATS_LIST, spSeat.Id, data));
      } else {
        promises.push(spCreate(SEATS_LIST, data));
      }
    } else if (spSeat) {
      promises.push(spDelete(SEATS_LIST, spSeat.Id));
    }
  });

  Promise.all(promises).then(function() {
    hasChanges = false;
    toast('Changes saved to SharePoint', 'success');
  }).catch(function(err) {
    console.error('SharePoint save error:', err);
    toast('Error saving to SharePoint', 'error');
  });
}

var saveTimeout = null;
function autoSave() {
  if (!isSharePoint) return;
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(function() { saveToSharePointLists(); }, 2000);
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

// ============================================================
// COLOR PICKER: Customize department and room colors
// ============================================================
var DEFAULT_DEPT_COLORS = JSON.parse(JSON.stringify(DEPT_COLORS));
var DEFAULT_ROOM_COLORS = JSON.parse(JSON.stringify(ROOM_COLORS));

function loadCustomColors() {
  try {
    var saved = localStorage.getItem('sortis_custom_colors');
    if (saved) {
      var data = JSON.parse(saved);
      if (data.dept) { for (var k in data.dept) { DEPT_COLORS[k] = data.dept[k]; } }
      if (data.room) { for (var k in data.room) { ROOM_COLORS[k] = data.room[k]; } }
    }
  } catch(e) {}
}

function saveCustomColors(deptColors, roomColors) {
  localStorage.setItem('sortis_custom_colors', JSON.stringify({ dept: deptColors, room: roomColors }));
}

function resetColors() {
  for (var k in DEFAULT_DEPT_COLORS) { DEPT_COLORS[k] = DEFAULT_DEPT_COLORS[k]; }
  for (var k in DEFAULT_ROOM_COLORS) { ROOM_COLORS[k] = DEFAULT_ROOM_COLORS[k]; }
  localStorage.removeItem('sortis_custom_colors');
  refreshGrid();
  initLegend();
  toast('Colors reset to defaults', 'info');
}

function showColorPickerModal() {
  var body = document.getElementById('modal-body');
  document.getElementById('modal-title').textContent = 'Customize Colors';
  var h = '';

  h += '<div class="color-section-title">Department Colors</div>';
  h += '<div class="color-grid">';
  var deptKeys = Object.keys(DEPT_COLORS).sort();
  for (var i = 0; i < deptKeys.length; i++) {
    var d = deptKeys[i];
    h += '<div class="color-item"><label>' + d + '</label>';
    h += '<input type="color" id="dc-' + d.replace(/[^a-zA-Z0-9]/g, '_') + '" value="' + DEPT_COLORS[d] + '"></div>';
  }
  h += '</div>';

  h += '<div class="color-section-title">Room Colors</div>';
  h += '<div class="color-grid">';
  var roomKeys = Object.keys(ROOM_COLORS).sort();
  for (var j = 0; j < roomKeys.length; j++) {
    var r = roomKeys[j];
    h += '<div class="color-item"><label>' + r + '</label>';
    h += '<input type="color" id="rc-' + r.replace(/[^a-zA-Z0-9]/g, '_') + '" value="' + ROOM_COLORS[r] + '"></div>';
  }
  h += '</div>';

  h += '<div class="modal-actions">';
  h += '<button class="btn btn-danger" onclick="resetColors(); closeModal();">Reset Defaults</button>';
  h += '<button class="btn btn-secondary" onclick="closeModal()">Cancel</button>';
  h += '<button class="btn btn-primary" onclick="applyColorPicker()">Apply</button>';
  h += '</div>';
  body.innerHTML = h;
  document.getElementById('modal-overlay').classList.add('active');
}

function applyColorPicker() {
  var newDept = {};
  var deptKeys = Object.keys(DEFAULT_DEPT_COLORS).sort();
  for (var i = 0; i < deptKeys.length; i++) {
    var d = deptKeys[i];
    var el = document.getElementById('dc-' + d.replace(/[^a-zA-Z0-9]/g, '_'));
    if (el) { newDept[d] = el.value; DEPT_COLORS[d] = el.value; }
  }
  var newRoom = {};
  var roomKeys = Object.keys(DEFAULT_ROOM_COLORS).sort();
  for (var j = 0; j < roomKeys.length; j++) {
    var r = roomKeys[j];
    var el2 = document.getElementById('rc-' + r.replace(/[^a-zA-Z0-9]/g, '_'));
    if (el2) { newRoom[r] = el2.value; ROOM_COLORS[r] = el2.value; }
  }
  saveCustomColors(newDept, newRoom);
  closeModal();
  refreshGrid();
  initLegend();
  toast('Colors updated', 'success');
}

function initAdmin() {
  if (isAdmin) {
    document.getElementById('admin-panel').classList.add('visible');
    document.getElementById('grid-container').style.height = 'calc(100vh - 115px)';
    if (isSharePoint) {
      document.getElementById('btn-seed').style.display = 'inline-block';
    }
  }
}

// ============================================================
// SEED DATA: Populate SharePoint Lists from embedded data
// ============================================================
async function seedSharePointData() {
  if (!isSharePoint) { toast('SharePoint not configured', 'error'); return; }
  var people = DATA.people_directory || [];
  var seats = DATA.seats || [];
  var confirmMsg = 'This will create ' + people.length + ' people and ' + seats.filter(function(s){return s.person}).length + ' seat assignments in SharePoint Lists. Continue?';
  if (!confirm(confirmMsg)) return;

  var btn = document.getElementById('btn-seed');
  btn.disabled = true;
  btn.textContent = 'Seeding...';
  var created = 0;
  var errors = 0;

  try {
    // Seed People
    toast('Creating people records...', 'info');
    for (var i = 0; i < people.length; i++) {
      var p = people[i];
      try {
        await spCreate(PEOPLE_LIST, {
          Title: p.name,
          Department: p.department || '',
          JobTitle: p.title || '',
          Status: 'Active'
        });
        created++;
      } catch(e) { errors++; }
    }
    toast('People: ' + created + ' created, ' + errors + ' errors', 'success');

    // Seed Seats
    var seatCreated = 0;
    var seatErrors = 0;
    toast('Creating seat assignments...', 'info');
    for (var j = 0; j < seats.length; j++) {
      var s = seats[j];
      if (!s.person || !s.person.name) continue;
      try {
        await spCreate(SEATS_LIST, {
          Title: s.seat_no,
          PersonName: s.person.name,
          Brigadista: s.brigadista || '',
          Notas: s.person.notas || ''
        });
        seatCreated++;
      } catch(e) { seatErrors++; }
    }
    toast('Seats: ' + seatCreated + ' created, ' + seatErrors + ' errors', 'success');

    btn.textContent = 'Seed Complete!';
    btn.style.background = '#2e7d32';
  } catch(e) {
    toast('Seed failed: ' + e.message, 'error');
    btn.textContent = 'Seed Failed';
    btn.style.background = '#c62828';
  }
  btn.disabled = false;
}

document.addEventListener('DOMContentLoaded', function() {
  loadCustomColors();
  initAdmin();
  buildGrid();
  initFilters();
  initLegend();
  initModalClose();
  updateCounter();
  if (isSharePoint) {
    loadFromSharePointLists();
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

    # Static data (rooms + seat positions) - never changes
    static_data = {
        "rooms": room_cells,
        "seat_positions": seat_positions,
    }

    # Full data (for JSON export and local mode)
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

    static_json = json.dumps(static_data, ensure_ascii=False)
    data_json = json.dumps(output, ensure_ascii=False)
    html = generate_html(static_json, data_json)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML: {HTML_PATH} ({os.path.getsize(HTML_PATH):,} bytes)")
    print(f"Timestamp: {timestamp}")
    print(f"Personas en directorio: {len(people_directory)}")
    print(f"Brigadistas: {len(brigadistas)}")


if __name__ == "__main__":
    main()
