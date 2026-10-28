param([switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskStartedTranscript = $false
Push-Location -LiteralPath $taskRoot
try {
    New-Item -ItemType Directory -Force -Path ".local" | Out-Null
    Start-Transcript -Path ".local\LOG_MULAI.txt" -Force | Out-Null
    $taskStartedTranscript = $true
    Write-Host "PINJAMLAB - WEBSITE PEMINJAMAN ALAT" -ForegroundColor Green
    Write-Host ""
    $taskRequired = @("Dockerfile", "compose.yaml", "requirements.txt", "app.py", "database.py", "rules.py", "init_db.py", "schema.sql", "static\style.css", "static\app.js", "static\favicon.svg", "templates\base.html", "templates\macros.html", "templates\dashboard.html", "templates\equipment_list.html", "templates\equipment_form.html", "templates\loan_list.html", "templates\loan_form.html", "templates\return_form.html", "templates\receipt.html", "templates\activity.html", "templates\error.html", "scripts\common.ps1", "scripts\setup-env.ps1", "scripts\seed_demo.py")
    foreach ($taskFile in $taskRequired) {
        if (-not (Test-Path -LiteralPath $taskFile -PathType Leaf)) {
            throw "File $taskFile tidak ditemukan. Ekstrak SEMUA isi ZIP ke folder baru, lalu buka MULAI_DI_SINI.cmd dari sana."
        }
    }
    . "$PSScriptRoot\common.ps1"
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker Desktop belum terpasang atau PATH belum diperbarui. Pasang Docker Desktop, restart laptop, lalu buka Docker Desktop dan coba lagi."
    }
    Write-Host "[1/4] Memeriksa Docker..."
    $taskDocker = Invoke-TaskNative -FilePath "docker" -Arguments @("info", "--format", "{{.OSType}}") -AllowFailure -Quiet
    if ($taskDocker.ExitCode -ne 0) {
        throw "Docker belum berjalan. Buka Docker Desktop, tunggu Engine running, lalu klik MULAI_DI_SINI.cmd lagi."
    }
    if (($taskDocker.Lines -join "").Trim() -ne "linux") {
        throw "Pilih Linux containers di Docker Desktop, lalu coba lagi."
    }
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "version") | Out-Null
    & "$PSScriptRoot\setup-env.ps1"
    Write-Host "[2/4] Membangun dan menjalankan website. Pertama kali perlu internet; tunggu hingga selesai..."
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "up", "--build", "-d", "--wait", "--wait-timeout", "180") | Out-Null
    Write-Host "[3/4] Menyiapkan data contoh jika inventaris masih kosong..."
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "exec", "-T", "web", "python", "scripts/seed_demo.py") | Out-Null
    $taskPortResult = Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "port", "web", "8000") -Quiet
    $taskPortLine = ($taskPortResult.Lines -join "").Trim()
    if ($taskPortLine -notmatch '^127\.0\.0\.1:(\d+)$') {
        throw "Alamat website tidak dapat dibaca dari Docker: $taskPortLine"
    }
    $taskUrl = "http://127.0.0.1:$($Matches[1])"
    $taskHealth = Invoke-RestMethod -Uri "$taskUrl/health" -TimeoutSec 15
    if ($taskHealth.status -ne "ok") { throw "Website belum sehat. Periksa Docker Desktop dan log." }
    Write-Host "[4/4] Website siap." -ForegroundColor Green
    Invoke-TaskNative -FilePath "docker" -Arguments @("compose", "ps") | Out-Null
    Write-Host ""
    Write-Host "BUKA: $taskUrl" -ForegroundColor Green
    Write-Host "Data contoh berlabel DEMO. Perubahan data tersimpan di volume Docker."
    Write-Host "Sesudah restart laptop: buka Docker Desktop, lalu klik MULAI_DI_SINI.cmd lagi."
    if (-not $NoBrowser) {
        try { Start-Process $taskUrl } catch { Write-Host "Buka alamat di atas secara manual di browser." }
    }
} catch {
    Write-Host ""
    Write-Host "BELUM BERHASIL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Jika muncul port already allocated, ubah APP_PORT di .env menjadi 8081, lalu coba lagi."
    Write-Host "Log tersimpan di .local\LOG_MULAI.txt. Jendela CMD tetap terbuka."
    throw
} finally {
    if ($taskStartedTranscript) { Stop-Transcript | Out-Null }
    Pop-Location
}
