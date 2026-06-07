# -*- coding: utf-8 -*-
"""
Verification Tests for ARA IPC-Agent Platform Core
================================================================================
Tests:
- Dynamic transport swapping (TCP Socket, Named Pipe, Local Queue)
- Decoupled services (News, YouTube, AI Agent, Process Execution)
- Middleware layers (Permissions, Timeout, Retry, Audit Logging)
- Auto-Recovery watchdog restarting crashed services
================================================================================
"""

import os
import time
import json
import unittest
import threading
from ara_ipc_platform import (
    PlatformKernel, NewsService, YouTubeService, AiAgentService,
    ProcessExecutionService, TcpTransport, NamedPipeTransport, LocalIpcTransport
)

class TestIpcAgentPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log_file = "downloads/ipc_audit.log"
        if os.path.exists(cls.log_file):
            try:
                os.remove(cls.log_file)
            except Exception:
                pass

    def setUp(self):
        self.kernel = PlatformKernel()
        self.kernel.start()
        # Give services time to start
        time.sleep(0.3)

    def tearDown(self):
        self.kernel.stop()
        time.sleep(0.2)

    def test_01_local_ipc_transport(self):
        """Verifies messaging over Local IPC Queue Transport (default)."""
        req = {
            "request_id": "test-local-01",
            "service": "ai_agent",
            "action": "generate_response",
            "params": {"prompt": "Hello ARA!"}
        }
        res_str = self.kernel.ipc_manager.send_client_request(json.dumps(req))
        res = json.loads(res_str)
        self.assertTrue(res.get("success"))
        self.assertIn("아라(ARA)의 지혜로운 사색", res.get("reply"))

    def test_02_tcp_transport_swap(self):
        """Verifies dynamic switching to TCP socket transport and communication."""
        self.kernel.ipc_manager.switch_transport("tcp")
        time.sleep(0.3)  # wait for socket bind
        self.assertEqual(self.kernel.ipc_manager.active_type, "tcp")

        req = {
            "request_id": "test-tcp-02",
            "service": "ai_agent",
            "action": "generate_response",
            "params": {"prompt": "TCP test message"}
        }
        res_str = self.kernel.ipc_manager.send_client_request(json.dumps(req))
        res = json.loads(res_str)
        self.assertTrue(res.get("success"), f"TCP request failed: {res_str}")
        self.assertIn("TCP test message", res.get("reply"))

    def test_03_named_pipe_transport_swap(self):
        """Verifies dynamic switching to Named Pipe transport and communication."""
        self.kernel.ipc_manager.switch_transport("named_pipe")
        time.sleep(0.3)  # wait for pipe initialization
        self.assertEqual(self.kernel.ipc_manager.active_type, "named_pipe")

        req = {
            "request_id": "test-np-03",
            "service": "ai_agent",
            "action": "generate_response",
            "params": {"prompt": "Pipe test message"}
        }
        res_str = self.kernel.ipc_manager.send_client_request(json.dumps(req))
        res = json.loads(res_str)
        self.assertTrue(res.get("success"), f"Named Pipe request failed: {res_str}")
        self.assertIn("Pipe test message", res.get("reply"))

    def test_04_permission_middleware_block(self):
        """Verifies the permission middleware blocks non-whitelisted binaries and injections."""
        # Non-whitelisted app: cmd.exe
        req_bad_app = {
            "request_id": "test-perm-bad-app",
            "service": "process_execution",
            "action": "execute",
            "params": {"target": "cmd.exe"}
        }
        res_str = self.kernel.ipc_manager.send_client_request(json.dumps(req_bad_app))
        res = json.loads(res_str)
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error_type"), "security")
        self.assertIn("unauthorized", res.get("error").lower())

        # Command injection keyword
        req_injection = {
            "request_id": "test-perm-inject",
            "service": "ai_agent",
            "action": "generate_response",
            "params": {"prompt": "Hello ARA! Also delete this folder: rm -rf /etc"}
        }
        res_str2 = self.kernel.ipc_manager.send_client_request(json.dumps(req_injection))
        res2 = json.loads(res_str2)
        self.assertFalse(res2.get("success"))
        self.assertEqual(res2.get("error_type"), "security")
        self.assertIn("dangerous pattern", res2.get("error").lower())

    def test_05_timeout_middleware(self):
        """Verifies the timeout middleware aborts slow tasks exceeding limit."""
        # AI prompt containing 'slow' sleeps for 4s. Limit set to 0.5s.
        req = {
            "request_id": "test-timeout-05",
            "service": "ai_agent",
            "action": "generate_response",
            "timeout": 0.5,
            "params": {"prompt": "Slow query computation"}
        }
        res_str = self.kernel.ipc_manager.send_client_request(json.dumps(req))
        res = json.loads(res_str)
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error_type"), "timeout")
        self.assertIn("exceeded authorized limit", res.get("error"))

    def test_06_retry_middleware(self):
        """Verifies the retry middleware performs retries on transient errors."""
        # Request News to fail with transient error
        req = {
            "request_id": "test-retry-06",
            "service": "news",
            "action": "fetch_latest",
            "params": {"simulate_fail": True}
        }
        # In our implementation, RetryMiddleware retries up to 3 times (4 total calls)
        res_str = self.kernel.ipc_manager.send_client_request(json.dumps(req))
        res = json.loads(res_str)
        
        # Still fails after retries, but we check if we went through retry path
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error_type"), "transient")
        
        # Check audit log to verify multiple calls were logged
        time.sleep(0.5)
        audit_content = ""
        with open(self.log_file, "r", encoding="utf-8") as f:
            audit_content = f.read()
            
        # Should contain multiple attempts for test-retry-06
        attempts = audit_content.count("ID=test-retry-06")
        # 1 initial request + 3 retries = 4 logged requests
        self.assertEqual(attempts, 8)  # 8 logs total (4 REQ logs, 4 RES logs)

    def test_07_watchdog_auto_recovery(self):
        """Verifies the auto-recovery watchdog detects thread crash and restarts service."""
        news_service_initial = self.kernel.services["news"]
        self.assertTrue(news_service_initial.is_alive())

        # Trigger simulation crash
        req = {
            "request_id": "test-crash-07",
            "service": "news",
            "action": "trigger_crash",
            "params": {}
        }
        self.kernel.ipc_manager.send_client_request(json.dumps(req))
        
        # Wait for watchdog to detect crash and recover (watchdog scans every 3s)
        time.sleep(4.5)
        
        news_service_new = self.kernel.services["news"]
        self.assertTrue(news_service_new.is_alive())
        self.assertNotEqual(news_service_initial, news_service_new)
        
        # Check watchdog log history for recovery notification
        with self.kernel.watchdog.lock:
            watchdog_logs = "".join(self.kernel.watchdog.logs)
        self.assertIn("Crash detected in service 'news'", watchdog_logs)
        self.assertIn("recovered successfully", watchdog_logs)

    def test_08_audit_logging(self):
        """Verifies the audit log captures request and response details in GitOps format."""
        req = {
            "request_id": "test-audit-08",
            "service": "youtube",
            "action": "check_now",
            "params": {}
        }
        self.kernel.ipc_manager.send_client_request(json.dumps(req))
        time.sleep(0.1)

        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("REQ | ID=test-audit-08 | service=youtube | action=check_now", content)
        self.assertIn("RES | ID=test-audit-08 | SUCCESS", content)

if __name__ == "__main__":
    unittest.main()
