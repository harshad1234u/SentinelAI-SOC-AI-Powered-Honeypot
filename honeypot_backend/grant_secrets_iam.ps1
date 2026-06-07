$sa = "755420559974-compute@developer.gserviceaccount.com"
$secrets = @("nim-api-key", "jwt-secret", "telegram-bot-token", "abuseipdb-api-key", "admin-password", "database-url")

foreach ($secret in $secrets) {
    Write-Host "Granting access to $secret..."
    gcloud secrets add-iam-policy-binding $secret `
        --member="serviceAccount:$sa" `
        --role="roles/secretmanager.secretAccessor" *>$null
}
Write-Host "IAM permissions granted."
