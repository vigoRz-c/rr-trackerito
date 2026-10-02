@echo off
chcp 65001 >nul
set "VBS_PATH=%~dp0run_invisible.vbs"
echo Activation du lancement automatique...
REG ADD "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /V "RRTrackerito" /t REG_SZ /F /D "wscript.exe \"%VBS_PATH%\"" >nul
echo.
echo [SUCCES] Le lancement automatique de RR Trackerito a ete ACTIVE !
echo Le bot s'ouvrira tout seul lors du prochain demarrage de Windows.
echo.
pause
