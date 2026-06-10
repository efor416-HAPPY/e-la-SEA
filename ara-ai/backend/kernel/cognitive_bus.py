# -*- coding: utf-8 -*-
"""
🧠 ARA AI CognitiveBus (ARA 3.0 Central Nervous System)
Pub/Sub based neural bus connecting all cognitive agents.

Unlike the legacy AgentBus (1:1 direct dispatch), the CognitiveBus:
  - Routes Thoughts by topic (thought_type) to all subscribed agents
  - Supports wildcard subscriptions ("*") and source-specific subscriptions
  - Maintains a priority queue ordered by importance
  - Tracks thought propagation traces
  - Runs an async processing loop in a background thread
  - Cascades derivative Thoughts automatically (agent reactions)
"""

import time
import threading
from collections import deque
from queue import PriorityQueue, Empty
from typing import TYPE_CHECKING, Optional

from backend.kernel.message import Thought, Message

if TYPE_CHECKING:
    from backend.agents.base_cognitive_agent import ICognitiveAgent


# ============================================================================
# Priority wrapper for PriorityQueue (higher importance = higher priority)
# ============================================================================

class _PrioritizedThought:
    """PriorityQueue에 넣기 위한 래퍼. importance가 높을수록 먼저 처리."""

    def __init__(self, thought: Thought):
        self.thought = thought
        # PriorityQueue는 작은 값이 먼저이므로 음수로 변환
        self.priority = -thought.importance

    def __lt__(self, other: '_PrioritizedThought') -> bool:
        if self.priority == other.priority:
            return self.thought.timestamp < other.thought.timestamp
        return self.priority < other.priority


# ============================================================================
# CognitiveBus — 아라의 중추 신경계
# ============================================================================

class CognitiveBus:
    """
    아라의 중추 신경계.
    모든 인지 에이전트를 연결하고, Thought를 토픽 기반으로 자동 전파합니다.

    전파 흐름 예시:
        NewsAgent.emit(Thought(type="perception", content="금리 인상"))
          → CognitiveBus.publish()
          → "perception" 토픽 구독자들에게 전파:
              → MemoryAgent.on_thought()  → 기억 저장
              → ReasoningAgent.on_thought() → 분석 시작
              → EmotionEngine → curiosity 증가
    """

    def __init__(self, max_history: int = 1000, process_interval: float = 0.05):
        # Agent Registry
        self._agents: dict[str, 'ICognitiveAgent'] = {}

        # Topic Subscriptions: topic -> set of agent_ids
        self._subscriptions: dict[str, set[str]] = {}

        # Priority Queue for ordered Thought processing
        self._queue: PriorityQueue = PriorityQueue()

        # Thought History (circular buffer for recent thoughts)
        self._history: deque[Thought] = deque(maxlen=max_history)

        # Processing thread
        self._process_interval = process_interval
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Statistics
        self._stats = {
            "total_published": 0,
            "total_delivered": 0,
            "total_dropped": 0,
            "total_cascaded": 0,
            "agents_registered": 0,
        }

        # Hooks: external observers can register callbacks
        self._global_hooks: list = []  # Called for every Thought (EmotionEngine, AuditCore, etc.)

    # =========================================================================
    # Agent Registration
    # =========================================================================

    def register(self, agent: 'ICognitiveAgent') -> None:
        """인지 에이전트를 버스에 등록하고 토픽 구독을 설정합니다."""
        agent_id = agent.id()

        with self._lock:
            self._agents[agent_id] = agent
            agent.bus = self

            # Register topic subscriptions
            topics = agent.subscribed_topics()
            for topic in topics:
                if topic not in self._subscriptions:
                    self._subscriptions[topic] = set()
                self._subscriptions[topic].add(agent_id)

            self._stats["agents_registered"] = len(self._agents)

        print(f"🧠 [CognitiveBus] 에이전트 등록: '{agent_id}' → 토픽: {topics}")

    def unregister(self, agent_id: str) -> None:
        """에이전트를 버스에서 제거합니다."""
        with self._lock:
            if agent_id in self._agents:
                # Remove from all subscription lists
                for topic_subs in self._subscriptions.values():
                    topic_subs.discard(agent_id)

                del self._agents[agent_id]
                self._stats["agents_registered"] = len(self._agents)
                print(f"🧠 [CognitiveBus] 에이전트 해제: '{agent_id}'")

    # =========================================================================
    # Publishing (Thought를 큐에 넣고 비동기 처리)
    # =========================================================================

    def publish(self, thought: Thought) -> None:
        """
        Thought를 CognitiveBus에 발행합니다.
        Priority Queue에 삽입되어 중요도 순으로 처리됩니다.
        """
        self._queue.put(_PrioritizedThought(thought))
        self._stats["total_published"] += 1

    def publish_sync(self, thought: Thought) -> list[Thought]:
        """
        동기식 Thought 처리. 즉시 라우팅하고 모든 응답을 수집합니다.
        테스트 및 즉시 응답이 필요한 대화 처리에 사용.
        """
        return self._route_thought(thought)

    # =========================================================================
    # Internal Routing (토픽 기반 전파)
    # =========================================================================

    def _route_thought(self, thought: Thought) -> list[Thought]:
        """Thought를 구독자 에이전트들에게 전파하고 파생 Thought를 수집합니다."""
        derivative_thoughts: list[Thought] = []
        delivered_count = 0

        with self._lock:
            # 1. Determine target agents based on topic subscriptions
            target_agent_ids: set[str] = set()

            # Direct topic match
            topic = thought.thought_type
            if topic in self._subscriptions:
                target_agent_ids.update(self._subscriptions[topic])

            # Wildcard subscribers (receive all thoughts)
            if "*" in self._subscriptions:
                target_agent_ids.update(self._subscriptions["*"])

            # Source-specific subscribers (e.g., "source.news")
            source_topic = f"source.{thought.source}"
            if source_topic in self._subscriptions:
                target_agent_ids.update(self._subscriptions[source_topic])

            # Remove the source agent from targets (don't echo back to sender)
            target_agent_ids.discard(thought.source)

            # Snapshot agents to avoid holding lock during processing
            target_agents = [(aid, self._agents[aid]) for aid in target_agent_ids if aid in self._agents]

        # 2. Deliver to each subscribed agent (outside lock)
        for agent_id, agent in target_agents:
            try:
                thought.add_trace(agent_id)
                result = agent.on_thought(thought)
                agent._log_thought(thought)
                delivered_count += 1

                # Collect derivative Thoughts (agent reactions)
                if result is not None:
                    if isinstance(result, Thought):
                        derivative_thoughts.append(result)
                    elif isinstance(result, list):
                        derivative_thoughts.extend(t for t in result if isinstance(t, Thought))

            except Exception as e:
                print(f"❌ [CognitiveBus] 에이전트 '{agent_id}' Thought 처리 오류: {e}")
                self._stats["total_dropped"] += 1

        # 3. Execute global hooks (EmotionEngine, AuditCore, etc.)
        for hook in self._global_hooks:
            try:
                hook(thought)
            except Exception as e:
                print(f"❌ [CognitiveBus] 글로벌 훅 오류: {e}")

        # 4. Archive thought
        thought.processed = True
        self._history.append(thought)
        self._stats["total_delivered"] += delivered_count

        return derivative_thoughts

    # =========================================================================
    # Background Processing Loop
    # =========================================================================

    def start(self) -> None:
        """백그라운드 Thought 처리 루프를 시작합니다."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._process_loop,
            name="CognitiveBus-ProcessLoop",
            daemon=True
        )
        self._thread.start()
        print("🧠 [CognitiveBus] 인지 버스 처리 루프 가동.")

    def stop(self) -> None:
        """백그라운드 처리 루프를 정지합니다."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            self._thread = None
        print("🧠 [CognitiveBus] 인지 버스 정지.")

    def _process_loop(self) -> None:
        """Priority Queue에서 Thought를 꺼내어 순차 처리합니다."""
        while self._running:
            try:
                prioritized = self._queue.get(timeout=self._process_interval)
                thought = prioritized.thought

                # Route the thought to subscribed agents
                cascaded = self._route_thought(thought)

                # Cascade derivative thoughts (agent reactions trigger further processing)
                for derived in cascaded:
                    self._queue.put(_PrioritizedThought(derived))
                    self._stats["total_cascaded"] += 1

            except Empty:
                # No thoughts in queue — idle cycle
                continue
            except Exception as e:
                print(f"❌ [CognitiveBus] 처리 루프 오류: {e}")

    # =========================================================================
    # Global Hooks
    # =========================================================================

    def add_hook(self, callback) -> None:
        """모든 Thought가 처리될 때 호출되는 글로벌 훅을 등록합니다."""
        self._global_hooks.append(callback)

    def remove_hook(self, callback) -> None:
        """글로벌 훅을 제거합니다."""
        if callback in self._global_hooks:
            self._global_hooks.remove(callback)

    # =========================================================================
    # Query & Statistics
    # =========================================================================

    def get_recent_thoughts(self, limit: int = 50, thought_type: str = None) -> list[dict]:
        """최근 처리된 Thought 이력을 조회합니다."""
        thoughts = list(self._history)
        if thought_type:
            thoughts = [t for t in thoughts if t.thought_type == thought_type]
        return [t.to_dict() for t in thoughts[-limit:]]

    def get_stats(self) -> dict:
        """CognitiveBus 통계를 반환합니다."""
        return {
            **self._stats,
            "queue_size": self._queue.qsize(),
            "history_size": len(self._history),
            "subscriptions": {
                topic: list(agents) for topic, agents in self._subscriptions.items()
            },
            "running": self._running,
        }

    def get_registered_agents(self) -> list[str]:
        """등록된 에이전트 ID 목록을 반환합니다."""
        with self._lock:
            return list(self._agents.keys())

    # =========================================================================
    # Legacy Compatibility (기존 AgentBus.dispatch() 호환)
    # =========================================================================

    def dispatch(self, message: Message) -> bool:
        """
        기존 AgentBus.dispatch() API와 호환되는 래퍼.
        Message를 Thought로 변환하여 대상 에이전트에 직접 전달합니다.
        """
        target = message.target
        with self._lock:
            agent = self._agents.get(target)

        if agent is None:
            print(f"⚠️ [CognitiveBus] Legacy dispatch 대상 '{target}'이 등록되지 않았습니다.")
            return False

        try:
            # Use the agent's legacy process() method for backward compatibility
            if hasattr(agent, 'process'):
                return agent.process(message)
            else:
                # Convert to Thought and use on_thought
                thought = Thought(
                    source=message.source,
                    thought_type="action",
                    content=str(message.payload),
                    context={"legacy_message": message.to_dict()},
                )
                result = agent.on_thought(thought)
                return result is not None
        except Exception as e:
            print(f"❌ [CognitiveBus] Legacy dispatch 오류 '{target}': {e}")
            return False

    def __repr__(self) -> str:
        return (
            f"CognitiveBus(agents={len(self._agents)}, "
            f"queue={self._queue.qsize()}, "
            f"history={len(self._history)}, "
            f"running={self._running})"
        )
