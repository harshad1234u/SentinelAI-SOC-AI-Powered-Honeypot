from typing import Any
from app.models.attack import Attack

class AlertAction:
    def __init__(self, rule_name: str, alert_type: str, severity: str):
        self.rule_name = rule_name
        self.alert_type = alert_type
        self.severity = severity

class RuleEngine:
    def evaluate(self, attack: Attack, context: dict[str, Any] = None) -> list[AlertAction]:
        actions = []
        
        # CriticalSeverityRule
        if attack.severity == "critical":
            actions.append(AlertAction("CriticalSeverityRule", "critical_attack", "critical"))
            
        # MalwareDownloadRule
        if attack.attack_type == "malware_download":
            actions.append(AlertAction("MalwareDownloadRule", "malware", "critical"))
            
        # HighReputationRule
        if (attack.abuse_confidence and attack.abuse_confidence >= 90) or attack.reputation == "critical":
            actions.append(AlertAction("HighReputationRule", "known_attacker", "high"))
            
        # SuspiciousCommandRule
        if attack.command and any(cmd in attack.command for cmd in ["wget", "curl", "chmod", "/etc/passwd", "rm -rf", "nc -e"]):
            actions.append(AlertAction("SuspiciousCommandRule", "suspicious_command", "high"))
            
        # Basic brute force rule (relies on burst context if available, else just logs success)
        if attack.attack_type == "brute_force_success":
            actions.append(AlertAction("BruteForceSuccessRule", "compromise", "high"))
            
        # If no specific critical/high rules fired but attack is medium
        if not actions and attack.severity == "medium":
            actions.append(AlertAction("MediumSeverityRule", "notice", "medium"))
            
        return actions

rule_engine = RuleEngine()
