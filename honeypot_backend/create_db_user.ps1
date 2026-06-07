Write-Host "Creating database honeypot_soc..."
gcloud sql databases create honeypot_soc --instance=honeypot-db

Write-Host "Creating user soc..."
gcloud sql users create soc --instance=honeypot-db --password="change-me-in-production"
