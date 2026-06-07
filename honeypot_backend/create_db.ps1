Write-Host "Creating Cloud SQL Instance (this will take 5-10 minutes)..."
gcloud sql instances create honeypot-db --database-version=POSTGRES_16 --region=us-central1 --tier=db-custom-1-3840 --backup-start-time=02:00 --enable-bin-log --deletion-protection *>$null

Write-Host "Creating database honeypot_soc..."
gcloud sql databases create honeypot_soc --instance=honeypot-db *>$null

Write-Host "Creating user soc..."
gcloud sql users create soc --instance=honeypot-db --password="change-me-in-production" *>$null

Write-Host "Cloud SQL Setup Complete!"
