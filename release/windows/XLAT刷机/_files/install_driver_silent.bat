@echo off
setlocal EnableExtensions

set "DRVDIR=%~dp0driver"
if not exist "%DRVDIR%\stlink_dbg_winusb.inf" exit /b 1

REM Clear any driver-block set by the uninstall tool, so the install is allowed
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceInstall\Restrictions" /f >nul 2>&1

pushd "%DRVDIR%"

where pnputil >nul 2>&1
if errorlevel 1 goto legacy

pnputil /add-driver *.inf /install
if errorlevel 1 goto legacy
pnputil /scan-devices >nul 2>&1
popd
set "DP_RESULT=0"
goto copyconfig

:legacy
if /I "%PROCESSOR_ARCHITECTURE%"=="AMD64" goto amd64
if /I "%PROCESSOR_ARCHITEW6432%"=="AMD64" goto amd64
dpinst_x86.exe /q /f
set "DP_RESULT=%errorlevel%"
goto done

:amd64
dpinst_amd64.exe /q /f
set "DP_RESULT=%errorlevel%"

:done
popd

:copyconfig
set "STLINK_CFG=%ProgramFiles(x86)%\stlink\config\chips"
if "%STLINK_CFG%"=="\stlink\config\chips" set "STLINK_CFG=%ProgramFiles%\stlink\config\chips"
if not exist "%STLINK_CFG%" mkdir "%STLINK_CFG%"
copy /Y "%~dp0config\chips\*.chip" "%STLINK_CFG%\" >nul
exit /b %DP_RESULT%
