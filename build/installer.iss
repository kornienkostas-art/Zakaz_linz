; Inno Setup Script for OrdersApp Installer
; Requirements:
; 1) Build the app with PyInstaller into dist\OrdersApp\
; 2) Install Inno Setup (https://jrsoftware.org/isinfo.php) and run:
;    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build\installer.iss

#define MyAppName "OrdersApp"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company"
#define MyAppExeName "OrdersApp.exe"

[Setup]
AppId={{3B8F51CE-6C4D-4A4E-9F15-1F5ED450A8B1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=OrdersAppSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkablealone

[Files]
Source: "..\dist\OrdersApp\*"; DestDir: "{app}"; Flags: ignoreversion recurses createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent