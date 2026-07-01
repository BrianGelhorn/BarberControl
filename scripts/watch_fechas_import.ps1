$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Fechas = Join-Path $Root "Fechas"
$Importer = Join-Path $PSScriptRoot "import_fechas.py"

if (-not (Test-Path $Fechas)) {
  Write-Host "No existe la carpeta Fechas."
  exit 1
}

$Python = (Get-Command py -ErrorAction SilentlyContinue)
if ($Python) {
  $PythonArgs = @("-3", $Importer)
} else {
  $Python = Get-Command python -ErrorAction SilentlyContinue
  if (-not $Python) {
    Write-Host "No encuentro Python en PATH."
    exit 1
  }
  $PythonArgs = @($Importer)
}

function Get-Fingerprint {
  $files = Get-ChildItem $Fechas -Recurse -File -Filter "*.xlsx" |
    Where-Object { -not $_.Name.StartsWith("~$") } |
    Sort-Object FullName

  return ($files | ForEach-Object { "$($_.FullName)|$($_.LastWriteTimeUtc.Ticks)|$($_.Length)" }) -join "`n"
}

function Run-Import {
  Write-Host ""
  Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Importando Fechas..."
  & $Python.Source @PythonArgs
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Import fallido. Reintento en el proximo cambio."
  }
}

Write-Host "Vigilando $Fechas"
Write-Host "Presiona Ctrl+C para salir."

$last = Get-Fingerprint
Run-Import

while ($true) {
  Start-Sleep -Seconds 3
  $current = Get-Fingerprint
  if ($current -ne $last) {
    Start-Sleep -Seconds 2
    $current = Get-Fingerprint
    if ($current -ne $last) {
      $last = $current
      Run-Import
    }
  }
}
