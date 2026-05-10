; Inno Setup 脚本 — 电子表格数据分析系统安装包
; GitHub Actions 中由 Minionguyjpro/Inno-Setup-Action 执行

#define MyAppName "电子表格数据分析系统"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "数据分析系统"
#define MyAppExeName "数据分析系统.exe"
#define MyAppURL "https://github.com/mozengfu/shujufenxi"

[Setup]
AppId={{A3B5C7D9-1234-5678-90AB-CDEF12345678}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=数据分析系统-安装包
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\数据分析系统\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\数据分析系统\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
