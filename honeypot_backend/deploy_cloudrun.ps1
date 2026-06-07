$ENV_VARS = "ENVIRONMENT=production," +
            "DEBUG=false," +
            "REDIS_ENABLED=false," +
            "LOKI_URL=http://34.93.77.93:3100," +
            "QDRANT_URL=http://34.93.77.93:6333," +
            "GEOIP_BUCKET_NAME=honeypot-soc-geoip-us-central1," +
            "NIM_BASE_URL=https://integrate.api.nvidia.com/v1," +
            "REALTIME_MODEL=deepseek-v4-flash," +
            "FALLBACK_REALTIME_MODEL=llama-3.1-nemotron-nano-8b-v1," +
            "INVESTIGATION_MODEL=qwen3-next-80b-a3b-instruct," +
            "EMBED_MODEL=nv-embedqa-e5-v5," +
            "CORS_ORIGINS=^[^https://soc-frontend-755420559974.us-central1.run.app^,http://localhost:3000^]^"
$SECRETS = "NIM_API_KEY=nim-api-key:latest," +
           "JWT_SECRET_KEY=jwt-secret:latest," +
           "TELEGRAM_BOT_TOKEN=telegram-bot-token:latest," +
           "TELEGRAM_CHAT_ID=telegram-chat-id:latest," +
           "ABUSEIPDB_API_KEY=abuseipdb-api-key:latest," +
           "ADMIN_PASSWORD=admin-password:latest," +
           "DATABASE_URL=database-url:latest"

Write-Host "Deploying to Cloud Run..."
gcloud run deploy soc-backend --source . --region=us-central1 --memory=2Gi --cpu=2 --concurrency=50 --timeout=300s --min-instances=0 --max-instances=5 --allow-unauthenticated --add-cloudsql-instances="testpot:us-central1:honeypot-db" --env-vars-file=env-vars.yaml --set-secrets=$SECRETS

