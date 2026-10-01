@echo off
chcp 65001 >nul
set "EXE_PATH=%~dp0neckhurts.exe"
echo Activation du lancement automatique...
REG ADD "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /V "NeckhurtsBot" /t REG_SZ /F /D "\"%EXE_PATH%\"" >nul
echo.
echo [SUCCES] Le lancement automatique de Neckhurts a ete ACTIVE !
echo Le bot s'ouvrira tout seul lors du prochain demarrage de Windows.
echo.
pause
