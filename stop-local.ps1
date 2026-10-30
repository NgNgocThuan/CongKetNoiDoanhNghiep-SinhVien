$ErrorActionPreference = 'Stop'
$metadataPath = Join-Path $PSScriptRoot 'tmp/local-runtime/processes.json'
if (!(Test-Path -LiteralPath $metadataPath)) { Write-Output 'No local demo process metadata.'; exit 0 }
$metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
foreach ($serviceName in @('backend','frontend')) {
  $serviceProcess = Get-Process -Id $metadata.$serviceName -ErrorAction SilentlyContinue
  $expectedStart = $metadata.($serviceName + '_started')
  if ($serviceProcess -and $expectedStart -and $serviceProcess.StartTime.ToUniversalTime().ToString('o') -eq $expectedStart) {
    Stop-Process -Id $serviceProcess.Id
    Write-Output "Stopped $serviceName."
  }
}
