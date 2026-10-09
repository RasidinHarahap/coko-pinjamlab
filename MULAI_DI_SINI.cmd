@echo off
if /I "%~1"=="--inside" goto run
"%ComSpec%" /d /k ""%~f0" --inside"
exit /b
:run
title PinjamLab - Jalankan Website
cd /d "%~dp0"
if not exist "%~dp0scripts\jalankan.ps1" goto missing
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\jalankan.ps1"
set "taskExitCode=%errorlevel%"
echo.
if "%taskExitCode%"=="0" (echo Website siap. Jendela ini boleh ditutup; website tetap berjalan.) else (echo Proses belum berhasil. Pesan kesalahan tetap terlihat di atas.)
echo Log: .local\LOG_MULAI.txt
echo Untuk keluar dari jendela ini, ketik exit lalu Enter.
exit /b %taskExitCode%
:missing
echo File scripts\jalankan.ps1 tidak ditemukan.
echo Klik kanan ZIP, pilih Extract All / Ekstrak Semua, lalu jalankan dari folder hasil ekstrak.
echo Jangan menjalankan CMD langsung dari dalam ZIP.
exit /b 1
