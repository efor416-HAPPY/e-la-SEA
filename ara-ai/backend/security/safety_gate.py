# -*- coding: utf-8 -*-
"""
🔒 ARA AI Security Subsystem: Ingestion Safety Gate
Validates input strings for PII leakage, SQL Injection, and command execution hazards.
"""

import re

class SafetyGate:
    """Filters malicious input strings and safeguards privacy (PII)."""
    def __init__(self):
        self.self_adaptation_weight = 1.0

        # Patterns for PII validation
        self.ssn_pattern = re.compile(r'\d{6}-\d{7}')
        self.phone_pattern = re.compile(r'01[0-9]-\d{3,4}-\d{4}')
        
        # Macro-economic critical indicator patterns
        self.economic_pattern = re.compile(r'.*(주식시장|경제|인플레이션|금리|긴축재정|정치).*')

        # Dangerous command keywords (system hazard prevention)
        self.forbidden_keywords = [
            "sudo ", "rm -rf", "drop table", "delete from", "format c:", 
            "mkfs", "chmod ", "chown ", "shutdown"
        ]

    def check_text_safety(self, text: str) -> tuple[bool, str]:
        """
        Scans text for security vulnerability or PII.
        Returns (is_safe, message)
        """
        if not text:
            return True, "Empty text"

        # 1. PII check
        if self.ssn_pattern.search(text):
            return False, "개인정보(주민등록번호) 패턴 감격 차단"
        if self.phone_pattern.search(text):
            return False, "개인정보(전화번호) 패턴 감격 차단"

        # 2. Command Injection & SQL Injection Keywords check
        text_lower = text.lower()
        for keyword in self.forbidden_keywords:
            if keyword in text_lower:
                return False, f"위험 명령어/SQL 키워드 감지 차단: '{keyword}'"

        # 3. Macro-economic indicator monitoring
        if self.economic_pattern.search(text):
            # Log notice internally
            pass

        # 4. Self-Feedback weight adjustment based on request complexity
        confidence = 0.5
        if len(text) > 20:
            confidence += 0.3
        if self.economic_pattern.search(text):
            confidence += 0.2

        if confidence < 0.6:
            self.self_adaptation_weight += 0.05
            
        return True, "안전 검증 통과"
