# -*- coding: utf-8 -*-
"""
🏥 ARA AI Health Monitor
Monitors registered IAgent states and triggers automatic self-healing recovery if background loops crash.
"""

import time
import threading
from typing import Dict
from backend.agents.base_agent import IAgent


class HealthMonitor(threading.Thread):
    def __init__(self, kernel):
        super().__init__()
        self.name = "AraHealthMonitorWatchdog"
        self.daemon = True
        self.kernel = kernel
        self.running = False
        self.agent_threads: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()

    def start_monitor(self) -> None:
        """Starts the watchdog recovery background thread."""
        self.running = True
        self.start()
        print("🏥 [HealthMonitor] Watchdog daemon started.")

    def stop_monitor(self) -> None:
        """Stops the watchdog recovery daemon."""
        self.running = False

    def check(self, agent: IAgent) -> bool:
        """Checks if a given agent's background loop thread is alive."""
        agent_id = agent.id()
        with self.lock:
            thread = self.agent_threads.get(agent_id)
            if thread and not thread.is_alive():
                return False
        return True

    def register_thread(self, agent_id: str, thread: threading.Thread) -> None:
        """Registers a thread handle associated with an agent's background loop."""
        with self.lock:
            self.agent_threads[agent_id] = thread

    def run(self) -> None:
        while self.running:
            time.sleep(5.0)  # Check health every 5 seconds for responsive sandbox demonstration
            
            # Retrieve currently registered agents on the bus
            agents = list(self.kernel.bus.agents.items())
            
            for agent_id, agent in agents:
                # We check the background collector agents news, youtube, and economy
                if agent_id in ["news", "youtube", "economy"]:
                    if not self.check(agent):
                        print(f"🚨 [HealthMonitor] Crash detected in agent '{agent_id}'! Re-initializing...")
                        self.kernel.audit_core.log(
                            "AGENT_CRASH", "HealthMonitor", agent_id, 
                            f"Agent '{agent_id}' background thread crashed. Restarting agent...", "WARNING"
                        )
                        
                        try:
                            # Re-instantiate based on agent ID
                            if agent_id == "news":
                                from backend.agents.news_agent import NewsAgent
                                new_agent = NewsAgent()
                            elif agent_id == "youtube":
                                from backend.agents.youtube_agent import YouTubeAgent
                                new_agent = YouTubeAgent()
                            elif agent_id == "economy":
                                from backend.agents.economy_agent import EconomyAgent
                                new_agent = EconomyAgent()
                            else:
                                continue
                            
                            # Register and initialize the new instance
                            self.kernel.register_agent(new_agent)
                            new_agent.initialize()
                            
                            # Start its background loop in a new thread
                            thread = threading.Thread(target=new_agent.start_loop, name=f"{agent_id}_loop", daemon=True)
                            self.register_thread(agent_id, thread)
                            thread.start()
                            
                            self.kernel.audit_core.log(
                                "AGENT_RECOVERY", "HealthMonitor", agent_id, 
                                f"Agent '{agent_id}' recovered and restarted successfully.", "SUCCESS"
                            )
                            print(f"✅ [HealthMonitor] Recovered agent '{agent_id}' successfully.")
                        except Exception as e:
                            print(f"❌ [HealthMonitor] Recovery failed for agent '{agent_id}': {e}")
