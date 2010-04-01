; -- direfl.iss -- an Inno Setup Script for DiRefl

; This script is used by the Inno Setup Compiler to build a Windows XP
; installer/uninstaller for the DANSE Reflectometry application named DiRefl.
; The script is written to explicitly allow multiple versions of the
; application to be installed simulaneously in separate subdirectories such
; as "DiRefl 0.5.0", "DiRefl 0.7.2", and "DiRefl 1.0" under a group directory.

; NOTE: In order to support more than one version of the application
; installed simultaneously, the AppName, Desktop shortcut name, and Quick
; Start shortcut name must be unique among versions.  This is in addition to
; having unique names (in the more obvious places) for DefaultDirNam,
; DefaultGroupName, and output file name.

; By default, when installing DiRefl:
; - The destination folder will be "C:\Program Files\DANSE\DiRefl x.y.z"
; - A desktop icon will be created with the label "DiRefl x.y.z"
; - A quickstart icon is optional
; - A start menu folder will be created with the name DANSE -> DiRefl x.y.z
; By default, when uninstalling DiRefl x.y.z
; - The uninstall can be initiated from either the:
;   * Start menu via DANSE -> DiRefl x.y.z -> Uninstall DiRefl
;   * Start menu via Control Panel - > Add or Remove Programs -> DiRefl x.y.z
; - It will not delete the C:\Program Files\DANSE\DiRefl x.y.z folder if it
;   contains any user created files
; - It will delete any desktop or quickstart icons for DiRefl that were
;   created on installation

; NOTE: The Quick Start package add-on for the Inno Setup Compiler needs to be
; installed to support the use of #define statements.
#define MyAppName "DiRefl"
#define MyAppNameLowercase "direfl"
#define MyAppVersion "1.0.0"
#define MyGroupFolderName "DANSE"
#define MyAppPublisher "University of Maryland"
#define MyAppURL "http://www.reflectometry.org/danse/"
#define MyAppFileName "direfl.exe"
#define MyIconFileName "direfl.ico"
#define MyReadmeFileName "README-direfl.txt"
#define MyLicenseFileName "LICENSE-direfl.txt"
#define Space " "

[Setup]
; Make the AppName string unique so that other versions of the program can be installed simultaniously.
; This is done by using the name and version of the application together as the AppName.
AppName={#MyAppName}{#Space}{#MyAppVersion}
AppVerName={#MyAppName}{#Space}{#MyAppVersion}
AppPublisher={#MyAppPublisher}
ChangesAssociations=yes
; If you do not want a space in folder names, omit {#Space} or replace it with a hyphen char, etc.
DefaultDirName={pf}\{#MyGroupFolderName}\{#MyAppName}{#Space}{#MyAppVersion}
DefaultGroupName={#MyGroupFolderName}\{#MyAppName}{#Space}{#MyAppVersion}
Compression=lzma/max
SolidCompression=yes
DisableProgramGroupPage=yes
; A file extension of .exe will be appended to OutputBaseFilename.
OutputBaseFilename={#MyAppNameLowercase}-{#MyAppVersion}-win32
OutputManifestFile={#MyAppNameLowercase}-{#MyAppVersion}-manifest.txt
SetupIconFile={#MyIconFileName}
LicenseFile={#MyLicenseFileName}
SourceDir=.
OutputDir=.
PrivilegesRequired=none
;InfoBeforeFile=display_before_install.txt
;InfoAfterFile=display_after_install.txt

; The App*URL directives are for display in the Add/Remove Programs control panel and are all optional
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; This script assumes that the output from the previously run py2exe packaging process is in .\dist\...
; NOTE: Don't use "Flags: ignoreversion" on any shared system files
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{group}\Launch {#MyAppName}"; Filename: "{app}\{#MyAppFileName}"; IconFilename: "{app}\{#MyIconFileName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}{#Space}{#MyAppVersion}"; Filename: "{app}\{#MyAppFileName}"; Tasks: desktopicon; WorkingDir: "{app}"; IconFilename: "{app}\{#MyIconFileName}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}{#Space}{#MyAppVersion}"; Filename: "{app}\{#MyAppFileName}"; Tasks: quicklaunchicon; WorkingDir: "{app}"; IconFilename: "{app}\{#MyIconFileName}"

[Run]
Filename: "{app}\{#MyAppFileName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#MyReadmeFileName}"; Description: "Read Release Notes"; Verb: "open"; Flags: shellexec waituntilterminated skipifdoesntexist postinstall skipifsilent unchecked
