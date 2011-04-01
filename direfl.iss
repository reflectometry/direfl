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

; NOTE: The Quick Start Pack for the Inno Setup Compiler needs to be installed
; with the Preprocessor add-on selected to support use of #define statements.
#define MyAppName "DiRefl"
#define MyAppNameLowercase "direfl"
#define MyGroupFolderName "DANSE"
#define MyAppPublisher "University of Maryland"
#define MyAppURL "http://www.reflectometry.org/danse/"
#define MyAppFileName "direfl.exe"
#define MyIconFileName "direfl.ico"
#define MyReadmeFileName "README.txt"
#define MyLicenseFileName "LICENSE.txt"
#define Space " "
; Use updated version string if present in the include file.  It is expected that the DiRefl
; build script will create this file using the application's internal version string to create
; a define statement in the format shown below.
#define MyAppVersion "0.0.0"
#ifexist "direfl.iss-include"
    #include "direfl.iss-include"
#endif

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
OutputManifestFile={#MyAppNameLowercase}-{#MyAppVersion}-win32-manifest.txt
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

; The following Pascal function checks for the presence of the VC++ 2008 DLL folder on the target system
; to determine if the VC++ 2008 Redistributable kit needs to be installed.
[Code]
function InstallVC90CRT(): Boolean;
begin
    Result := not DirExists('C:\WINDOWS\WinSxS\x86_Microsoft.VC90.CRT_1fc8b3b9a1e18e3b_9.0.21022.8_x-ww_d08d0375');
end;

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
; This section creates shortcuts.
; - {group} refers to shortcuts in the Start Menu.
; - {commondesktop} refers to shortcuts on the desktop.
; - {userappdata} refers to shortcuts in the Quick Start menu on the tool bar.
Name: "{group}\Launch {#MyAppName}"; Filename: "{app}\{#MyAppFileName}"; IconFilename: "{app}\{#MyIconFileName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}{#Space}{#MyAppVersion}"; Filename: "{app}\{#MyAppFileName}"; Tasks: desktopicon; WorkingDir: "{app}"; IconFilename: "{app}\{#MyIconFileName}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}{#Space}{#MyAppVersion}"; Filename: "{app}\{#MyAppFileName}"; Tasks: quicklaunchicon; WorkingDir: "{app}"; IconFilename: "{app}\{#MyIconFileName}"

[Run]
Filename: "{app}\{#MyAppFileName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#MyReadmeFileName}"; Description: "Read Release Notes"; Verb: "open"; Flags: shellexec waituntilterminated skipifdoesntexist postinstall skipifsilent unchecked
; Install the Microsoft C++ DLL redistributable package if it is provided and the DLLs are not present on the target system.
; Note that the redistributable package is included if the app was built using Python 2.6 or 2.7, but not with 2.5.
; Parameter options:
; - for silent install use: "/q"
; - for silent install with progress bar use: "/qb"
; - for silent install with progress bar but disallow cancellation of operation use: "/qb!"
; Note that we do not use the postinstall flag as this would display a checkbox and thus require the user to decide what to do.
Filename: "{app}\vcredist_x86.exe"; Parameters: "/qb!"; WorkingDir: "{tmp}"; StatusMsg: "Installing Microsoft Visual C++ 2008 Redistributable Package ..."; Check: InstallVC90CRT(); Flags: skipifdoesntexist waituntilterminated

[UninstallDelete]
; Delete directories and files that are dynamically created by the application (i.e. at runtime).
Type: filesandordirs; Name: "{app}\.matplotlib"
Type: files; Name: "{app}\*.exe.log"
; The following is a workaround for the case where the application is installed and uninstalled but the
;{app} directory is not deleted because it has user files.  Then the application is installed into the
; existing directory, user files are deleted, and the application is un-installed again.  Without the
; directive below, {app} will not be deleted because Inno Setup did not create it during the previous
; installation.
Type: dirifempty; Name: "{app}"
