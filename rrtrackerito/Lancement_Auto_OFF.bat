@echo off
chcp 65001 >nul
echo Desactivation du lancement automatique...
REG DELETE "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /V "RRTrackerito" /f >nul 2>&1
echo.
echo [SUCCES] Le lancement automatique de RR Trackerito a ete DESACTIVE !
echo Le bot ne s'ouvrira plus tout seul. Vous devrez lancer run_invisible.vbs pour le lancer sans fenetre.
echo.
pause
