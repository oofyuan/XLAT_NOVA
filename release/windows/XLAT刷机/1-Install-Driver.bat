@echo off
setlocal EnableExtensions

fltmc >nul 2>&1
if errorlevel 1 (
    echo Requesting administrator privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

set "DRVDIR=%~dp0_files\driver"
if not exist "%DRVDIR%\stlink_dbg_winusb.inf" (
    echo Driver files not found. Please keep the _files folder intact.
    pause
    exit /b 1
)

echo ============================================
echo    XLAT one-click flash - Install ST-LINK driver
echo ============================================
echo.

REM Clear any driver-block set by the uninstall tool, so the install is allowed
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceInstall\Restrictions" /f >nul 2>&1

pushd "%DRVDIR%"
where pnputil >nul 2>&1
if errorlevel 1 goto legacy

echo Installing driver with Windows pnputil...
pnputil /add-driver *.inf /install
if errorlevel 1 goto legacy
pnputil /scan-devices >nul 2>&1
popd
goto copyconfig

echo pnputil failed, trying ST official dpinst...
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
copy /Y "%~dp0_files\config\chips\*.chip" "%STLINK_CFG%\" >nul

echo.
echo Driver installation completed.
echo Please reconnect the USB cable, then run 2-Flash-XLAT.exe.
echo.
pause
exit /b %DP_RESULT%
