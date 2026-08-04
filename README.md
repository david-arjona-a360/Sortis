# SORTIS — Floor Plan Desktop

Aplicación de escritorio para el mapa de asientos (floor plan) y la gestión de
solicitudes de cambio de personal de a360inc. Incluye identificación
automática del usuario de Windows (sin contraseñas), control de roles y
sincronización de datos a través de OneDrive.

## Descargas

**SORTIS v2.0.1** — descarga `SORTIS_v2.0.1.zip` desde la sección **Releases**
de este repositorio (<https://github.com/david-arjona-a360/Sortis/releases>).

> El instalador `.exe` (Inno Setup) está en pausa temporalmente: Microsoft
> Defender lo marca como falso positivo mientras no se firme con un
> certificado confiable o IT despliegue una regla de permiso. Se distribuye
> el ZIP hasta resolverlo.

## Requisitos por equipo

- Windows 10/11 de 64 bits.
- OneDrive for Business de a360inc instalado e iniciado con la cuenta
  corporativa.
- Acceso (lectura/escritura) a la carpeta compartida
  `OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN`.

> No se necesita Python, .NET ni permisos de administrador.

## Instalación

1. Descarga `SORTIS_v2.0.1.zip` desde **Releases**.
2. Extrae el contenido en la carpeta `%LOCALAPPDATA%\SORTIS`
   (usa *Win+R* y pega `%LOCALAPPDATA%`; si no existe la subcarpeta
   `SORTIS`, créala). Es importante usar **esa** ruta: es donde la app tiene
   permiso de ejecución permitido en la red de a360inc.
3. Ejecuta `SORTIS.exe` desde esa carpeta.
4. Opcional: crea un acceso directo a `SORTIS.exe` en el escritorio o menú
   Inicio.
5. La app se instala sin Python, .NET ni permisos de administrador.

> Antes de actualizar una instalación existente, cierra la app y borra el
> contenido anterior de `%LOCALAPPDATA%\SORTIS` (o sobrescríbelo). La carpeta
> `config\` local se regenera; los datos del mapa viven en OneDrive.

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

## Microsoft Defender / antivirus (importante)

Microsoft Defender a veces marca la app compilada como
`Trojan:Win32/Wacatac.B!ml` o `Wacatac.C!ml`. Es un **falso positivo**: el
sufijo `!ml` indica detección heurística de *machine learning*, no un virus
real. Ocurre porque los ejecutables empaquetados con PyInstaller (sin firma
digital) son usados también por malware, y la heurística los agrupa.

La versión 2.0.1 ya mitiga esto:

- Se añadieron **metadatos de versión** e **icono** al ejecutable.
- El ejecutable se firma digitalmente con el certificado interno de A360
  (`CN=Inventory Manager Dev`) al compilar.
- Se distribuye como **ZIP** (un archivo `.zip` no dispara la heurística).

Qué hacer si aparece la alerta:

- Si ocurre al extraer/ejecutar, confirma que la app esté en
  `%LOCALAPPDATA%\SORTIS` (ruta permitida en la red).
- En **Windows Security → Protection history**, si la marca, usa
  **Restore** (la app es la propia herramienta interna).
- Para instalaciones corporativas, contacta a IT para que despliegue una
  **regla de permiso / exclusión** de Defender para la app, o un certificado
  de firma de código confiable (Azure Trusted Signing) con el que firmar el
  instalador y poder volver al formato `.exe`.

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
