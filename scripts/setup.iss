; SORTIS Inno Setup Installer
; Requires Inno Setup 6+

#define MyAppName "SORTIS"
#define MyAppVersion "2.0.1"
#define MyAppPublisher "a360inc"
#define MyAppURL "https://a360inc.sharepoint.com"
#define MyAppExeName "SORTIS.exe"

[Setup]
AppId={{B8F3A2D1-5E4C-4A7B-9D6F-1C2E3A4B5C6D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
SetupIconFile=..\assets\SORTIS.ico
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename={#MyAppName}_Setup_v{#MyAppVersion}
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableDirPage=no
DisableReadyPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\SORTIS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Launch disabled by default: auto-starting the freshly-installed EXE lets
; real-time AV scan the process at its most fragile moment and can produce
; "CreateProcess failed; code 225" on clean-but-unreputed builds. Users launch
; SORTIS.exe from the Start menu / shortcut instead.

[Code]
function InitializeSetup: Boolean;
begin
  Result := True;
end;
