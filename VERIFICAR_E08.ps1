param([string]$Salida = '')

$ErrorActionPreference = 'Stop'
$carpetaE08 = Join-Path $PSScriptRoot 'P2_E08'
$candidatos = @(
    (Join-Path $PSScriptRoot '.venv-e08\Scripts\python.exe'),
    (Join-Path $carpetaE08 '.venv\Scripts\python.exe')
)
$pythonE08 = $candidatos | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $pythonE08) {
    throw 'No se encontro el entorno Python. Sigue la instalacion de P2_E08/README.md.'
}
$argumentosE08 = @('-X', 'utf8', '-B', 'scripts/verify_e08.py')
if ($Salida) {
    $destinoE08 = if ([System.IO.Path]::IsPathRooted($Salida)) { $Salida } else { Join-Path $PSScriptRoot $Salida }
} else {
    $fechaE08 = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ')
    $destinoE08 = Join-Path $carpetaE08 "results\auditoria_e08\$fechaE08"
}
$argumentosE08 += @('--output', $destinoE08)
Write-Host "E08: resultados en $destinoE08"
Push-Location -LiteralPath $carpetaE08
try {
    & $pythonE08 @argumentosE08
    $codigoE08 = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $codigoE08
