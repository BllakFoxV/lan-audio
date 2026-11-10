param([string]$AdbDirectory)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.build-venv/Scripts/python.exe')) {
        python -m venv .build-venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create build environment.' }
    }
    $buildPython = Join-Path $projectRoot '.build-venv/Scripts/python.exe'
    & $buildPython -m pip install -r build/requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw 'Build dependency installation failed.' }
    $compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    New-Item -ItemType Directory -Path '.build/capture' -Force | Out-Null
    $captureBinary = Join-Path $projectRoot '.build/capture/Loopback.exe'
    $captureSource = Join-Path $projectRoot 'app/Loopback.cs'
    & $compiler /nologo /optimize+ /platform:x64 "/out:$captureBinary" $captureSource
    if ($LASTEXITCODE -ne 0) { throw 'Audio capture compilation failed.' }
    & $buildPython -m unittest discover -s tests -t . -q
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
    $previousAdbDirectory = $env:LAN_AUDIO_ADB_DIR
    try {
        if ($AdbDirectory) { $env:LAN_AUDIO_ADB_DIR = $AdbDirectory }
        & $buildPython -m PyInstaller --noconfirm --workpath '.build/pyinstaller' --distpath dist 'build/LAN Audio.spec'
        if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
    } finally {
        $env:LAN_AUDIO_ADB_DIR = $previousAdbDirectory
    }
    $releaseName = 'LAN-Audio-v0.1-Windows-x64'
    Copy-Item -LiteralPath 'dist/LAN Audio.exe' -Destination "dist/$releaseName.exe" -Force
    Compress-Archive -LiteralPath 'dist/LAN Audio.exe' -DestinationPath "dist/$releaseName.zip" -Force
    $checksumLines = foreach ($releaseFile in @("$releaseName.exe", "$releaseName.zip")) {
        $checksum = (Get-FileHash -LiteralPath "dist/$releaseFile" -Algorithm SHA256).Hash.ToLowerInvariant()
        "$checksum  $releaseFile"
    }
    $checksumLines | Set-Content -LiteralPath 'dist/SHA256SUMS.txt' -Encoding ascii
    Get-Item -LiteralPath 'dist/LAN Audio.exe' | Select-Object FullName, Length
} finally {
    Pop-Location
}
