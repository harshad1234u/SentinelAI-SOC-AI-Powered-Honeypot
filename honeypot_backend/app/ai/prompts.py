"""
Versioned LLM prompt templates for the Honeypot SOC pipeline.

Every template carries a ``PROMPT_VERSION`` so that changes to prompts
can be tracked alongside the analysis results they produced.  Two
families exist:

* **Realtime** – low-latency, single-event prompts (``realtime-v1``).
* **Investigation** – deep, multi-event analysis prompts (``investigation-v2``).
"""

from __future__ import annotations

# ── Version registry ─────────────────────────────────────────────────────────

PROMPT_VERSIONS: dict[str, str] = {
    "realtime": "realtime-v1",
    "investigation": "investigation-v2",
}


# ═══════════════════════════════════════════════════════════════════════════════
# REALTIME PROMPTS  (version: realtime-v1)
# ═══════════════════════════════════════════════════════════════════════════════

REALTIME_SYSTEM_PROMPT: str = (
    "You are a SOC analyst AI specialising in honeypot attack analysis. "
    "Analyse the attack data provided and respond ONLY in valid JSON – "
    "never include markdown fences, explanatory text, or any content "
    "outside the JSON object.\n\n"
    "Prompt version: realtime-v1"
)

REALTIME_ANALYSIS_TEMPLATE: str = """\
Analyse the following honeypot attack event and return a JSON object with \
exactly these keys: "summary", "severity", "attack_type", "recommendation".

Attack details:
- Source IP: {src_ip}
- Country: {country}
- Service: {service}
- Port: {port}
- Username attempted: {username}
- Password attempted: {password}
- Command executed: {command}
- Current severity: {severity}
- Threat score: {threat_score}
- AbuseIPDB confidence: {abuse_confidence}
- ISP: {isp}

Respond ONLY with valid JSON.
Prompt version: realtime-v1"""

ALERT_SUMMARY_TEMPLATE: str = """\
Generate a concise, one-paragraph Telegram alert summary for the \
following honeypot attack.  The summary must be suitable for a SOC \
team chat – include the key indicators (IP, country, service, \
severity) and a brief risk assessment.

Attack details:
- Source IP: {src_ip}
- Country: {country}
- Service: {service}
- Port: {port}
- Username: {username}
- Password: {password}
- Command: {command}
- Severity: {severity}
- Threat score: {threat_score}
- AbuseIPDB confidence: {abuse_confidence}
- ISP: {isp}

Prompt version: realtime-v1"""

SEVERITY_CLASSIFICATION_TEMPLATE: str = """\
Based on the attack data below, classify the severity as exactly one \
of: "low", "medium", "high", or "critical".  Respond with a single \
word – no JSON, no explanation.

Attack details:
- Source IP: {src_ip}
- Country: {country}
- Service: {service}
- Port: {port}
- Username: {username}
- Password: {password}
- Command: {command}
- Threat score: {threat_score}
- AbuseIPDB confidence: {abuse_confidence}
- ISP: {isp}

Prompt version: realtime-v1"""


# ═══════════════════════════════════════════════════════════════════════════════
# INVESTIGATION PROMPTS  (version: investigation-v2)
# ═══════════════════════════════════════════════════════════════════════════════

INVESTIGATION_SYSTEM_PROMPT: str = (
    "You are a senior threat analyst performing deep incident "
    "investigation on honeypot attack data.  You have access to "
    "correlated events and contextual intelligence retrieved via "
    "RAG.  Provide thorough, actionable analysis and respond ONLY "
    "in valid JSON.\n\n"
    "Prompt version: investigation-v2"
)

INCIDENT_INVESTIGATION_TEMPLATE: str = """\
Perform a comprehensive investigation of the following correlated \
attack events.  Use the provided RAG context for additional \
intelligence.

Return a JSON object with exactly these keys:
- "summary": string – executive summary of the incident
- "attack_chain": list[object] – ordered steps the attacker took, each object is {{ "step_number": int, "action": string, "mitre_id": string (optional), "description": string }}
- "severity": string – one of "low", "medium", "high", "critical"
- "threat_actor_profile": string – a brief profile of the likely threat actor
- "recommended_actions": list[string] – prioritised remediation steps
- "confidence": float – your confidence score between 0.0 and 1.0
- "mitre_techniques": list[string] – applicable MITRE ATT&CK technique IDs (e.g. "T1110.001")

--- ATTACK EVENTS ---
{attacks_json}

--- RAG CONTEXT ---
{rag_context}

Respond ONLY with valid JSON.
Prompt version: investigation-v2"""

ATTACK_CHAIN_TEMPLATE: str = """\
Reconstruct the attack chain from the following honeypot events.  \
Return a JSON object with:
- "chain": list of objects, each with "step", "timestamp", "action", "details"
- "initial_access": string – how the attacker gained initial access
- "objective": string – likely attacker objective
- "sophistication": string – one of "script_kiddie", "intermediate", "advanced", "apt"

--- EVENTS ---
{attacks_json}

Respond ONLY with valid JSON.
Prompt version: investigation-v2"""

ADVERSARY_PROFILE_TEMPLATE: str = """\
Profile the threat actor behind the following honeypot attacks.  \
Return a JSON object with:
- "actor_type": string – e.g. "botnet", "manual_attacker", "apt_group", "scanner"
- "sophistication": string – "low", "medium", "high", "expert"
- "likely_origin": string – best guess of origin region
- "motivation": string – e.g. "credential_harvesting", "cryptomining", "espionage", "ransomware"
- "tools_observed": list[string] – tools/malware families observed
- "ttps": list[string] – MITRE ATT&CK technique IDs
- "confidence": float – 0.0 to 1.0

--- ATTACKS ---
{attacks_json}

Respond ONLY with valid JSON.
Prompt version: investigation-v2"""

MALWARE_ANALYSIS_TEMPLATE: str = """\
Analyse the following commands/payloads captured from a honeypot and \
explain the malware behaviour.  Return a JSON object with:
- "malware_family": string – identified or suspected family name
- "behaviour": list[string] – step-by-step actions the payload performs
- "persistence_mechanisms": list[string] – how it maintains persistence
- "c2_indicators": list[string] – command-and-control indicators
- "iocs": list[string] – indicators of compromise (hashes, domains, IPs)
- "risk_level": string – "low", "medium", "high", "critical"
- "mitigation": list[string] – recommended mitigations

--- PAYLOADS ---
{attacks_json}

Respond ONLY with valid JSON.
Prompt version: investigation-v2"""
