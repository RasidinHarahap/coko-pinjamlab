$ErrorActionPreference = "Stop"
$taskRoot = Split-Path $PSScriptRoot -Parent
& "$PSScriptRoot\jalankan.ps1" -NoBrowser
. "$PSScriptRoot\common.ps1"
$taskTranscript = $false
$taskMarkerCreated = $false
$taskMarker = "PERSIST-" + [DateTime]::Now.ToString("yyyyMMdd-HHmmss") + "-" + [Guid]::NewGuid().ToString("N").Substring(0,8)
Push-Location -LiteralPath $taskRoot
try {
    Start-Transcript -Path ".local\LOG_UJI.txt" -Force | Out-Null
    $taskTranscript = $true
    Write-Host "[1/5] Tujuh pemeriksaan integritas SQLite di database terisolasi..."
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "exec", "-T", "web", "python", "scripts/test_sqlite_integrity.py") | Out-Null
    Write-Host "[2/5] Delapan pengujian aturan peminjaman..."
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "exec", "-T", "web", "python", "scripts/test_rules.py") | Out-Null
    Write-Host "[3/5] Dua puluh tujuh pengujian aplikasi dan SQLite..."
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "exec", "-T", "web", "python", "scripts/test_app.py") | Out-Null
    Write-Host "[4/5] Tiga belas pengujian HTTP pada website yang benar-benar berjalan..."
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "exec", "-T", "web", "python", "scripts/smoke_test.py", "--base-url", "http://127.0.0.1:8000") | Out-Null
    Write-Host "[5/5] Memeriksa data tetap ada setelah container dibuat ulang..."
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "exec", "-T", "web", "python", "scripts/persistence_probe.py", "create", $taskMarker) | Out-Null
    $taskMarkerCreated = $true
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "up", "-d", "--force-recreate", "--wait", "--wait-timeout", "180") | Out-Null
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "exec", "-T", "web", "python", "scripts/persistence_probe.py", "verify", $taskMarker) | Out-Null
    Write-Host ""
    Write-Host "LULUS: 48/48 uji aplikasi/HTTP, 7/7 uji integritas SQLite + persistensi volume Docker." -ForegroundColor Green
} catch {
    Write-Host "PENGUJIAN BELUM LULUS: $($_.Exception.Message)" -ForegroundColor Red
    throw
} finally {
    if ($taskMarkerCreated) {
        try {
            $taskCleanup = Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "exec", "-T", "web", "python", "scripts/persistence_probe.py", "cleanup", $taskMarker) -AllowFailure
            if ($taskCleanup.ExitCode -ne 0) { Write-Warning "Marker uji $taskMarker belum terhapus; jalankan UJI_WEBSITE.cmd lagi setelah Docker siap." }
        } catch { Write-Warning "Marker uji $taskMarker belum terhapus: $($_.Exception.Message)" }
    }
    if ($taskTranscript) { Stop-Transcript | Out-Null }
    Pop-Location
}
