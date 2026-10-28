@echo off
if /I "%~1"=="--inside" goto run
"%ComSpec%" /d /k ""%~f0" --inside"
exit /b
:run
title PinjamLab v5 - Upload Aman ke GitHub
cd /d "%~dp0"
if not exist "%~dp0scripts\upload-ke-github.ps1" (
  echo File scripts\upload-ke-github.ps1 tidak ditemukan.
  echo Ekstrak semua isi ZIP ke folder biasa sebelum menjalankan.
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\upload-ke-github.ps1"
set "UP_EXIT=%errorlevel%"
echo.
if "%UP_EXIT%"=="0" (echo SELESAI: Periksa hasil GitHub pada alamat repository.) else (echo BELUM BERHASIL: Baca pesan error di atas. Tidak ada force push.)
echo Jendela boleh ditutup setelah pemeriksaan. Ketik exit lalu Enter.
exit /b %UP_EXIT%
