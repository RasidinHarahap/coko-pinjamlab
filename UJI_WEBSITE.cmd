@echo off
if /I "%~1"=="--inside" goto run
"%ComSpec%" /d /k ""%~f0" --inside"
exit /b
:run
title PinjamLab - Uji Website dan Database
cd /d "%~dp0"
if not exist "%~dp0scripts\uji.ps1" goto missing
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\uji.ps1"
set "taskExitCode=%errorlevel%"
echo.
if "%taskExitCode%"=="0" (echo Pengujian selesai. Website tetap berjalan.) else (echo Pengujian belum berhasil. Periksa pesan di atas.)
echo Log: .local\LOG_UJI.txt
echo Untuk keluar dari jendela ini, ketik exit lalu Enter.
exit /b %taskExitCode%
:missing
echo File scripts\uji.ps1 tidak ditemukan. Ekstrak semua isi ZIP terlebih dahulu.
exit /b 1
