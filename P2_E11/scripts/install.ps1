$ErrorActionPreference = 'Stop'
$deliveryRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $deliveryRoot
$priorTmp = $env:TMP
$priorTemp = $env:TEMP
$installTmp = Join-Path $deliveryRoot '.tmp'
New-Item -ItemType Directory -Path $installTmp -Force | Out-Null
$env:TMP = $installTmp
$env:TEMP = $installTmp
try {
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        py -3.12 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno Python 3.12.' }
    }
    $deliveryPython = Join-Path $deliveryRoot '.venv/Scripts/python.exe'
    & $deliveryPython -m pip install --no-cache-dir --index-url https://pypi.org/simple -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Falló la descarga oficial de dependencias.' }
    & $deliveryPython -m pip install --no-cache-dir --no-index --no-build-isolation --no-deps -e '.[dev,plot,bim,viz]'
    if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación del proyecto.' }
    & $deliveryPython -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependencias inconsistentes.' }
} finally {
    $env:TMP = $priorTmp
    $env:TEMP = $priorTemp
    # Únicamente la carpeta temporal propia vacía, verificada dentro de la entrega.
    $resolvedTmp = [IO.Path]::GetFullPath($installTmp)
    if ($resolvedTmp -eq [IO.Path]::GetFullPath((Join-Path $deliveryRoot '.tmp'))) {
        try { [IO.Directory]::Delete($resolvedTmp, $false) } catch { }
    }
}
