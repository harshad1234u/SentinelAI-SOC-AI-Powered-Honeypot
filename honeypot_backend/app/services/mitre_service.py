class MitreService:
    def __init__(self):
        # Dictionary-based lookup mapping normalized attack categories to MITRE ATT&CK technique IDs.
        self.mapping = {
            "brute_force": "T1110",
            "brute_force_success": "T1110",
            "malware_download": "T1105",
            "credential_access": "T1003",
            "command_execution": "T1059",
            "command_injection": "T1059",
            "reconnaissance": "T1595",
            "port_scan": "T1595",
            "proxy_abuse": "T1090"
        }

    def map_attack_type(self, attack_type: str) -> str | None:
        """Returns the MITRE ATT&CK technique ID for a given attack type, or None if not found."""
        return self.mapping.get(attack_type)

mitre_service = MitreService()
