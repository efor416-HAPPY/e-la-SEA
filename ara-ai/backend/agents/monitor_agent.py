# -*- coding: utf-8 -*-
"""
🖥️ ARA AI Agent Layer: Monitor Agent & Telemetry Daemon
Monitors CPU/RAM load, manages periodic scheduler threads, and triggers auto-recovery routines.
"""

import os
import time
import threading
import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor
from backend.agents.news_agent import news_agent
from backend.agents.youtube_agent import youtube_agent

class MonitorAgent:
    """Manages background threads, system metrics telemetry, and auto-recovery daemon."""
    def __init__(self):
        self.running = False
        self.lock = threading.Lock()
        self.logs = []
        self.thread_states = {}  # name -> bool (active)
        self.executor = None
        self.system_metrics = {"cpu_usage": 0.0, "ram_usage": 50.0}

    def log_status(self, msg: str):
        with self.lock:
            timestamp = time.strftime('%H:%M:%S')
            self.logs.append(f"[{timestamp}] {msg}")
            if len(self.logs) > 15:
                self.logs.pop(0)

    def get_system_metrics(self) -> dict:
        """Gathers basic system metrics, executing helper scripts or fallback commands."""
        metrics = {"cpu_usage": 10.0, "ram_usage": 45.0, "platform": platform.system()}
        
        # Windows CPU load extraction fallback
        if platform.system() == "Windows":
            try:
                cmd = 'powershell -Command "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    metrics["cpu_usage"] = float(result.stdout.strip())
            except Exception:
                pass
        return metrics

    def start(self):
        """Launches the background schedulers and the recovery watchdog."""
        self.running = True
        self.log_status("ARA 모니터링 및 자동 복구 에이전트 시작...")
        
        # Core background tasks
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="AraMonitor")
        
        # Submit tasks
        self.executor.submit(self._run_news_loop)
        self.executor.submit(self._run_youtube_loop)
        self.executor.submit(self._run_recovery_watchdog)

    def _run_news_loop(self):
        self.thread_states["news_ingestion"] = True
        self.log_status("NewsAgent periodic loop started.")
        while self.running:
            try:
                news_agent.run_news_ingestion()
            except Exception as e:
                self.log_status(f"❌ NewsAgent loop crashed: {e}")
                self.thread_states["news_ingestion"] = False
                break  # Trigger watchdog recovery
            time.sleep(60.0)  # Scan every minute in sandbox (10m in production)

    def _run_youtube_loop(self):
        self.thread_states["youtube_ingestion"] = True
        self.log_status("YouTubeAgent periodic loop started.")
        while self.running:
            try:
                youtube_agent.run_video_ingestion()
            except Exception as e:
                self.log_status(f"❌ YouTubeAgent loop crashed: {e}")
                self.thread_states["youtube_ingestion"] = False
                break  # Trigger watchdog recovery
            time.sleep(60.0)

    def _run_recovery_watchdog(self):
        """Watchdog checks if threads are alive, automatically recreating them if dead."""
        self.thread_states["watchdog"] = True
        while self.running:
            time.sleep(15.0)  # Check health every 15 seconds
            
            # Check News Loop
            if not self.thread_states.get("news_ingestion", False):
                self.log_status("🚨 NewsAgent loop failure detected! Recovering...")
                self.executor.submit(self._run_news_loop)
                
            # Check YouTube Loop
            if not self.thread_states.get("youtube_ingestion", False):
                self.log_status("🚨 YouTubeAgent loop failure detected! Recovering...")
                self.executor.submit(self._run_youtube_loop)

    def stop(self):
        self.running = False
        if self.executor:
            self.executor.shutdown(wait=False)
        self.log_status("ARA 모니터링 데몬 정지 완료.")

# Global Monitor Agent
monitor_agent = MonitorAgent()
