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
DEPLOY_PATH = os.path.join(SCRIPT_DIR, "deploy", "floor_plan.html")




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
    for row in range(1, ws.max_row + 1):
        for col in range(1, ws.max_column + 1):
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

    max_content_row = 1
    max_content_col = 1
    for info in room_cells:
        max_content_row = max(max_content_row, info["max_row"])
        max_content_col = max(max_content_col, info["max_col"])
    for s in seat_positions:
        max_content_row = max(max_content_row, s["row"])
        max_content_col = max(max_content_col, s["col"])

    return room_cells, seat_positions, max_content_row, max_content_col


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


def generate_html(static_json, data_json, grid_rows, grid_cols):
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
  grid-template-columns: repeat(''' + str(grid_cols) + ''', var(--cell-w));
  grid-template-rows: repeat(''' + str(grid_rows) + ''', var(--cell-h));
  gap: var(--gap);
  width: fit-content;
  margin: 0 auto;
  position: relative;
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
.room-editor-bar {
  display: none; background: #fff3e0; padding: 8px 20px;
  border-bottom: 2px solid #ff9800; font-size: 12px;
  align-items: center; gap: 12px; flex-wrap: wrap;
}
.room-editor-bar.active { display: flex; }
.room-editor-bar .re-label { font-weight: 700; color: #e65100; text-transform: uppercase; }
.room-editor-bar .re-status { font-weight: 600; color: #333; }
.cell.room.editor-hover { outline: 3px solid #ff9800; outline-offset: -1px; box-shadow: 0 0 8px rgba(255,152,0,0.5); z-index: 20; }
.cell.room.editor-selected { outline: 3px solid #dc1e28; outline-offset: -1px; box-shadow: 0 0 8px rgba(220,30,40,0.5); z-index: 20; }
.cell.editor-target { outline: 2px dashed #ff9800; outline-offset: -1px; background: rgba(255,152,0,0.15) !important; }
.cell.room.dragging { opacity: 0.3; }
.room-ghost {
  position: absolute; pointer-events: none; z-index: 50;
  border: 2px dashed #4caf50; background: rgba(76,175,80,0.2);
  border-radius: 3px; transition: none;
}
.room-ghost.invalid { border-color: #f44336; background: rgba(244,67,54,0.2); }
.cell.room.edge-n { cursor: n-resize; }
.cell.room.edge-s { cursor: s-resize; }
.cell.room.edge-e { cursor: e-resize; }
.cell.room.edge-w { cursor: w-resize; }
.cell.room.edge-nw { cursor: nw-resize; }
.cell.room.edge-ne { cursor: ne-resize; }
.cell.room.edge-sw { cursor: sw-resize; }
.cell.room.edge-se { cursor: se-resize; }
.cell.room.edge-move { cursor: grab; }
.cell.room.dragging { cursor: grabbing; }
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
  </div>
</div>
<div id="admin-panel" class="admin-panel">
  <span class="admin-label">Admin Mode</span>
  <button class="btn btn-primary" onclick="showAddPersonModal()" style="font-size:12px;padding:4px 12px">+ Add Person</button>
  <button class="btn btn-secondary" onclick="showManageBrigadistasModal()" style="font-size:12px;padding:4px 12px">Manage Brigadistas</button>
  <button class="btn btn-secondary" onclick="showColorPickerModal()" style="font-size:12px;padding:4px 12px">Customize Colors</button>
  <button class="btn btn-secondary" onclick="toggleRoomEditor()" id="btn-room-editor" style="font-size:12px;padding:4px 12px">Edit Rooms</button>
</div>
<div id="room-editor-bar" class="room-editor-bar">
  <span class="re-label">Room Editor:</span>
  <span class="re-status" id="re-status">Click a room to edit, or click two empty cells to draw a new room</span>
  <button class="btn btn-primary" id="re-draw-btn" onclick="startDrawRoom()" style="font-size:11px;padding:3px 10px">Draw New Room</button>
  <button class="btn btn-danger" id="re-cancel-draw-btn" onclick="cancelDraw()" style="font-size:11px;padding:3px 10px;display:none">Cancel Draw</button>
  <button class="btn btn-danger" id="re-delete-btn" onclick="deleteSelectedRoom()" style="font-size:11px;padding:3px 10px;display:none">Delete Room</button>
  <button class="btn btn-secondary" onclick="resetCustomRooms()" style="font-size:11px;padding:3px 10px">Reset Rooms</button>
  <button class="btn btn-secondary" onclick="cancelRoomEditor()" style="font-size:11px;padding:3px 10px">Exit Editor</button>
</div>
<div id="legend"></div>
<div id="grid-container"><div id="grid"><div id="room-ghost" class="room-ghost" style="display:none"></div></div></div>
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

var STATIC_DATA = ''' + static_json + ''';
var DATA = ''' + data_json + ''';

var isAdmin = new URLSearchParams(window.location.search).has('admin');
var LOCAL_DATA = JSON.parse(JSON.stringify(DATA));
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
  var allRooms = STATIC_DATA.rooms.concat(customRooms);
  allRooms.forEach(function(r) {
    roomOrigin[r.min_row + ',' + r.min_col] = r;
    for (var rr = r.min_row; rr <= r.max_row; rr++) {
      for (var cc = r.min_col; cc <= r.max_col; cc++) {
        covered[rr + ',' + cc] = 1;
      }
    }
  });
  for (var row = 1; row <= STATIC_DATA.grid_rows; row++) {
    for (var col = 1; col <= STATIC_DATA.grid_cols; col++) {
      var key = row + ',' + col;
      var origin = roomOrigin[key];
      if (origin) {
        var d = document.createElement('div');
        d.className = 'cell room';
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
      if (covered[key]) continue;
      var seat = seatMap[key];
      if (seat) {
        var d = document.createElement('div');
        var dept = seat.person ? seat.person.department : null;
        d.className = 'cell seat';
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
      var d = document.createElement('div');
      d.className = 'cell empty';
      d.style.gridRow = row;
      d.style.gridColumn = col;
      grid.appendChild(d);
    }
  }
  if (!document.getElementById('room-ghost')) {
    var ghost = document.createElement('div');
    ghost.id = 'room-ghost';
    ghost.className = 'room-ghost';
    ghost.style.display = 'none';
    grid.appendChild(ghost);
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
  if (typeof roomEditorMode !== 'undefined' && roomEditorMode !== 'idle') {
    cancelDraw();
  }
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
      if (dragState) {
        endDrag(e);
      } else if (typeof roomEditorMode !== 'undefined' && roomEditorMode !== 'idle') {
        cancelDraw();
      } else {
        closeModal();
        document.getElementById('confirm-overlay').classList.remove('active');
      }
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

// ============================================================
// ROOM EDITOR: Draw/edit rooms in admin mode
// ============================================================
var roomEditorActive = false;
var roomEditorMode = 'idle'; // idle, draw-first, draw-second, edit
var drawFirstCell = null;
var selectedRoom = null;
var customRooms = [];

function loadCustomRooms() {
  try {
    var saved = localStorage.getItem('sortis_custom_rooms');
    if (saved) customRooms = JSON.parse(saved);
  } catch(e) { customRooms = []; }
  var staticNames = {};
  STATIC_DATA.rooms.forEach(function(r) { staticNames[r.name.trim().toUpperCase()] = true; });
  customRooms = customRooms.filter(function(r) {
    return !staticNames[(r.name || '').trim().toUpperCase()];
  });
}

function saveCustomRooms() {
  localStorage.setItem('sortis_custom_rooms', JSON.stringify(customRooms));
}

function toggleRoomEditor() {
  if (roomEditorActive) { cancelRoomEditor(); return; }
  roomEditorActive = true;
  roomEditorMode = 'idle';
  document.getElementById('room-editor-bar').classList.add('active');
  document.getElementById('btn-room-editor').textContent = 'Stop Editing';
  document.getElementById('btn-room-editor').classList.remove('btn-secondary');
  document.getElementById('btn-room-editor').classList.add('btn-danger');
  document.getElementById('grid-container').style.height = 'calc(100vh - 140px)';
  document.getElementById('re-status').textContent = 'Click a room to edit, or click "Draw New Room"';
  addRoomEditorListeners();
  toast('Room editor activated', 'info');
}

function cancelRoomEditor() {
  roomEditorActive = false;
  roomEditorMode = 'idle';
  drawFirstCell = null;
  selectedRoom = null;
  dragState = null;
  document.getElementById('room-editor-bar').classList.remove('active');
  document.getElementById('btn-room-editor').textContent = 'Edit Rooms';
  document.getElementById('btn-room-editor').classList.remove('btn-danger');
  document.getElementById('btn-room-editor').classList.add('btn-secondary');
  document.getElementById('re-delete-btn').style.display = 'none';
  document.getElementById('grid-container').style.height = 'calc(100vh - 115px)';
  document.getElementById('room-ghost').style.display = 'none';
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', endDrag);
  removeRoomEditorListeners();
  refreshGrid();
}

function getCellRC(cell) {
  var gr = parseInt(cell.style.gridRow);
  var gc = parseInt(cell.style.gridColumn);
  return { row: gr, col: gc };
}

function onRoomEditorHover(e) {
  if (!roomEditorActive) return;
  var cell = e.target;
  if (roomEditorMode === 'draw-first' || roomEditorMode === 'draw-second') {
    cell.classList.add('editor-target');
  }
  if (cell.classList.contains('room')) {
    cell.classList.add('editor-hover');
  }
}

function onRoomEditorLeave(e) {
  e.target.classList.remove('editor-target');
  e.target.classList.remove('editor-hover');
}

function onRoomEditorClick(e) {
  if (!roomEditorActive) return;
  if (wasDragged) return;
  e.stopPropagation();
  var cell = e.target;
  var rc = getCellRC(cell);

  if (roomEditorMode === 'draw-first') {
    drawFirstCell = rc;
    roomEditorMode = 'draw-second';
    document.getElementById('re-status').textContent = 'Click second corner to complete the room';
    cell.classList.add('editor-selected');
    return;
  }

  if (roomEditorMode === 'draw-second') {
    var r1 = Math.min(drawFirstCell.row, rc.row);
    var c1 = Math.min(drawFirstCell.col, rc.col);
    var r2 = Math.max(drawFirstCell.row, rc.row);
    var c2 = Math.max(drawFirstCell.col, rc.col);
    if (r1 === r2 && c1 === c2) { toast('Select two different cells', 'error'); return; }
    showNewRoomForm(r1, c1, r2, c2);
    return;
  }

  // In idle mode, try to find a room at this position
  var room = findRoomAt(rc.row, rc.col);
  if (room) {
    selectedRoom = room;
    document.getElementById('re-delete-btn').style.display = 'inline-block';
    document.getElementById('re-status').textContent = 'Selected: ' + room.name + ' (' + (room.max_col-room.min_col+1) + 'x' + (room.max_row-room.min_row+1) + ')';
    // Highlight the selected room
    document.querySelectorAll('.editor-selected').forEach(function(c) { c.classList.remove('editor-selected'); });
    highlightRoom(room);
    showEditRoomForm(room);
    return;
  }
}

function findRoomAt(row, col) {
  var allRooms = STATIC_DATA.rooms.concat(customRooms);
  // Check custom rooms first (they override static rooms)
  for (var i = customRooms.length - 1; i >= 0; i--) {
    var r = customRooms[i];
    if (row >= r.min_row && row <= r.max_row && col >= r.min_col && col <= r.max_col) return r;
  }
  // Then check static rooms
  for (var j = 0; j < STATIC_DATA.rooms.length; j++) {
    var r2 = STATIC_DATA.rooms[j];
    if (row >= r2.min_row && row <= r2.max_row && col >= r2.min_col && col <= r2.max_col) return r2;
  }
  return null;
}

function highlightRoom(room) {
  document.querySelectorAll('.cell.room').forEach(function(cell) {
    var rc = getCellRC(cell);
    if (rc.row >= room.min_row && rc.row <= room.max_row && rc.col >= room.min_col && rc.col <= room.max_col) {
      cell.classList.add('editor-selected');
    }
  });
}

function startDrawRoom() {
  roomEditorMode = 'draw-first';
  drawFirstCell = null;
  document.getElementById('re-status').textContent = 'Click first corner of the new room (any empty cell)';
  document.getElementById('re-draw-btn').style.display = 'none';
  document.getElementById('re-cancel-draw-btn').style.display = 'inline-block';
  document.querySelectorAll('.cell.empty, .cell.seat').forEach(function(c) {
    c.style.cursor = 'crosshair';
  });
}

function showNewRoomForm(r1, c1, r2, c2) {
  var body = document.getElementById('modal-body');
  document.getElementById('modal-title').textContent = 'New Room';
  var h = '<div class="form-group"><label>Room Name</label>';
  h += '<input type="text" id="new-room-name" placeholder="e.g. OFICINA 01"></div>';
  h += '<div class="form-group"><label>Position</label>';
  h += '<div style="font-size:13px;color:#555">Row ' + r1 + '-' + r2 + ', Col ' + c1 + '-' + c2 + ' (' + (c2-c1+1) + ' x ' + (r2-r1+1) + ' cells)</div></div>';
  h += '<div class="modal-actions">';
  h += '<button class="btn btn-secondary" onclick="closeModal(); cancelDraw();">Cancel</button>';
  h += '<button class="btn btn-primary" onclick="saveNewRoom(' + r1 + ',' + c1 + ',' + r2 + ',' + c2 + ')">Create Room</button>';
  h += '</div>';
  body.innerHTML = h;
  document.getElementById('modal-overlay').classList.add('active');
  document.getElementById('new-room-name').focus();
}

function cancelDraw() {
  roomEditorMode = 'idle';
  drawFirstCell = null;
  document.getElementById('re-status').textContent = 'Click a room to edit, or click "Draw New Room"';
  document.getElementById('re-draw-btn').style.display = 'inline-block';
  document.getElementById('re-cancel-draw-btn').style.display = 'none';
  document.querySelectorAll('.editor-selected').forEach(function(c) { c.classList.remove('editor-selected'); });
  document.querySelectorAll('.cell').forEach(function(c) { c.style.cursor = ''; });
}

function saveNewRoom(r1, c1, r2, c2) {
  var name = document.getElementById('new-room-name').value.trim();
  if (!name) { toast('Room name required', 'error'); return; }
  var room = {
    name: name,
    min_row: r1, min_col: c1,
    max_row: r2, max_col: c2,
    _custom: true
  };
  customRooms.push(room);
  saveCustomRooms();
  closeModal();
  cancelDraw();
  refreshGrid();
  addRoomEditorListeners();
  toast('Room created: ' + name, 'success');
}

function selectRoomForEdit(cell) {
  document.querySelectorAll('.editor-selected').forEach(function(c) { c.classList.remove('editor-selected'); });
  cell.classList.add('editor-selected');
  var rc = getCellRC(cell);

  var room = null;
  var allRooms = STATIC_DATA.rooms.concat(customRooms);
  for (var i = 0; i < allRooms.length; i++) {
    var r = allRooms[i];
    if (rc.row >= r.min_row && rc.row <= r.max_row && rc.col >= r.min_col && rc.col <= r.max_col) {
      room = r; break;
    }
  }
  if (!room) return;
  selectedRoom = room;

  document.getElementById('re-delete-btn').style.display = room._custom ? 'inline-block' : 'none';
  document.getElementById('re-status').textContent = 'Editing: ' + room.name + ' (' + (room.max_col-room.min_col+1) + 'x' + (room.max_row-room.min_row+1) + ')';
  showEditRoomForm(room);
}

function showEditRoomForm(room) {
  var body = document.getElementById('modal-body');
  document.getElementById('modal-title').textContent = 'Edit Room: ' + room.name;
  var h = '<div class="form-group"><label>Room Name</label>';
  h += '<input type="text" id="edit-room-name" value="' + room.name.replace(/"/g, '&quot;') + '"></div>';
  h += '<div class="form-group"><label>Top-Left Row</label>';
  h += '<input type="number" id="edit-room-r1" value="' + room.min_row + '" min="1" max="' + STATIC_DATA.grid_rows + '"></div>';
  h += '<div class="form-group"><label>Top-Left Column</label>';
  h += '<input type="number" id="edit-room-c1" value="' + room.min_col + '" min="1" max="' + STATIC_DATA.grid_cols + '"></div>';
  h += '<div class="form-group"><label>Bottom-Right Row</label>';
  h += '<input type="number" id="edit-room-r2" value="' + room.max_row + '" min="1" max="' + STATIC_DATA.grid_rows + '"></div>';
  h += '<div class="form-group"><label>Bottom-Right Column</label>';
  h += '<input type="number" id="edit-room-c2" value="' + room.max_col + '" min="1" max="' + STATIC_DATA.grid_cols + '"></div>';
  h += '<div class="modal-actions">';
  h += '<button class="btn btn-secondary" onclick="closeModal()">Cancel</button>';
  h += '<button class="btn btn-primary" onclick="saveEditRoom()">Save</button>';
  h += '</div>';
  body.innerHTML = h;
  document.getElementById('modal-overlay').classList.add('active');
}

function saveEditRoom() {
  if (!selectedRoom) return;
  var name = document.getElementById('edit-room-name').value.trim();
  var r1 = parseInt(document.getElementById('edit-room-r1').value);
  var c1 = parseInt(document.getElementById('edit-room-c1').value);
  var r2 = parseInt(document.getElementById('edit-room-r2').value);
  var c2 = parseInt(document.getElementById('edit-room-c2').value);
  if (!name || !r1 || !c1 || !r2 || !c2) { toast('All fields required', 'error'); return; }
  if (r1 > r2 || c1 > c2) { toast('Invalid range', 'error'); return; }

  if (selectedRoom._custom) {
    // Update existing custom room
    selectedRoom.name = name;
    selectedRoom.min_row = r1;
    selectedRoom.min_col = c1;
    selectedRoom.max_row = r2;
    selectedRoom.max_col = c2;
  } else {
    // Static room → create a custom override
    var newRoom = {
      name: name,
      min_row: r1, min_col: c1,
      max_row: r2, max_col: c2,
      _custom: true
    };
    customRooms.push(newRoom);
  }
  saveCustomRooms();

  closeModal();
  selectedRoom = null;
  refreshGrid();
  addRoomEditorListeners();
  toast('Room saved: ' + name, 'success');
}

function deleteSelectedRoom() {
  if (!selectedRoom) return;
  var name = selectedRoom.name;
  if (selectedRoom._custom) {
    customRooms = customRooms.filter(function(r) { return r !== selectedRoom; });
    saveCustomRooms();
    toast('Room deleted: ' + name, 'info');
  } else {
    toast('Cannot delete original rooms', 'error');
    return;
  }
  selectedRoom = null;
  closeModal();
  document.getElementById('re-delete-btn').style.display = 'none';
  refreshGrid();
  addRoomEditorListeners();
}

function resetCustomRooms() {
  customRooms = [];
  localStorage.removeItem('sortis_custom_rooms');
  refreshGrid();
  addRoomEditorListeners();
  toast('Rooms reset to defaults', 'info');
}

// ============================================================
// DRAG AND DROP: Move/resize rooms by dragging
// ============================================================
var dragState = null;
var DRAG_THRESHOLD = 4;
var MIN_ROOM_SIZE = 2;
var wasDragged = false;

function getGridCoords(clientX, clientY) {
  var grid = document.getElementById('grid');
  var rect = grid.getBoundingClientRect();
  var cellW = 42 + 1;
  var cellH = 26 + 1;
  var col = Math.floor((clientX - rect.left) / cellW) + 1;
  var row = Math.floor((clientY - rect.top) / cellH) + 1;
  col = Math.max(1, Math.min(col, STATIC_DATA.grid_cols));
  row = Math.max(1, Math.min(row, STATIC_DATA.grid_rows));
  return { row: row, col: col };
}

function getRoomEdge(room, clientX, clientY) {
  var grid = document.getElementById('grid');
  var rect = grid.getBoundingClientRect();
  var cellW = 42 + 1;
  var cellH = 26 + 1;
  var threshold = 8;

  var roomLeft = (room.min_col - 1) * cellW + rect.left;
  var roomRight = room.max_col * cellW + rect.left;
  var roomTop = (room.min_row - 1) * cellH + rect.top;
  var roomBottom = room.max_row * cellH + rect.top;

  var nearTop = clientY - roomTop < threshold && clientY >= roomTop - 2;
  var nearBottom = roomBottom - clientY < threshold && clientY <= roomBottom + 2;
  var nearLeft = clientX - roomLeft < threshold && clientX >= roomLeft - 2;
  var nearRight = roomRight - clientX < threshold && clientX <= roomRight + 2;

  if (nearTop && nearLeft) return 'nw';
  if (nearTop && nearRight) return 'ne';
  if (nearBottom && nearLeft) return 'sw';
  if (nearBottom && nearRight) return 'se';
  if (nearTop) return 'n';
  if (nearBottom) return 's';
  if (nearLeft) return 'w';
  if (nearRight) return 'e';
  return null;
}

function getEdgeCursor(edge) {
  var map = { n:'n-resize', s:'s-resize', e:'e-resize', w:'w-resize', nw:'nw-resize', ne:'ne-resize', sw:'sw-resize', se:'se-resize' };
  return map[edge] || 'grab';
}

function updateRoomEdgeCursors() {
  if (!roomEditorActive || roomEditorMode !== 'idle') return;
  document.querySelectorAll('.cell.room').forEach(function(cell) {
    var rc = getCellRC(cell);
    var room = findRoomAt(rc.row, rc.col);
    if (!room) return;
    cell.classList.remove('edge-n','edge-s','edge-e','edge-w','edge-nw','edge-ne','edge-sw','edge-se','edge-move');
  });
}

function createGhost(room, r1, c1, r2, c2) {
  var ghost = document.getElementById('room-ghost');
  var cellW = 42 + 1;
  var cellH = 26 + 1;

  var x = (c1 - 1) * cellW;
  var y = (r1 - 1) * cellH;
  var w = (c2 - c1 + 1) * cellW - 1;
  var h = (r2 - r1 + 1) * cellH - 1;

  ghost.style.display = 'block';
  ghost.style.left = x + 'px';
  ghost.style.top = y + 'px';
  ghost.style.width = w + 'px';
  ghost.style.height = h + 'px';
  ghost.textContent = room.name;
  ghost.style.display = 'flex';
  ghost.style.alignItems = 'center';
  ghost.style.justifyContent = 'center';
  ghost.style.fontSize = '12px';
  ghost.style.fontWeight = '600';
  ghost.style.color = '#333';
}

function checkRoomCollision(excludeRoom, r1, c1, r2, c2) {
  if (r1 < 1 || c1 < 1 || r2 > STATIC_DATA.grid_rows || c2 > STATIC_DATA.grid_cols) return true;
  var allRooms = STATIC_DATA.rooms.concat(customRooms);
  for (var i = 0; i < allRooms.length; i++) {
    var r = allRooms[i];
    if (r === excludeRoom) continue;
    if (r === selectedRoom) continue;
    if (r1 <= r.max_row && r2 >= r.min_row && c1 <= r.max_col && c2 >= r.min_col) return true;
  }
  return false;
}

function startDrag(e, room, edge) {
  var startCoord = getGridCoords(e.clientX, e.clientY);
  dragState = {
    room: room,
    type: edge ? 'resize' : 'move',
    edge: edge,
    startMouse: { x: e.clientX, y: e.clientY },
    startCoord: startCoord,
    startBounds: { min_row: room.min_row, min_col: room.min_col, max_row: room.max_row, max_col: room.max_col },
    currentBounds: null,
    moved: false
  };

  document.addEventListener('mousemove', onDrag);
  document.addEventListener('mouseup', endDrag);
  e.preventDefault();
}

function onDrag(e) {
  if (!dragState) return;

  var dx = e.clientX - dragState.startMouse.x;
  var dy = e.clientY - dragState.startMouse.y;

  if (!dragState.moved && Math.abs(dx) < DRAG_THRESHOLD && Math.abs(dy) < DRAG_THRESHOLD) return;
  dragState.moved = true;

  var startCoord = dragState.startCoord;
  var b = dragState.startBounds;
  var room = dragState.room;

  if (!dragState.startedVisual) {
    dragState.startedVisual = true;
    document.querySelectorAll('.cell.room').forEach(function(cell) {
      var rc = getCellRC(cell);
      if (rc.row >= b.min_row && rc.row <= b.max_row && rc.col >= b.min_col && rc.col <= b.max_col) {
        cell.classList.add('dragging');
      }
    });
  }

  var delta = getGridCoords(e.clientX, e.clientY);
  var dRow = delta.row - startCoord.row;
  var dCol = delta.col - startCoord.col;

  var nr1, nc1, nr2, nc2;
  if (dragState.type === 'move') {
    nr1 = b.min_row + dRow;
    nc1 = b.min_col + dCol;
    nr2 = b.max_row + dRow;
    nc2 = b.max_col + dCol;
  } else {
    nr1 = b.min_row;
    nc1 = b.min_col;
    nr2 = b.max_row;
    nc2 = b.max_col;
    var edge = dragState.edge;
    if (edge === 'n' || edge === 'nw' || edge === 'ne') nr1 = b.min_row + dRow;
    if (edge === 's' || edge === 'sw' || edge === 'se') nr2 = b.max_row + dRow;
    if (edge === 'w' || edge === 'nw' || edge === 'sw') nc1 = b.min_col + dCol;
    if (edge === 'e' || edge === 'ne' || edge === 'se') nc2 = b.max_col + dCol;

    if (nr2 - nr1 + 1 < MIN_ROOM_SIZE) {
      if (edge === 'n' || edge === 'nw' || edge === 'ne') nr1 = nr2 - MIN_ROOM_SIZE + 1;
      else nr2 = nr1 + MIN_ROOM_SIZE - 1;
    }
    if (nc2 - nc1 + 1 < MIN_ROOM_SIZE) {
      if (edge === 'w' || edge === 'nw' || edge === 'sw') nc1 = nc2 - MIN_ROOM_SIZE + 1;
      else nc2 = nc1 + MIN_ROOM_SIZE - 1;
    }
  }

  if (nr1 < 1 || nc1 < 1 || nr2 > STATIC_DATA.grid_rows || nc2 > STATIC_DATA.grid_cols) {
    createGhost(room, b.min_row, b.min_col, b.max_row, b.max_col);
    document.getElementById('room-ghost').classList.add('invalid');
    dragState.currentBounds = null;
    document.getElementById('re-status').textContent = 'Out of bounds!';
    return;
  }

  var collision = checkRoomCollision(room, nr1, nc1, nr2, nc2);
  var ghost = document.getElementById('room-ghost');
  createGhost(room, nr1, nc1, nr2, nc2);
  if (collision) {
    ghost.classList.add('invalid');
    dragState.currentBounds = null;
    document.getElementById('re-status').textContent = 'Cannot place here (overlaps another room)';
  } else {
    ghost.classList.remove('invalid');
    dragState.currentBounds = { min_row: nr1, min_col: nc1, max_row: nr2, max_col: nc2 };
    var dims = (nc2 - nc1 + 1) + 'x' + (nr2 - nr1 + 1);
    document.getElementById('re-status').textContent = 'Drop to place: ' + dims + ' (press Esc to cancel)';
  }
}

function endDrag(e) {
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', endDrag);

  if (!dragState) return;

  var ghost = document.getElementById('room-ghost');
  ghost.style.display = 'none';
  ghost.classList.remove('invalid');

  document.querySelectorAll('.cell.room.dragging').forEach(function(c) { c.classList.remove('dragging'); });

  if (dragState.moved && dragState.currentBounds) {
    var nb = dragState.currentBounds;
    var room = dragState.room;
    wasDragged = true;
    setTimeout(function() { wasDragged = false; }, 300);

    if (!room._custom) {
      var newRoom = {
        name: room.name,
        min_row: nb.min_row, min_col: nb.min_col,
        max_row: nb.max_row, max_col: nb.max_col,
        _custom: true
      };
      customRooms.push(newRoom);
    } else {
      room.min_row = nb.min_row;
      room.min_col = nb.min_col;
      room.max_row = nb.max_row;
      room.max_col = nb.max_col;
    }
    saveCustomRooms();
    refreshGrid();
    addRoomEditorListeners();
    toast('Room moved: ' + room.name, 'success');
  }

  dragState = null;
}

function onRoomEditorMouseMove(e) {
  if (!roomEditorActive || roomEditorMode !== 'idle' || dragState) return;
  var cell = e.target;
  if (!cell.classList.contains('room')) {
    document.querySelectorAll('.cell.room').forEach(function(c) {
      c.classList.remove('edge-n','edge-s','edge-e','edge-w','edge-nw','edge-ne','edge-sw','edge-se','edge-move');
    });
    return;
  }
  var rc = getCellRC(cell);
  var room = findRoomAt(rc.row, rc.col);
  if (!room) return;

  var edge = getRoomEdge(room, e.clientX, e.clientY);
  document.querySelectorAll('.cell.room').forEach(function(c) {
    c.classList.remove('edge-n','edge-s','edge-e','edge-w','edge-nw','edge-ne','edge-sw','edge-se','edge-move');
  });

  if (edge) {
    var cells = document.querySelectorAll('.cell.room');
    cells.forEach(function(c) {
      var r = getCellRC(c);
      if (r.row >= room.min_row && r.row <= room.max_row && r.col >= room.min_col && r.col <= room.max_col) {
        c.classList.add('edge-' + edge);
      }
    });
  } else {
    var cells2 = document.querySelectorAll('.cell.room');
    cells2.forEach(function(c) {
      var r = getCellRC(c);
      if (r.row >= room.min_row && r.row <= room.max_row && r.col >= room.min_col && r.col <= room.max_col) {
        c.classList.add('edge-move');
      }
    });
  }
}

function onRoomEditorMouseDown(e) {
  if (!roomEditorActive || roomEditorMode !== 'idle') return;
  var cell = e.target;
  if (!cell.classList.contains('room')) return;

  var rc = getCellRC(cell);
  var room = findRoomAt(rc.row, rc.col);
  if (!room) return;

  e.preventDefault();
  e.stopPropagation();

  var edge = getRoomEdge(room, e.clientX, e.clientY);
  startDrag(e, room, edge);
}

function addRoomEditorListeners() {
  var cells = document.querySelectorAll('.cell');
  cells.forEach(function(cell) {
    cell.addEventListener('click', onRoomEditorClick);
    cell.addEventListener('mouseenter', onRoomEditorHover);
    cell.addEventListener('mouseleave', onRoomEditorLeave);
    cell.addEventListener('mousedown', onRoomEditorMouseDown);
    cell.addEventListener('mousemove', onRoomEditorMouseMove);
  });
}

function removeRoomEditorListeners() {
  var cells = document.querySelectorAll('.cell');
  cells.forEach(function(cell) {
    cell.removeEventListener('click', onRoomEditorClick);
    cell.removeEventListener('mouseenter', onRoomEditorHover);
    cell.removeEventListener('mouseleave', onRoomEditorLeave);
    cell.removeEventListener('mousedown', onRoomEditorMouseDown);
    cell.removeEventListener('mousemove', onRoomEditorMouseMove);
  });
}

function initAdmin() {
  if (isAdmin) {
    document.getElementById('admin-panel').classList.add('visible');
    document.getElementById('grid-container').style.height = 'calc(100vh - 115px)';
  }
}

document.addEventListener('DOMContentLoaded', function() {
  loadCustomColors();
  loadCustomRooms();
  initAdmin();
  buildGrid();
  initFilters();
  initLegend();
  initModalClose();
  updateCounter();
});
</script>
</body>
</html>'''


def main():
    print(f"Leyendo: {EXCEL_PATH}")
    wb = openpyxl.load_workbook(EXCEL_PATH)

    print("Parseando plano...")
    room_cells, seat_positions, grid_rows, grid_cols = read_floor_plan(wb)
    print(f"  Salas: {len(room_cells)}, Puestos en plano: {len(seat_positions)}")
    print(f"  Grid: {grid_rows} rows x {grid_cols} cols")

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
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
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
    html = generate_html(static_json, data_json, grid_rows, grid_cols)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML: {HTML_PATH} ({os.path.getsize(HTML_PATH):,} bytes)")

    html_deploy = generate_html(static_json, data_json, grid_rows, grid_cols)
    os.makedirs(os.path.dirname(DEPLOY_PATH), exist_ok=True)
    with open(DEPLOY_PATH, "w", encoding="utf-8") as f:
        f.write(html_deploy)
    print(f"DEPLOY: {DEPLOY_PATH} ({os.path.getsize(DEPLOY_PATH):,} bytes)")
    print(f"Timestamp: {timestamp}")
    print(f"Personas en directorio: {len(people_directory)}")
    print(f"Brigadistas: {len(brigadistas)}")


if __name__ == "__main__":
    main()
