; Interactive Office Map Inno Setup Installer
; Requires Inno Setup 6+

#define MyAppName "Interactive Office Map"
#define MyAppVersion "2.2.2"
#define MyAppPublisher "a360inc"
#define MyAppURL "https://a360inc.sharepoint.com"
#define MyAppExeName "SORTIS.exe"

[Setup]
; AppId intentionally UNCHANGED from the SORTIS v2.0.x installer so existing
; installations upgrade in place.
AppId={{B8F3A2D1-5E4C-4A7B-9D6F-1C2E3A4B5C6D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
; Install folder stays {localappdata}\SORTIS: it is the execution path that
; a360inc IT allows on the corporate network.
DefaultDirName={localappdata}\SORTIS
DefaultGroupName={#MyAppName}
SetupIconFile=..\assets\blueprint.ico
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename=Interactive_Office_Map_Setup_v{#MyAppVersion}
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
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove the first-run marker so the user sees the setup requirements
; guidance again after a reinstall.
Filename: "{cmd}"; Parameters: "/c if exist ""{localappdata}\SORTIS\config.json"" del ""{localappdata}\SORTIS\config.json"""; Flags: runhidden

[Code]
function InitializeSetup: Boolean;
begin
  Result := True;
end;
