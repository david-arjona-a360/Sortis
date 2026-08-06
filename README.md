# Interactive Office Map — Floor Plan Desktop

Aplicación de escritorio para el mapa de asientos (floor plan) y la gestión de
solicitudes de cambio de personal de a360inc. Incluye identificación
automática del usuario de Windows (sin contraseñas), control de roles y
sincronización de datos a través de OneDrive.

## Descargas

**Interactive Office Map v2.2.0** — descarga el instalador
`Interactive_Office_Map_Setup_v2.2.0.exe` desde la sección **Releases** de
este repositorio (<https://github.com/david-arjona-a360/Sortis/releases>).

> Si Microsoft Defender marca el instalador o el ejecutable, es un falso
> positivo (heurística ML sobre ejecutables PyInstaller sin firma). El
> administrador/IT gestiona la excepción de Defender correspondiente.

## Requisitos por equipo

- Windows 10/11 de 64 bits.
- OneDrive for Business de a360inc instalado e iniciado con la cuenta
  corporativa.
- Acceso (lectura/escritura) a la carpeta compartida
  `OneDrive - a360inc\PTY Files - Documents\FLOOR PLAN`.

> No se necesita Python, .NET ni permisos de administrador.

## Instalación

1. Descarga `Interactive_Office_Map_Setup_v2.2.0.exe` desde **Releases**.
2. Ejecuta el instalador (no requiere permisos de administrador). Instala en
   `%LOCALAPPDATA%\SORTIS`, la ruta con permiso de ejecución permitido en la
   red de a360inc.
3. La app se abre al terminar la instalación. También quedan accesos en el
   menú Inicio y (opcional) en el escritorio.
4. La app se instala sin Python, .NET ni permisos de administrador.

> Para actualizar una instalación existente, ejecuta el nuevo instalador sobre
> la misma versión (mismo AppId de Inno Setup): se actualiza en su sitio. La
> carpeta `config\` local se regenera; los datos del mapa viven en OneDrive.

## Primer arranque

La primera vez que ejecutas la aplicación aparece un mensaje **Setup
Requirements** (en inglés):

```
This application requires access to the following OneDrive/SharePoint folder:

    - PTY Files - Documents\FLOOR PLAN

Please ensure:
    1. OneDrive is synchronized
    2. This folder exists in your OneDrive
    3. Files are available locally (not cloud-only)
```

- Lee el mensaje y pulsa **OK**.
- La app comprueba tu OneDrive. Si todo está bien, se abre el mapa.
- Si falta la carpeta requerida, aparece un diálogo **Configuration Error** y
  la app se cierra. Arregla tu OneDrive y vuelve a abrirla.
- Esta validación se ejecuta **en cada arranque**. El mensaje de requisitos
  solo aparece la primera vez; para verlo de nuevo (p. ej. tras reinstalar),
  borra el archivo `%LOCALAPPDATA%\SORTIS\config.json`.

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
`Trojan:Win32/Wacatac.B!ml`, `Wacatac.C!ml` o `Wacatac.F!ml`. Es un **falso
positivo**: el sufijo `!ml` indica detección heurística de *machine learning*,
no un virus real. Ocurre porque los ejecutables empaquetados con PyInstaller
(sin firma digital) son usados también por malware, y la heurística los
agrupa.

El build actual ya reduce mucho este riesgo: el bundle es mínimo (~48
archivos / 55 MB, solo Qt Core/Gui/Widgets/PrintSupport y openpyxl), sin
DLLs de terceros ni paquetes innecesarios, y con metadatos de versión/icono.

Qué hacer si aparece la alerta:

- Confirma que la app esté instalada en `%LOCALAPPDATA%\SORTIS` (ruta
  permitida en la red).
- En **Windows Security → Protection history**, si la marca, usa **Restore**
  (la app es la propia herramienta interna).
- Para instalaciones corporativas, el **administrador/IT** despliega una
  **regla de permiso / exclusión** de Defender para la app o el instalador.
  Esa gestión se hace manualmente por IT, no en el repo.

La mitigación definitiva (opcional, fuera de este alcance) es firmar el
instalador con un certificado de firma de código confiable (Azure Trusted
Signing).

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
