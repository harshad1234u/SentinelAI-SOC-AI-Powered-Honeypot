import subprocess
import json

cors_origins = '["https://soc-frontend-755420559974.us-central1.run.app", "http://localhost:3000"]'
escaped_json = cors_origins.replace('"', '\\"')

cmd = f'gcloud run services update soc-backend --region us-central1 --update-env-vars "^@^CORS_ORIGINS={escaped_json}"'

print("Running command:", cmd)
result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
