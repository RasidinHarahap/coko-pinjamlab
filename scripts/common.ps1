# Native commands may write normal progress to stderr in Windows PowerShell 5.1.
# Determine success from the exit code, while retaining and displaying both streams.
function Invoke-TaskNative {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$LogPath,
        [switch]$AllowFailure,
        [switch]$Quiet
    )
    if (-not (Get-Command $FilePath -ErrorAction SilentlyContinue)) {
        throw "Perintah $FilePath belum tersedia. Periksa instalasi/PATH, lalu buka ulang terminal."
    }
    if ($LogPath) {
        $taskParent = Split-Path $LogPath -Parent
        if ($taskParent) { New-Item -ItemType Directory -Force $taskParent | Out-Null }
        Set-Content -LiteralPath $LogPath -Value "" -Encoding UTF8
    }
    $taskOldPreference = $ErrorActionPreference
    $PSNativeCommandUseErrorActionPreference = $false
    try {
        $ErrorActionPreference = "Continue"
        $taskLines = @(& $FilePath @Arguments 2>&1 | ForEach-Object {
            $taskLine = $_.ToString().Replace([string][char]0, "")
            if ($LogPath) { Add-Content -LiteralPath $LogPath -Value $taskLine -Encoding UTF8 -ErrorAction Stop }
            if (-not $Quiet) { Write-Host $taskLine }
            $taskLine
        })
        $taskExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $taskOldPreference
    }
    if ($null -eq $taskExitCode) { throw "Tidak memperoleh exit code dari $FilePath." }
    $taskResult = [PSCustomObject]@{
        ExitCode = [int]$taskExitCode
        Lines = $taskLines
        LogPath = $LogPath
    }
    if ($taskExitCode -ne 0 -and -not $AllowFailure) {
        throw "Gagal (exit $taskExitCode): $FilePath $($Arguments -join ' '). Periksa log pada $LogPath."
    }
    return $taskResult
}
