from typing import Any
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger(__name__)

def calculate_severity(attack_type: str, command: str = None) -> str:
    if attack_type == "malware_download" or (command and any(cmd in command for cmd in ["rm -rf", "wget", "curl", "chmod 777"])):
        return "critical"
    if attack_type == "proxy_abuse" or (command and any(cmd in command for cmd in ["/etc/passwd", "/etc/shadow"])):
        return "high"
    if attack_type == "brute_force_success" or attack_type == "command_injection" or attack_type == "reconnaissance":
        return "high"
    if attack_type == "brute_force" or attack_type == "port_scan":
        return "medium"
    return "low"

def parse_cowrie_log(log: dict[str, Any]) -> dict[str, Any] | None:
    try:
        eventid = log.get("eventid", "")
        if not eventid:
            return None

        attack_type = "unknown"
        severity = "low"
        
        if eventid == "cowrie.login.failed":
            attack_type = "brute_force"
        elif eventid == "cowrie.login.success":
            attack_type = "brute_force_success"
        elif eventid == "cowrie.command.input":
            command = log.get("input", "")
            if "wget" in command or "curl" in command:
                attack_type = "malware_download"
            else:
                attack_type = "command_execution"
        elif eventid in ["cowrie.session.file_download", "cowrie.session.file_upload"]:
            attack_type = "malware_download"
        elif eventid == "cowrie.direct-tcpip.request":
            attack_type = "proxy_abuse"

        dst_port = log.get("dst_port")
        service = "ssh" if dst_port == 22 else "telnet" if dst_port == 23 else "unknown"

        command = log.get("input", "")

        return {
            "src_ip": log.get("src_ip"),
            "dst_port": dst_port,
            "service": service,
            "username": log.get("username"),
            "password": log.get("password"),
            "command": command,
            "session_id": log.get("session"),
            "attack_type": attack_type,
            "severity": calculate_severity(attack_type, command),
            "honeypot_type": "cowrie",
            "raw_log": log,
            "timestamp": log.get("timestamp")
        }
    except Exception as e:
        logger.warning("Failed to parse cowrie log", error=str(e), log=log)
        return None

def parse_opencanary_log(log: dict[str, Any]) -> dict[str, Any] | None:
    try:
        logtype = str(log.get("logtype", ""))
        if not logtype:
            return None

        attack_type = "unknown"
        service = "unknown"
        
        if logtype == "4001":
            attack_type = "brute_force"
            service = "ssh"
        elif logtype == "2001":
            attack_type = "brute_force"
            service = "ftp"
        elif logtype == "3001":
            attack_type = "brute_force"
            service = "http"
        elif logtype == "5001":
            attack_type = "port_scan"
        elif logtype == "6001":
            attack_type = "brute_force"
            service = "telnet"
        elif logtype in ["8001", "9001", "9002"]:
            attack_type = "brute_force"
            service = "db"

        logdata = log.get("logdata", {})
        username = logdata.get("USER")
        password = logdata.get("PASSWORD")

        return {
            "src_ip": log.get("src_host"),
            "dst_port": log.get("dst_port"),
            "service": service,
            "username": username,
            "password": password,
            "command": None,
            "session_id": None,
            "attack_type": attack_type,
            "severity": calculate_severity(attack_type, None),
            "honeypot_type": "opencanary",
            "raw_log": log,
            "timestamp": log.get("local_time")
        }
    except Exception as e:
        logger.warning("Failed to parse opencanary log", error=str(e), log=log)
        return None

def parse_log(log: dict[str, Any], job: str) -> dict[str, Any] | None:
    if job == "cowrie":
        return parse_cowrie_log(log)
    elif job == "opencanary":
        return parse_opencanary_log(log)
    return None
