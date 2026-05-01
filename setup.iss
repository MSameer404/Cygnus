; Inno Setup Script for Cygnus
; Download Inno Setup from: https://jrsoftware.org/isdl.php

[Setup]
AppId={{C7B8E9A1-F2D3-4B5C-BD6E-8F9A0B1C2D3E}}
AppName=Cygnus
AppVersion=2.3.0
AppPublisher=Mohammad Sameer
DefaultDirName={autopf}\Cygnus
DefaultGroupName=Cygnus
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=Cygnus_Setup
SetupIconFile=src\app\assets\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; IMPORTANT: Point this to your PyInstaller output folder (if using --onedir)
; Or the single .exe file (if using --onefile)
Source: "dist\Cygnus.exe"; DestDir: "{app}"; Flags: ignoreversion
; Include any extra files if not bundled in the exe
; Source: "src\app\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Cygnus"; Filename: "{app}\Cygnus.exe"; AppUserModelID: "cygnus.study.timer.1.0"
Name: "{autodesktop}\Cygnus"; Filename: "{app}\Cygnus.exe"; Tasks: desktopicon; AppUserModelID: "cygnus.study.timer.1.0"

[Run]
Filename: "{app}\Cygnus.exe"; Description: "{cm:LaunchProgram,Cygnus}"; Flags: nowait postinstall skipifsilent
