import re

class IOCService:
    def __init__(self):
        # Compiled regex patterns for common IOCs
        self.ipv4_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        self.domain_pattern = re.compile(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b')
        self.url_pattern = re.compile(r'\b(?:http|https|ftp)://[^\s/$.?#].[^\s]*\b')
        self.sha256_pattern = re.compile(r'\b[A-Fa-f0-9]{64}\b')
        self.md5_pattern = re.compile(r'\b[A-Fa-f0-9]{32}\b')

    def extract_iocs(self, text: str) -> dict[str, list[str]]:
        if not text:
            return {
                "ipv4": [],
                "domains": [],
                "urls": [],
                "sha256": [],
                "md5": []
            }
            
        iocs = {
            "ipv4": list(set(self.ipv4_pattern.findall(text))),
            "domains": list(set(self.domain_pattern.findall(text))),
            "urls": list(set(self.url_pattern.findall(text))),
            "sha256": list(set(self.sha256_pattern.findall(text))),
            "md5": list(set(self.md5_pattern.findall(text)))
        }
        
        # Remove empty lists to keep the result clean
        return {k: v for k, v in iocs.items() if v}

ioc_service = IOCService()
