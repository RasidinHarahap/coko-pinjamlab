# Windows PowerShell 5.1+ | Git for Windows required. Optional GitHub CLI supports browser login.
$ErrorActionPreference = 'Stop'
$targetRepo = 'RasidinHarahap/coko-pinjamlab'
$branchName = 'main'
$remoteUrl = 'https://github.com/RasidinHarahap/coko-pinjamlab.git'
$sourceRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $sourceRoot 'MANIFEST_GITHUB.txt'
$cloneDir = Join-Path ([System.IO.Path]::GetTempPath()) ('pinjamlab-upload-' + [Guid]::NewGuid().ToString('N'))
$pushCompleted = $false

function Invoke-GitChecked {
    param([string[]]$GitArguments)
    & git @GitArguments
    if ($LASTEXITCODE -ne 0) { throw ('Git gagal (exit {0}): git {1}' -f $LASTEXITCODE, ($GitArguments -join ' ')) }
}

try {
    Write-Host '==========================================================' -ForegroundColor Cyan
    Write-Host ' PINJAMLAB v5.0 - UPLOAD KE GITHUB (TANPA FORCE PUSH)' -ForegroundColor Cyan
    Write-Host '==========================================================' -ForegroundColor Cyan
    Write-Host ('Repository tujuan: ' + $targetRepo)
    Write-Host ('Branch tujuan    : ' + $branchName)
    Write-Host ''

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'Git for Windows belum tersedia. Pasang dari https://git-scm.com/downloads/win lalu buka ulang file ini.'
    }
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw 'MANIFEST_GITHUB.txt tidak ditemukan. Ekstrak seluruh ZIP terlebih dahulu.'
    }
    $fileList = @(Get-Content -LiteralPath $manifestPath | Where-Object { $_ -and -not $_.StartsWith('#') })
    foreach ($relativePath in $fileList) {
        if ($relativePath -match '(^|/)\.\.(/|$)' -or $relativePath.StartsWith('/')) {
            throw ('Path manifest tidak diizinkan: ' + $relativePath)
        }
        if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot ($relativePath.Replace('/', '\'))) -PathType Leaf)) {
            throw ('File paket hilang: ' + $relativePath)
        }
    }

    # GitHub CLI is optional; Git Credential Manager in Git for Windows can also prompt login.
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        & gh auth status --hostname github.com *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Host 'Silakan login GitHub di browser (tanpa memasukkan token ke ZIP).' -ForegroundColor Yellow
            & gh auth login --hostname github.com --git-protocol https --web
            if ($LASTEXITCODE -ne 0) { throw 'Login GitHub CLI belum berhasil.' }
        }
        & gh auth setup-git
        if ($LASTEXITCODE -ne 0) { throw 'Gagal mengaktifkan autentikasi Git dari GitHub CLI.' }
    } else {
        Write-Host 'GitHub CLI tidak ditemukan. Jika diminta, selesaikan login browser melalui Git Credential Manager.' -ForegroundColor Yellow
    }

    Write-Host 'Mengambil cabang main terbaru dari GitHub...' -ForegroundColor Cyan
    Invoke-GitChecked -GitArguments @('clone', '--depth', '1', '--branch', $branchName, '--single-branch', $remoteUrl, $cloneDir)
    Write-Host ('Menyalin ' + $fileList.Count + ' file sumber yang terdaftar...')
    foreach ($relativePath in $fileList) {
        $osPath = $relativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
        $from = Join-Path $sourceRoot $osPath
        $to = Join-Path $cloneDir $osPath
        $toParent = Split-Path -Parent $to
        if (-not (Test-Path -LiteralPath $toParent)) { New-Item -ItemType Directory -Path $toParent -Force | Out-Null }
        Copy-Item -LiteralPath $from -Destination $to -Force
        Invoke-GitChecked -GitArguments @('-C', $cloneDir, 'add', '--', $relativePath)
    }
    # Intentionally do not delete files from GitHub that are absent from this ZIP.
    & git -C $cloneDir diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'Tidak ada perubahan. Repository sudah cocok dengan file dalam paket ini.' -ForegroundColor Green
        $pushCompleted = $true
    } elseif ($LASTEXITCODE -eq 1) {
        Write-Host ''
        Write-Host 'File yang berubah atau ditambahkan:' -ForegroundColor Cyan
        Invoke-GitChecked -GitArguments @('-C', $cloneDir, 'diff', '--cached', '--stat')
        Write-Host ''
        Write-Host 'File .env, *.sqlite3, dan database lokal TIDAK disalin ke GitHub.' -ForegroundColor Yellow
        $approve = Read-Host 'Ketik YA untuk commit dan push ke branch main (selain YA = batal)'
        if ($approve -cne 'YA') { throw 'Dibatalkan oleh pengguna. Tidak ada perubahan di GitHub.' }

        $authorName = (& git -C $cloneDir config user.name)
        if ([string]::IsNullOrWhiteSpace($authorName)) {
            $authorName = Read-Host 'Nama penulis commit Git (contoh: Rasidin Harahap)'
            if ([string]::IsNullOrWhiteSpace($authorName)) { throw 'Nama commit wajib diisi.' }
            Invoke-GitChecked -GitArguments @('-C', $cloneDir, 'config', 'user.name', $authorName)
        }
        $authorEmail = (& git -C $cloneDir config user.email)
        if ([string]::IsNullOrWhiteSpace($authorEmail)) {
            $authorEmail = Read-Host 'Email GitHub untuk commit (boleh alamat noreply dari pengaturan GitHub)'
            if ([string]::IsNullOrWhiteSpace($authorEmail)) { throw 'Email commit wajib diisi.' }
            Invoke-GitChecked -GitArguments @('-C', $cloneDir, 'config', 'user.email', $authorEmail)
        }
        Invoke-GitChecked -GitArguments @('-C', $cloneDir, 'commit', '-m', 'Update PinjamLab v5.0 - source, tests, and Docker CI')
        Write-Host 'Mengirim commit ke GitHub (tanpa --force)...' -ForegroundColor Cyan
        Invoke-GitChecked -GitArguments @('-C', $cloneDir, 'push', 'origin', ('HEAD:' + $branchName))
        $pushCompleted = $true
        $latestCommit = (& git -C $cloneDir rev-parse --short HEAD)
        Write-Host ('Upload berhasil. Commit: ' + $latestCommit) -ForegroundColor Green
    } else {
        throw ('Tidak dapat memeriksa perubahan (exit ' + $LASTEXITCODE + ').')
    }
    Write-Host ''
    Write-Host 'Periksa kode:    https://github.com/RasidinHarahap/coko-pinjamlab' -ForegroundColor Green
    Write-Host 'Periksa Actions: https://github.com/RasidinHarahap/coko-pinjamlab/actions' -ForegroundColor Green
    Write-Host 'GitHub Actions hanya menguji container; tidak mempublikasikan Flask ke internet.'
} catch {
    Write-Host ''
    Write-Host ('BELUM BERHASIL: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'Repository lama tidak di-force-push. Periksa koneksi, hak akses GitHub, dan file paket.'
    Write-Host ('Jika perlu, log/clone sementara ada di: ' + $cloneDir)
    exit 1
} finally {
    if ($pushCompleted -and (Test-Path -LiteralPath $cloneDir)) {
        Remove-Item -LiteralPath $cloneDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
