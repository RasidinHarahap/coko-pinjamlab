$ErrorActionPreference = "Stop"
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskEnv = Join-Path $taskRoot ".env"
if (Test-Path $taskEnv) { Write-Host ".env sudah ada; tidak ditimpa."; return }
$taskBytes = New-Object byte[] 32
$taskRng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try { $taskRng.GetBytes($taskBytes) } finally { $taskRng.Dispose() }
$taskSecret = -join ($taskBytes | ForEach-Object { $_.ToString("x2") })
"SECRET_KEY=$taskSecret`nAPP_PORT=8080`n" | Set-Content -Path $taskEnv -Encoding ASCII
Write-Host ".env berhasil dibuat. Simpan secara lokal; jangan unggah ke GitHub."
