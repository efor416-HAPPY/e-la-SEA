# -*- coding: utf-8 -*-
"""
🛡️ ARA AI Security Core
Unifies IP whitelisting, rate limiting (DDoS protection), and safety gate checks.
"""

from backend.security.firewall import check_ip_whitelist, global_limiter
from backend.security.safety_gate import SafetyGate

class SecurityCore:
    def __init__(self):
        self.safety_gate = SafetyGate()
        self.limiter = global_limiter

    def is_ip_allowed(self, ip: str) -> bool:
        """Validates if IP is whitelisted/trusted."""
        return check_ip_whitelist(ip)

    def is_rate_allowed(self, ip: str) -> bool:
        """Checks rate limit allowance for the given IP."""
        return self.limiter.is_allowed(ip)

    def check_safety(self, text: str) -> tuple[bool, str]:
        """Scans input text for PII leaks, command injection, or SQL hazards."""
        return self.safety_gate.check_text_safety(text)
