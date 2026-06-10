# -*- coding: utf-8 -*-
"""
🛡️ ARA AI Recovery Engine (ARA 3.0)
Self-healing engine that detects agent failures, restores from snapshots, and restarts.

Recovery flow:
    Agent Crash → Detect Failure → Load Snapshot → Restore State → Restart Agent
"""

import time
import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from backend.kernel.agent_runtime import AgentRuntime


class RecoveryEngine:
    """
    자가 치유 엔진.
    에이전트 크래시를 감지하고, 스냅샷에서 복원 후 재시작합니다.
    """

    def __init__(self, agent_runtime: 'AgentRuntime'):
        self.runtime = agent_runtime
        self._snapshots: dict[str, dict] = {}  # agent_id -> last known good state
        self._recovery_history: list[dict] = []
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._check_interval = 15.0  # 15초마다 체크
        self._max_auto_restarts = 3  # 자동 재시작 최대 횟수

    # =========================================================================
    # Snapshot Management
    # =========================================================================

    def take_snapshot(self, agent_id: str) -> None:
        """에이전트의 현재 상태를 스냅샷으로 저장합니다."""
        agent = self.runtime._agents.get(agent_id)
        if agent:
            try:
                state = agent.get_state()
                with self._lock:
                    self._snapshots[agent_id] = state
            except Exception as e:
                print(f"⚠️ [RecoveryEngine] 스냅샷 실패 '{agent_id}': {e}")

    def take_all_snapshots(self) -> None:
        """모든 에이전트의 스냅샷을 저장합니다."""
        for agent_id in list(self.runtime._agents.keys()):
            self.take_snapshot(agent_id)

    # =========================================================================
    # Failure Detection
    # =========================================================================

    def detect_failure(self, agent_id: str) -> bool:
        """에이전트의 장애 여부를 판단합니다."""
        health = self.runtime._health_status.get(agent_id, {})
        status = health.get("status", "unknown")

        if status in ("error", "unhealthy"):
            return True

        # Heartbeat 타임아웃 (60초 이상 무응답)
        last_beat = health.get("last_heartbeat", 0)
        if time.time() - last_beat > 60.0 and status == "running":
            return True

        return False

    # =========================================================================
    # Recovery
    # =========================================================================

    def recover(self, agent_id: str) -> bool:
        """에이전트를 스냅샷에서 복원하고 재시작합니다."""
        health = self.runtime._health_status.get(agent_id, {})
        restart_count = health.get("restart_count", 0)

        if restart_count >= self._max_auto_restarts:
            print(f"🚨 [RecoveryEngine] '{agent_id}' 최대 재시작 횟수 초과. 수동 복구 필요.")
            return False

        print(f"🔄 [RecoveryEngine] '{agent_id}' 복구 시작...")

        # 1. 스냅샷 복원
        with self._lock:
            snapshot = self._snapshots.get(agent_id)

        agent = self.runtime._agents.get(agent_id)
        if agent and snapshot:
            try:
                agent.restore_state(snapshot)
                print(f"📸 [RecoveryEngine] '{agent_id}' 스냅샷 복원 완료")
            except Exception as e:
                print(f"⚠️ [RecoveryEngine] '{agent_id}' 스냅샷 복원 실패: {e}")

        # 2. 재시작
        success = self.runtime.restart_agent(agent_id)

        # 3. 복구 이력 기록
        with self._lock:
            self._recovery_history.append({
                "agent_id": agent_id,
                "success": success,
                "had_snapshot": snapshot is not None,
                "timestamp": time.time(),
                "attempt": restart_count + 1,
            })

        if success:
            # 재시작 후 새 스냅샷
            self.take_snapshot(agent_id)

        return success

    # =========================================================================
    # Monitoring Loop
    # =========================================================================

    def start(self) -> None:
        """자가 치유 모니터링 루프를 시작합니다."""
        if self._running:
            return
        self._running = True

        def _loop():
            while self._running:
                try:
                    # 1. 전체 스냅샷 갱신
                    self.take_all_snapshots()

                    # 2. 장애 감지 및 자동 복구
                    for agent_id in list(self.runtime._agents.keys()):
                        if self.detect_failure(agent_id):
                            print(f"🚨 [RecoveryEngine] 장애 감지: '{agent_id}'")
                            self.recover(agent_id)

                except Exception as e:
                    print(f"❌ [RecoveryEngine] 모니터링 오류: {e}")

                time.sleep(self._check_interval)

        self._monitor_thread = threading.Thread(
            target=_loop,
            name="RecoveryEngine-Monitor",
            daemon=True
        )
        self._monitor_thread.start()
        print("🛡️ [RecoveryEngine] 자가 치유 모니터링 시작.")

    def stop(self) -> None:
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

    def get_recovery_history(self) -> list[dict]:
        with self._lock:
            return list(self._recovery_history)

    def __repr__(self) -> str:
        return f"RecoveryEngine(snapshots={len(self._snapshots)}, recoveries={len(self._recovery_history)})"
