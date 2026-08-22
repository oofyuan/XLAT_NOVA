Unicode true

!define APPNAME "XLAT一键刷机"
!define APPEXE "xl-flash.exe"

!include "x64.nsh"

Name "${APPNAME}"
OutFile "XLAT一键刷机-安装.exe"
InstallDir "$LOCALAPPDATA\XLATFlash"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

Page directory
Page instfiles

Section "安装"
  SetOutPath "$INSTDIR"
  File /r "XLAT刷机\*.*"

  DetailPrint "正在安装 ST-LINK 官方驱动，请稍候..."
  ExecWait '"$INSTDIR\_files\install_driver_silent.bat"' $0
  ${If} $0 != 0
    MessageBox MB_ICONEXCLAMATION "ST-LINK 驱动自动安装失败。$\r$\n$\r$\n请稍后手动运行安装目录中的“install_driver.bat”，或把具体错误发给我。"
  ${EndIf}
  DetailPrint "驱动安装步骤完成。"

  SetOutPath "$INSTDIR"
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${APPEXE}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${APPEXE}"
  WriteUninstaller "$INSTDIR\卸载.exe"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APPNAME}"
  RMDir /r "$INSTDIR"
SectionEnd
