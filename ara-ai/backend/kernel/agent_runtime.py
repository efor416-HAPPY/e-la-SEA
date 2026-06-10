# -*- coding: utf-8 -*-
"""
🔧 ARA AI Agent Runtime (ARA 3.0)
Multi-agent lifecycle manager. Handles agent registration, startup, shutdown,
health monitoring, and thread management.
"""

import time
import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from backend.agents.base_cognitive_agent import ICognitiveAgent
    from backend.kernel.cognitive_bus import CognitiveBus


class AgentRuntime:
    """
    멀티 에이전트 런타임.
    모든 인지 에이전트의 수명을 관리하고 건강 상태를 감시합니다.
    """

    def __init__(self, cognitive_bus: 'CognitiveBus'):
        self.bus = cognitive_bus
        self._agents: dict[str, 'ICognitiveAgent'] = {}
        self._health_status: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._monitor_interval = 30.0  # 30초마다 헬스체크

    # =========================================================================
    # Agent Lifecycle
    # =========================================================================

    def register(self, agent: 'ICognitiveAgent') -> None:
        """에이전트를 런타임에 등록합니다."""
        agent_id = agent.id()
        with self._lock:
            self._agents[agent_id] = agent
            self._health_status[agent_id] = {
                "status": "registered",
                "last_heartbeat": time.time(),
                "error_count": 0,
                "restart_count": 0,
            }
        # CognitiveBus에도 등록
        self.bus.register(agent)
        print(f"🔧 [AgentRuntime] 에이전트 등록: '{agent_id}'")

    def start_all(self) -> None:
        """모든 등록된 에이전트를 초기화하고 시작합니다."""
        with self._lock:
            agents = list(self._agents.items())

        for agent_id, agent in agents:
            try:
                agent.initialize()
                agent.start_tick_loop()
                with self._lock:
                    self._health_status[agent_id]["status"] = "running"
                print(f"✅ [AgentRuntime] 에이전트 시작: '{agent_id}'")
            except Exception as e:
                with self._lock:
                    self._health_status[agent_id]["status"] = "error"
                    self._health_status[agent_id]["error_count"] += 1
                print(f"❌ [AgentRuntime] 에이전트 시작 실패 '{agent_id}': {e}")

    def stop_all(self) -> None:
        """모든 에이전트를 안전하게 종료합니다."""
        self._running = False
        with self._lock:
            agents = list(self._agents.items())

        for agent_id, agent in agents:
            try:
                agent.stop_tick_loop()
                agent.shutdown()
                with self._lock:
                    self._health_status[agent_id]["status"] = "stopped"
            except Exception as e:
                print(f"❌ [AgentRuntime] 에이전트 종료 오류 '{agent_id}': {e}")

    def restart_agent(self, agent_id: str) -> bool:
        """특정 에이전트를 재시작합니다."""
        with self._lock:
            agent = self._agents.get(agent_id)
            if not agent:
                return False
            health = self._health_status.get(agent_id, {})

        try:
            agent.stop_tick_loop()
            agent.shutdown()
            agent.initialize()
            agent.start_tick_loop()

            with self._lock:
                health["status"] = "running"
                health["restart_count"] = health.get("restart_count", 0) + 1
                health["last_heartbeat"] = time.time()

            print(f"🔄 [AgentRuntime] 에이전트 재시작 완료: '{agent_id}'")
            return True
        except Exception as e:
            with self._lock:
                health["status"] = "error"
                health["error_count"] = health.get("error_count", 0) + 1
            print(f"❌ [AgentRuntime] 에이전트 재시작 실패 '{agent_id}': {e}")
            return False

    # =========================================================================
    # Health Monitoring
    # =========================================================================

    def start_monitoring(self) -> None:
        """백그라운드 헬스체크 루프를 시작합니다."""
        if self._running:
            return
        self._running = True

        def _monitor_loop():
            while self._running:
                self._check_health()
                time.sleep(self._monitor_interval)

        self._monitor_thread = threading.Thread(
            target=_monitor_loop,
            name="AgentRuntime-Monitor",
            daemon=True
        )
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

    def _check_health(self) -> None:
        """모든 에이전트의 건강 상태를 확인합니다."""
        with self._lock:
            agents = list(self._agents.items())

        for agent_id, agent in agents:
            try:
                state = agent.get_state()
                with self._lock:
                    self._health_status[agent_id]["last_heartbeat"] = time.time()
                    if state.get("running", False):
                        self._health_status[agent_id]["status"] = "running"
            except Exception as e:
                with self._lock:
                    self._health_status[agent_id]["status"] = "unhealthy"
                    self._health_status[agent_id]["error_count"] += 1

    def get_health_report(self) -> dict:
        """전체 런타임 건강 보고서를 반환합니다."""
        with self._lock:
            return {
                "total_agents": len(self._agents),
                "agents": {aid: status.copy() for aid, status in self._health_status.items()},
                "healthy": sum(1 for s in self._health_status.values() if s["status"] == "running"),
                "unhealthy": sum(1 for s in self._health_status.values() if s["status"] in ("error", "unhealthy")),
            }

    def __repr__(self) -> str:
        return f"AgentRuntime(agents={len(self._agents)}, running={self._running})"
