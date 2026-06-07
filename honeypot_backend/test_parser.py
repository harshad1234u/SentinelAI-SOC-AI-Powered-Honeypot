import json
from app.services.log_parser import parse_log

sample_opencanary = {
  "stream": {
    "detected_level": "unknown",
    "filename": "/var/log/opencanary.log",
    "geoip_city_name": "Amsterdam",
    "geoip_continent_code": "EU",
    "geoip_continent_name": "Europe",
    "geoip_country_name": "The Netherlands",
    "geoip_location_latitude": "52.3716",
    "geoip_location_longitude": "4.8883",
    "job": "opencanary"
  },
  "values": [
    ["1780769108726454016", '{"dst_host":"honeypot","dst_port":22,"local_time":"2026-06-05 20:45:08.726454","logdata":{"PASSWORD":"password123","USERNAME":"root"},"logtype":4002,"node_id":"opencanary-1","src_host":"192.168.1.100","src_port":54321}']
  ]
}

print("Testing OpenCanary Parser")
# Loki service returns log_dict which is json.loads(log_line) + stream labels
# Let's mock what LokiService does:
log_line = sample_opencanary["values"][0][1]
log_dict = json.loads(log_line)
log_dict["_loki_timestamp"] = sample_opencanary["values"][0][0]
log_dict["_loki_labels"] = sample_opencanary["stream"]

result = parse_log(log_dict, "opencanary")
print(json.dumps(result, indent=2))
