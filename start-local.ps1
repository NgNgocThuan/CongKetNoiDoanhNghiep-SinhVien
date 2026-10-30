$ErrorActionPreference = 'Stop'
$checkoutPath = $PSScriptRoot
$runtimePath = Join-Path $checkoutPath 'tmp/local-runtime'
New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
$repoGitPath = (& git -C $checkoutPath rev-parse --path-format=absolute --git-common-dir).Trim()
$sharedRepoPath = Split-Path $repoGitPath -Parent
$backendPath = Join-Path $checkoutPath 'backend'
$frontendPath = Join-Path $checkoutPath 'frontend'
$databasePath = (Join-Path $runtimePath 'student-connect.sqlite3').Replace('\','/')
$env:PYTHONPATH = $backendPath + ';' + (Join-Path $sharedRepoPath '.codex-deps')
$env:DATABASE_URL = 'sqlite:///' + $databasePath
$env:UPLOAD_DIR = Join-Path $runtimePath 'uploads'
$env:SMTP_HOST = ''
$env:AI_API_KEY = ''
$env:AI_MODEL = ''
$env:DEBUG = 'false'
$env:CORS_ORIGINS = '["http://127.0.0.1:5173","http://localhost:5173"]'
$env:FRONTEND_URL = 'http://127.0.0.1:5173'
$env:BACKEND_PROXY_TARGET = 'http://127.0.0.1:8000'
foreach ($localPort in @(8000,5173)) {
  if (Get-NetTCPConnection -LocalPort $localPort -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $localPort is already in use. Stop the existing instance before starting this demo."
  }
}
Push-Location $backendPath
try { & python -m scripts.local_demo_seed; if ($LASTEXITCODE -ne 0) { throw 'Database setup failed.' } }
finally { Pop-Location }
$apiProcess = Start-Process -FilePath (Get-Command python).Source -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $backendPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimePath 'backend.log') -RedirectStandardError (Join-Path $runtimePath 'backend-error.log') -PassThru
$viteScript = Join-Path $frontendPath 'node_modules/vite/bin/vite.js'
$webProcess = Start-Process -FilePath (Get-Command node).Source -ArgumentList @($viteScript,'--host','127.0.0.1','--port','5173','--strictPort') -WorkingDirectory $frontendPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimePath 'frontend.log') -RedirectStandardError (Join-Path $runtimePath 'frontend-error.log') -PassThru
@{ backend=$apiProcess.Id; frontend=$webProcess.Id; backend_started=$apiProcess.StartTime.ToUniversalTime().ToString('o'); frontend_started=$webProcess.StartTime.ToUniversalTime().ToString('o') } | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $runtimePath 'processes.json')
Write-Output 'Frontend: http://127.0.0.1:5173'
Write-Output 'Backend: http://127.0.0.1:8000/docs'
