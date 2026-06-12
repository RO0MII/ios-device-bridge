; iOS Device Bridge — Inno Setup Installer Script
; Requires Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "iOS Device Bridge"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "iOS Device Bridge"
#define MyAppURL "https://github.com/anomalyco/ios-device-bridge"
#define MyAppExeName "iOSDeviceBridge.exe"

[Setup]
AppId={{B8F4A3E2-1C5D-4A6E-9F0B-7D2E8C1A3F5B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=iOSDeviceBridge_Setup_{#MyAppVersion}
SetupIconFile=icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
AlwaysRestart=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce
Name: "installusbdriver"; Description: "Install Apple Mobile Device USB driver (recommended)"; GroupDescription: "Drivers:"; Flags: checkedonce

[Files]
; Main application
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Bundled tools (libimobiledevice)
Source: "dist\tools\irecovery.exe"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "dist\tools\idevicerestore.exe"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "dist\tools\ideviceenterrecovery.exe"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "dist\tools\*.dll"; DestDir: "{app}\tools"; Flags: ignoreversion

; USB driver installer
Source: "dist\tools\libusb-1.0.dll"; DestDir: "{app}\tools"; Flags: ignoreversion

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}"
Name: "{app}\tools"
Name: "{localappdata}\iOSDeviceBridge"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Add tools to PATH for the app to find
Filename: "{cmd}"; Parameters: "/C setx PATH ""{app}\tools;%PATH%"""; Flags: runhidden waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: postinstall nowait skipifsilent shellexec

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--uninstall"; Flags: runhidden

[Code]
function InitializeSetup: Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not DirExists(ExpandConstant('{localappdata}\iOSDeviceBridge')) then
      CreateDir(ExpandConstant('{localappdata}\iOSDeviceBridge'));
  end;
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nMake sure your iPhone is connected via USB before running the application.
FinishedLabel=Setup completed successfully.%n%niOS Device Bridge will now launch.%n%nMake sure your iPhone is connected via USB and the Apple Mobile Device USB driver is installed.
