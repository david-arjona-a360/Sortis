# SORTIS - Mapa Interactivo de Oficina Piso 7

## Objetivo
Crear una app web interactiva (HTML/JS autocontenido) que muestre el mapa de oficina de SORTIS Piso 7, mostrando info de la persona en cada puesto al hacer click. Los managers pueden editar asignaciones desde la app.

## GitHub
https://github.com/david-arjona-a360/Sortis

## Archivos Fuente
- **Excel**: `C:\Users\david.arjona\OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN\SORTIS_FLOOR_PLAN.xlsx`
- **PDF** (analizado, NO se usa): `A02_DISTRIBUCIÓN_OSO (2).pdf`

## Arquitectura

### Modo Local (sin SharePoint)
- `generar_mapa.py` lee Excel → genera JSON + HTML con datos embebidos
- HTML funciona con `file://` o cualquier servidor estatico

### Modo SharePoint (produccion)
- HTML se incrusta en SharePoint Site Page via Embed web part
- `data.json` se almacena en SharePoint Document Library
- HTML lee/escribe via SharePoint REST API (cookie auth, sin Azure AD)
- Cambios de managers se reflejan instantaneamente
- SharePoint maneja version history automaticamente

### Para activar SharePoint
En `floor_plan.html`, cambiar:
```javascript
var SHAREPOINT_SITE = '';  // → var SHAREPOINT_SITE = '/sites/YOURSITE/';
var DATA_FILE_PATH = '/sites/YOURSITE/Shared Documents/FloorPlan/data.json';
```

## Estructura del Excel

### Hoja "Floor plan" (76 filas x 27 columnas, A-AA)
Grid visual de la oficina. Celdas combinadas = areas/habitaciones. Celdas individuales = puestos numerados 1-167.

**Areas principales:**
COMEDOR, RECEPCION, SALA DE REUNIONES, SALA DE ENTRENAMIENTO, OFICINA DE IT, OFICINA GERENCIA 01-06, CUARTO DE IT, ARCHIVE, WAR ROOM, BAÑOS, LOCKERS, CUARTO A/C, CUARTO ELECTRICO, HR162, Supervisors 163-165

### Hoja "Seats Allocation" (176 filas)
Columnas: A=Seat No., B=Name, C=Brigadista, D=Notas-Salud

### Hoja "Sheet1" (47 filas)
Columnas: A=Name, B=Department, C=Title
Departments: Finance, IT, ENS, Title, IBC, CaseAware, VS360, Firm Solutions

### Hoja "Brigadistas" (13 filas)
Columnas: A=Seat No, B=Nombre, C=Departamento

## Funcionalidades

### Visualizacion
- CSS Grid 27x76 replica el layout del Excel
- Colores por departamento
- Tooltip al hover con nombre + departamento
- Modal al click con info completa
- Filtro por departamento, brigadista y busqueda por nombre
- Contador: puestos mostrados / ocupados / vacios

### Edicion (SharePoint mode)
- Click en puesto vacio → dropdown con autocomplete para asignar persona
- Click en puesto ocupado → info + botones "Reasignar" y "Desasignar"
- Confirmacion antes de desasignar
- Auto-guardado cada 2 segundos despues de un cambio
- Toast notifications para feedback
- Timestamp de ultima actualizacion visible

### SharePoint Integration
- Lee data.json via REST API al cargar
- Escribe data.json via REST API al guardar
- Indicador "Conectado a SharePoint" en topbar
- Fallback a datos locales si SharePoint no esta disponible
- Usa cookie auth (sin Azure AD app registration)

## Datos Mostrados por Puesto
| Campo | Fuente |
|-------|--------|
| Nombre | Seats Allocation → col B |
| Departamento | Sheet1 → col B |
| Puesto/Titulo | Sheet1 → col C |
| Brigadista | Seats Allocation → col C |
| Notas | Seats Allocation → col D |

## Archivos
| Archivo | Descripcion |
|---------|-------------|
| `generar_mapa.py` | Lee Excel, genera JSON + HTML |
| `floor_plan.html` | Mapa interactivo autocontenido |
| `.gitignore` | Excluye JSON, xlsx, cache |
| `PROGRESO.md` | Este documento |

## Datos Generados (en JSON)
- rooms: array de areas/habitaciones con posiciones
- seats: array de puestos con personas asignadas
- departments: lista de departamentos unicos
- brigadistas: lista de brigadistas unicos
- people_directory: directorio de todas las personas (nombre, dept, titulo)
- total_seats: total de puestos
- occupied_seats: puestos ocupados
- timestamp: fecha/hora de ultima generacion

## Estado
- [x] Analisis completo del Excel (4 hojas, celdas combinadas, colores, posiciones)
- [x] Analisis del PDF (concluido: plano estructural, no usable)
- [x] Plan original aprobado y ejecutado
- [x] generar_mapa.py con people_directory, timestamp, brigadistas
- [x] floor_plan.html con edicion, SharePoint REST API, brigadista filter
- [x] .gitignore actualizado
- [ ] Configurar SharePoint Site Page + Document Library
- [ ] Subir data.json a SharePoint
- [ ] Configurar SHAREPOINT_SITE en el HTML
- [ ] Probar en SharePoint con managers
