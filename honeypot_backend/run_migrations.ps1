# Download proxy
Write-Host "Downloading Cloud SQL Auth Proxy..."
Invoke-WebRequest -Uri "https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.11.2/cloud-sql-proxy.x64.exe" -OutFile "cloud-sql-proxy.exe"

# Get Connection Name
$connName = $(gcloud sql instances describe honeypot-db --format="value(connectionName)")
Write-Host "Starting proxy for connection: $connName"

# Start proxy in background
$proxyProcess = Start-Process -FilePath ".\cloud-sql-proxy.exe" -ArgumentList "$connName" -PassThru -WindowStyle Hidden

# Give proxy time to initialize
Start-Sleep -Seconds 10

# Run migrations
Write-Host "Running Alembic migrations..."
$env:DATABASE_URL = "postgresql+asyncpg://soc:change-me-in-production@127.0.0.1:5432/honeypot_soc"
& .venv\Scripts\alembic.exe upgrade head

# Stop proxy
Write-Host "Stopping proxy..."
Stop-Process -Id $proxyProcess.Id
