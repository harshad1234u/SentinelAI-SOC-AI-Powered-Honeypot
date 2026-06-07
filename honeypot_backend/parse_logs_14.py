import json

with open('logs_14_ascii.json', encoding='ascii') as f:
    logs = json.load(f)

for log in logs:
    if "jsonPayload" in log and "message" in log["jsonPayload"]:
        print(log["jsonPayload"]["message"].strip())
    elif "textPayload" in log:
        print(log["textPayload"].strip())
