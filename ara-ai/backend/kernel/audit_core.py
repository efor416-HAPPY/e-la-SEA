# -*- coding: utf-8 -*-
"""
📝 ARA AI Audit Core
Logs security audits, operational events, and system lifecycle trails.
"""

from backend.security.audit import audit_logger

class AuditCore:
    def __init__(self):
        self.logger = audit_logger

    def log(self, event_type: str, actor: str, target: str, message: str, status: str = "SUCCESS") -> None:
        """Appends a new security event to the audit log."""
        self.logger.log(event_type, actor, target, message, status)

    def read_recent_logs(self, limit=50) -> list[str]:
        """Reads recent audit logs."""
        return self.logger.read_recent_logs(limit)
