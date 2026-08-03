# SORTIS — Floor Plan Desktop

Aplicación de escritorio para el mapa de asientos (floor plan) y la gestión de
solicitudes de cambio de personal de a360inc. Incluye identificación
automática del usuario de Windows (sin contraseñas), control de roles y
sincronización de datos a través de OneDrive.

## Descargas

Instalador (Windows): ver la sección **Releases** de este repositorio
(<https://github.com/david-arjona-a360/Sortis/releases>). Descarga
`SORTIS_Setup_v2.0.0.exe`.

## Requisitos por equipo

- Windows 10/11 de 64 bits.
- OneDrive for Business de a360inc instalado e iniciado con la cuenta
  corporativa.
- Acceso (lectura/escritura) a la carpeta compartida
  `OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN`.

> No se necesita Python, .NET ni permisos de administrador.

## Instalación

1. Descarga el instalador desde **Releases**.
2. Ejecuta `SORTIS_Setup_v2.0.0.exe`.
3. Si Windows muestra **"Windows protegió su PC"** (SmartScreen), haz clic en
   **More info → Run anyway**. El instalador no está firmado digitalmente.
4. Sigue el asistente (se instala en `%LOCALAPPDATA%\SORTIS`, sin admin).
5. Acepta la opción de **crear acceso directo en el escritorio**.

## Configuración de OneDrive (importante)

La app lee los datos del mapa y las solicitudes desde OneDrive. Asegúrate de
que la carpeta esté disponible en el equipo:

1. Abre el Explorador de archivos.
2. Ve a `OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN`.
3. Clic derecho en la carpeta → **Always keep on this device**.
   (Si la carpeta está solo "en la nube", el mapa no se carga.)

## Roles y acceso

- La identidad del usuario se detecta automáticamente desde la sesión de
  Windows. No hay login ni contraseñas.
- Todos los usuarios ven el mapa, los filtros y pueden **crear solicitudes**.
- Solo los usuarios con rol **admin** ven el menú **Admin → Manage Requests**
  (aprobar/cancelar solicitudes y exportar). En esta versión, `david.arjona`
  es administrador.

## Uso

- **Mapa de asientos**: haz clic en un asiento para ver detalles y crear una
  solicitud de cambio.
- **Filtros**: por departamento y ocupación (barra superior).
- **Solicitudes (admin)**: menú **Admin → Manage Requests** — ver, completar,
  cancelar, reabrir y exportar a PDF/Excel.
- **Identidad**: tu usuario y rol se muestran en el badge superior derecho.

## Solución de problemas

Al arrancar, la app valida automáticamente (barra de estado):

| Check | Qué revisa |
|---|---|
| OneDrive | Carpeta OneDrive de a360inc encontrada |
| FLOOR PLAN | Carpeta de datos presente |
| positions.json | Archivo del mapa existe y es válido |
| requests/ | Carpeta de solicitudes existe y tiene escritura |

Si algo falla, la barra de estado lo indica. Las causas típicas son:
- OneDrive no iniciado o carpeta compartida sin sincronizar.
- Carpeta FLOOR PLAN en "solo nube" (usa *Always keep on this device*).
- Sin permiso de escritura en la carpeta compartida.

## Soporte

Para reportar problemas o solicitar funciones, abre un issue en este
repositorio o contacta al equipo de desarrollo.
