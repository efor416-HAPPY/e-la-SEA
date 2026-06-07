# -*- coding: utf-8 -*-
"""
📝 ARA AI Security Subsystem: Audit Logging
Handles write-ahead security logs, validation errors, and GitOps audit trailing.
"""

import os
import time
import threading

class AuditLogger:
    """Thread-safe auditor for logging system security events and actions."""
    def __init__(self, log_path="downloads/security_audit.log"):
        self.log_path = log_path
        self.lock = threading.Lock()
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log(self, event_type: str, actor: str, target: str, message: str, status: str = "SUCCESS"):
        """Appends a new security event to the audit log."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{event_type}] [Status: {status}] [Actor: {actor}] [Target: {target}] - {message}\n"
        
        with self.lock:
            try:
                with open(self.log_path, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
            except Exception as e:
                print(f"❌ Failed to write audit log: {e}")

    def read_recent_logs(self, limit=50) -> list[str]:
        """Reads recent audit logs."""
        if not os.path.exists(self.log_path):
            return []
        
        with self.lock:
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                return [line.strip() for line in lines[-limit:]]
            except Exception as e:
                print(f"❌ Failed to read audit logs: {e}")
                return []

    def rotate_logs(self, max_size_bytes=1024 * 1024):
        """Truncates audit log if it exceeds max size to protect disk space."""
        if not os.path.exists(self.log_path):
            return
        
        with self.lock:
            try:
                size = os.path.getsize(self.log_path)
                if size > max_size_bytes:
                    backup_path = self.log_path + ".bak"
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(self.log_path, backup_path)
            except Exception as e:
                print(f"❌ Failed to rotate audit logs: {e}")

# Global auditor instance
audit_logger = AuditLogger()
