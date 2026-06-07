import sys
import os

with open("logs2.txt", "r", encoding="utf-16le", errors="replace") as f:
    content = f.read()

lines = content.split('\n')
app_logs = [line for line in lines if "Loki" in line or "Ingest" in line or "backend" in line]

for log in app_logs[-50:]:
    if "httpRequest" not in log and "insertId" not in log:
        print(log.strip())
