# -*- coding: utf-8 -*-
"""
🧬 ARA AI Cognitive Agent Interface (ARA 3.0)
Extends the legacy IAgent with CognitiveBus integration:
  - Topic-based pub/sub subscriptions
  - Thought reception and emission
  - State snapshot/restore for self-healing
  - Lifecycle hooks (initialize, shutdown, periodic tick)
"""

import time
import threading
from typing import Optional
from backend.agents.base_agent import IAgent
from backend.kernel.message import Message, Thought


class ICognitiveAgent(IAgent):
    """
    인지 에이전트 인터페이스.
    CognitiveBus에 연결되어 Thought를 송수신하는 자율 에이전트.

    모든 인지 에이전트는 이 클래스를 상속하고 아래 메서드를 구현해야 합니다:
      - id()               : 고유 식별자
      - subscribed_topics() : 구독할 Thought 토픽 목록
      - on_thought()        : Thought 수신 시 처리 로직
      - initialize()        : 초기화
      - shutdown()           : 종료 정리
    """

    def __init__(self):
        self.kernel = None          # AraKernel reference (set by kernel on registration)
        self.bus = None             # CognitiveBus reference (set by bus on registration)
        self._running: bool = False
        self._tick_thread: Optional[threading.Thread] = None
        self._tick_interval: float = 0.0  # 0이면 주기적 tick 없음
        self._state: dict = {}      # 내부 상태 (self-healing 스냅샷용)
        self._thought_log: list = []  # 최근 처리한 Thought 로그
        self._max_log_size: int = 100

    # =========================================================================
    # Abstract Methods (서브클래스에서 반드시 구현)
    # =========================================================================

    def id(self) -> str:
        """에이전트 고유 식별자를 반환합니다."""
        raise NotImplementedError

    def subscribed_topics(self) -> list[str]:
        """
        구독할 Thought 토픽(thought_type) 목록을 반환합니다.
        CognitiveBus는 이 토픽의 Thought가 publish될 때 on_thought()를 호출합니다.
        
        예시: ["perception", "dialogue", "plan"]
        
        특수 토픽:
          - "*" : 모든 토픽 수신
          - "source.<agent_id>" : 특정 에이전트의 Thought만 수신
        """
        raise NotImplementedError

    def on_thought(self, thought: Thought) -> Optional[Thought]:
        """
        CognitiveBus로부터 Thought를 수신했을 때 호출됩니다.
        
        반환값:
          - Thought: 파생 Thought를 반환하면 CognitiveBus가 자동으로 publish합니다.
          - None: 반응 없음 (기억 저장 등 사이드이펙트만 수행)
        """
        raise NotImplementedError

    def initialize(self) -> bool:
        """에이전트 초기화. 리소스 할당, 모델 로드 등."""
        raise NotImplementedError

    def shutdown(self) -> None:
        """에이전트 종료 정리. 리소스 해제."""
        raise NotImplementedError

    # =========================================================================
    # CognitiveBus Integration (bus가 호출하는 메서드)
    # =========================================================================

    def emit(self, thought: Thought) -> None:
        """
        CognitiveBus에 Thought를 발행합니다.
        이 에이전트를 source로 설정하고, bus.publish()를 호출합니다.
        """
        if self.bus is not None:
            thought.source = self.id()
            self.bus.publish(thought)
        else:
            print(f"⚠️ [{self.id()}] CognitiveBus에 연결되지 않아 Thought를 발행할 수 없습니다.")

    def emit_new(self, thought_type: str, content: str, importance: float = 0.5,
                 context: dict = None, emotion: dict = None, parent_id: str = None) -> Thought:
        """편의 메서드: 새 Thought를 생성하고 즉시 발행합니다."""
        thought = Thought(
            source=self.id(),
            thought_type=thought_type,
            content=content,
            importance=importance,
            context=context,
            emotion=emotion,
            parent_id=parent_id,
        )
        self.emit(thought)
        return thought

    # =========================================================================
    # Legacy IAgent Compatibility
    # =========================================================================

    def process(self, message: Message) -> bool:
        """
        기존 AgentBus의 Message dispatch와 호환.
        Message를 Thought로 변환하여 on_thought()에 위임합니다.
        """
        thought = Thought(
            source=message.source,
            thought_type="dialogue" if message.action == "chat" else "action",
            content=str(message.payload.get("message", message.payload) if isinstance(message.payload, dict) else message.payload),
            importance=0.5,
            context={"legacy_action": message.action, "legacy_payload": message.payload},
        )

        result_thought = self.on_thought(thought)

        # Legacy 호환: on_thought의 결과를 message.payload["result"]에 반영
        if result_thought and isinstance(message.payload, dict):
            message.payload["result"] = result_thought.content if isinstance(result_thought, Thought) else str(result_thought)
            return True

        return result_thought is not None

    # =========================================================================
    # State Management (Self-Healing 지원)
    # =========================================================================

    def get_state(self) -> dict:
        """
        에이전트의 현재 내부 상태를 스냅샷으로 반환합니다.
        RecoveryEngine이 주기적으로 호출하여 복구 포인트를 저장합니다.
        """
        return {
            "agent_id": self.id(),
            "running": self._running,
            "state": self._state.copy(),
            "thought_log_size": len(self._thought_log),
            "snapshot_time": time.time(),
        }

    def restore_state(self, state: dict) -> None:
        """
        저장된 스냅샷으로부터 에이전트 상태를 복원합니다.
        RecoveryEngine이 크래시 후 호출합니다.
        """
        self._state = state.get("state", {})
        print(f"🔄 [{self.id()}] 상태 복원 완료 (스냅샷 시각: {state.get('snapshot_time', 'N/A')})")

    # =========================================================================
    # Periodic Tick (주기적 작업용)
    # =========================================================================

    def set_tick_interval(self, seconds: float) -> None:
        """주기적 tick 간격을 설정합니다 (0이면 비활성화)."""
        self._tick_interval = seconds

    def on_tick(self) -> None:
        """
        주기적으로 호출되는 메서드. 데이터 수집, 기억 통합 등에 사용.
        set_tick_interval()로 간격을 설정한 경우에만 호출됩니다.
        """
        pass  # 서브클래스에서 오버라이드

    def start_tick_loop(self) -> None:
        """백그라운드 tick 루프를 시작합니다."""
        if self._tick_interval <= 0:
            return

        self._running = True

        def _loop():
            while self._running:
                try:
                    self.on_tick()
                except Exception as e:
                    print(f"❌ [{self.id()}] tick 오류: {e}")
                time.sleep(self._tick_interval)

        self._tick_thread = threading.Thread(
            target=_loop,
            name=f"tick-{self.id()}",
            daemon=True
        )
        self._tick_thread.start()

    def stop_tick_loop(self) -> None:
        """백그라운드 tick 루프를 중지합니다."""
        self._running = False
        if self._tick_thread and self._tick_thread.is_alive():
            self._tick_thread.join(timeout=5)
            self._tick_thread = None

    # =========================================================================
    # Thought Logging
    # =========================================================================

    def _log_thought(self, thought: Thought) -> None:
        """처리한 Thought를 내부 로그에 기록합니다."""
        self._thought_log.append({
            "thought_id": thought.id,
            "type": thought.thought_type,
            "source": thought.source,
            "content_preview": thought.content[:50],
            "importance": thought.importance,
            "received_at": time.time(),
        })
        if len(self._thought_log) > self._max_log_size:
            self._thought_log.pop(0)

    def __repr__(self) -> str:
        return f"CognitiveAgent(id='{self.id()}', topics={self.subscribed_topics()}, running={self._running})"
