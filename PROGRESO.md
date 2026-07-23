# SORTIS - Mapa Interactivo de Oficina Piso 7

## Objetivo
Crear una app web interactiva (HTML/JS autocontenido) que muestre el mapa de oficina de SORTIS Piso 7, mostrando info de la persona en cada puesto al hacer click.

## GitHub
https://github.com/david-arjona-a360/Sortis

## Archivos Fuente
- **Excel**: `C:\Users\david.arjona\OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN\SORTIS_FLOOR_PLAN.xlsx`
- **PDF** (analizado, NO se usa como base): `A02_DISTRIBUCIÓN_OSO (2).pdf` — es un plano estructural sin datos de puestos

## Estructura del Excel

### Hoja "Floor plan" (76 filas x 27 columnas, A-AA)
Grid visual de la oficina. Celdas combinadas = áreas/habitaciones. Celdas individuales = puestos numerados 1-167.

**Áreas (celdas combinadas):**
| Celda | Área |
|-------|------|
| A1:B6 | COMEDOR |
| Y1:Y6 | ARCHIVE |
| Z1:Z6 | CUARTO DE IT |
| A7:A11 | BAÑO DE MUJERES |
| C7:C11 | LOCKERS |
| D7 | Puesto 167 |
| E7:H8 | SALA DE ENTRENAMIENTO |
| O7:P11 | SALA DE REUNIONES |
| K8:N11 | RECEPCION |
| R8:U11 | CUARTO ELECTRICO |
| W8:X11 | CUARTO DE A/C |
| Y7:Z9 | OFICINA DE IT |
| Y10:Z11 | DEPOSITO IT |
| A12:A14 | BAÑO DE HOMBRES |
| Y13:Z13 | WAR ROOM |
| A15:A16 | CUARTO A/C |
| A17:A19 | SALA DE REUNIONES |
| A20:A22 | OFICINA GERENCIA 01 |
| Y21:Z22 | OFICINA GERENCIA 04 |
| A23:A25 | OFICINA GERENCIA 02 |
| Y23:Z25 | OFICINA DE GERENCIA 05 |
| A26:G30 | OFICINA DE GERENCIA 03 |
| H26:J30 | HR162 / 166 |
| L26:N30 | Supervisor 163 |
| O26:Q30 | Supervisor 164 |
| S26:U30 | Supervisor 165 |
| V26:Z30 | OFICINA DE GERENCIA 06 |

**Posiciones de puestos en el grid:**
- Columnas F, I, L, O, R, U están vacías (pasillos/muros)
- Filas 13-17: Puestos 1-70
- Filas 20-24: Puestos 71-140
- Columnas Y-Z filas 14-20: Puestos 141-151 (IT)
- Columnas D-H filas 9-10: Puestos 152-161 (Training room)
- D7: Puesto 167

### Hoja "Seats Allocation" (176 filas de datos)
Columnas: A=Seat No., B=Name, C=Brigadista, D=Notas-Salud
- El Seat No. coincide con el número en el grid del Floor plan
- Ejemplos: Seat "1" → Brig=Ricardo Gutiérrez; Seat "41" → Name=Lizmarie Tejeira, Brig=Amir Abad

### Hoja "Sheet1" (47 filas)
Columnas: A=Name, B=Department, C=Title
- Departments: Finance, IT, ENS, Title, IBC, CaseAware, VS360
- Se une con Seats Allocation por nombre

### Hoja "Brigadistas" (13 filas)
Columnas: A=Seat No, B=Nombre, C=Departamento

## Decisiones Tomadas
1. **Base visual**: Grid del Excel (no el PDF) — el PDF es plano estructural sin datos de puestos
2. **Layout**: CSS Grid 27x76 que replica el Excel exactamente
3. **Interacción**: Click → modal con info; Hover → tooltip rápido
4. **Filtros**: Dropdown por departamento + búsqueda por nombre + contador
5. **Colores por departamento**: Finance=verde, IT=azul, ENS=naranja, Title=púrpura, IBC=amarillo, CaseAware=rosa, VS360=teal, Vacío=gris
6. **Despliegue**: HTML en OneDrive → shortcut en SharePoint

## Datos Mostrados por Puesto
| Campo | Fuente |
|-------|--------|
| Nombre | Seats Allocation → col B |
| Departamento | Sheet1 → col B |
| Puesto/Título | Sheet1 → col C |
| Brigadista | Seats Allocation → col C |
| Notas | Seats Allocation → col D |

## Archivos a Crear
1. `generar_mapa.py` — Lee Excel con openpyxl, genera `floor_plan_data.json`
2. `floor_plan.html` — HTML autocontenido con JSON embebido, mapa interactivo
3. `floor_plan_data.json` — Datos generados (intermedio)

## Estado
- [x] Análisis completo del Excel (4 hojas, celdas combinadas, colores, posiciones)
- [x] Análisis del PDF (concluido: plano estructural, no usable)
- [x] Plan final aprobado
- [ ] Crear `generar_mapa.py`
- [ ] Crear `floor_plan.html`
- [ ] Ejecutar y verificar
