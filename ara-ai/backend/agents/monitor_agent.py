# -*- coding: utf-8 -*-
"""
🖥️ ARA AI Agent Layer: Monitor Agent
Coordinates CPU/RAM load calculations and telemetry dispatches via the AgentBus.
"""

import subprocess
import platform
from backend.agents.base_agent import IAgent
from backend.kernel.message import Message


class MonitorAgent(IAgent):
    def id(self) -> str:
        return "monitor"

    def initialize(self) -> bool:
        return True

    def process(self, message: Message) -> bool:
        """Processes monitoring and telemetry queries received via the AgentBus."""
        if message.action == "metrics":
            metrics = self.get_system_metrics()
            if isinstance(message.payload, dict):
                message.payload["result"] = metrics
            return True
        return False

    def shutdown(self) -> None:
        pass

    # Compatibility wrappers for legacy start/stop calls
    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def get_system_metrics(self) -> dict:
        """Gathers basic system metrics, executing helper commands or using fallbacks."""
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


# Global Monitor Agent Instance
monitor_agent = MonitorAgent()
