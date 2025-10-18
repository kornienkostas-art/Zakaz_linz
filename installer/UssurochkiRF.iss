; Inno Setup script for UssurochkiRF application
; Produces a Windows installer (EXE) that installs the app into Program Files
; and creates Start Menu and Desktop shortcuts.

#define MyAppName "UssurochkiRF"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "UssurOchki RF"
#define MyAppURL "https://example.local"
#define MyAppExeName "UssurochkiRF.exe"

[Setup]
AppId={{6A3F3B14-4D86-4D63-9D25-9E8D1B5C2B33}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=installer\Output
OutputBaseFilename={#MyAppName}-Setup-{#MyAppVersion}
SetupIconFile=app\assets\favicon.ico
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x86 x64
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "autostart"; Description: "Start {#MyAppName} automatically with Windows"; GroupDescription: "Startup options:"; Flags: unchecked

[Files]
; Copy all built files from dist\UssurochkiRF
Source: "dist\UssurochkiRF\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
; If using one-file build, you can alternatively point to dist\UssurochkiRF.exe
; Source: "dist\UssurochkiRF.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Registry]
; Optional: add Run key for autostart if task selected
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Code]
; Optional code section if we need more advanced logic later