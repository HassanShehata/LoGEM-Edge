[Setup]
AppName=LoGEM
AppVersion=1.0
DefaultDirName={pf}\LoGEM
DefaultGroupName=LoGEM
OutputBaseFilename=LoGEM-Installer
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\logem\logem.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\logem\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\LoGEM"; Filename: "{app}\logem.exe"
