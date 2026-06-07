# -*- coding: utf-8 -*-
"""
🛡️ ARA AI Security Subsystem: Firewall Module
Provides IP whitelisting and rate limiting (DDoS protection) guards.
"""

import time
import threading

class RateLimiter:
    """Token Bucket rate limiter for preventing DDoS and brute force."""
    def __init__(self, limit=30, window=1.0):
        self.limit = limit
        self.window = window
        self.history = {}  # ip -> list of timestamps
        self.lock = threading.Lock()

    def is_allowed(self, ip: str) -> bool:
        with self.lock:
            now = time.time()
            if ip not in self.history:
                self.history[ip] = []
            
            # Remove timestamps older than window
            self.history[ip] = [t for t in self.history[ip] if now - t < self.window]
            
            if len(self.history[ip]) < self.limit:
                self.history[ip].append(now)
                return True
            return False

# Global Rate Limiter instance
global_limiter = RateLimiter(limit=30, window=1.0)

def check_ip_whitelist(ip: str, allowed_ips=None) -> bool:
    """
    Checks if client IP is within private ranges or whitelist.
    """
    # Allow localhost loopback
    if ip in ('127.0.0.1', '::1', 'localhost'):
        return True
    if ip.startswith('127.'):
        return True
    
    # Allow explicit custom allowed IPs
    if allowed_ips and ip in allowed_ips:
        return True

    # Allow private network IP ranges (RFC 1918)
    if ip.startswith('10.'):
        return True
    if ip.startswith('192.168.'):
        return True
    if ip.startswith('172.'):
        parts = ip.split('.')
        if len(parts) >= 2:
            try:
                second_octet = int(parts[1])
                if 16 <= second_octet <= 31:
                    return True
            except ValueError:
                pass
                
    return False
