$ErrorActionPreference = 'Stop'
$volume = ('R','S','T','U','V','W','X','Y','Z' | Where-Object {
    -not (Get-PSDrive -Name $_ -ErrorAction SilentlyContinue)
} | Select-Object -First 1)
if (-not $volume) { throw 'No unused test drive letter.' }
$disk = Join-Path $env:RUNNER_TEMP 'relife-windows-test.vhd'
$script = Join-Path $env:RUNNER_TEMP 'relife-diskpart.txt'
if (Test-Path $disk) { throw 'The test VHD path already exists.' }
try {
    @(
        "create vdisk file=`"$disk`" maximum=128 type=expandable"
        "select vdisk file=`"$disk`""
        'attach vdisk'
        'create partition primary'
        'format fs=fat32 quick label=RELIFETEST'
        "assign letter=$volume"
    ) | Set-Content -Encoding ascii $script
    & diskpart.exe /s $script
    if ($LASTEXITCODE -ne 0) { throw 'Test VHD creation failed.' }
    if ((Get-Volume -DriveLetter $volume).FileSystemLabel -ne 'RELIFETEST') {
        throw 'The temporary test volume is unavailable.'
    }
    $env:RELIFE_TEST_VOLUME = "${volume}:"
    & go test -v ./...
    if ($LASTEXITCODE -ne 0) { throw 'Windows FAT32 tests failed.' }
} finally {
    if (Test-Path $disk) {
        @("select vdisk file=`"$disk`"", 'detach vdisk') | Set-Content -Encoding ascii $script
        & diskpart.exe /s $script
        if ($LASTEXITCODE -eq 0) { Remove-Item -LiteralPath $disk }
    }
    Remove-Item -LiteralPath $script -ErrorAction SilentlyContinue
}
