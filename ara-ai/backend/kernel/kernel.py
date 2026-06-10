# -*- coding: utf-8 -*-
"""
🌱 ARA AI Kernel 3.0 — Cognitive Agent Platform Orchestrator
The central brain of ARA OS. Coordinates all cognitive subsystems:

Architecture (ARA 3.0):
    AraKernel
    ├── CognitiveBus        (중추 신경계 — Pub/Sub Thought 전파)
    ├── MemoryCore           (5계층 인지 기억: STM/MTM/LTM/Vector/Episode)
    ├── EmotionEngine        (감정 엔진 — Thought에 따라 감정 변화)
    ├── KnowledgeGraph       (지식 그래프 — 개념 간 관계)
    ├── ReasoningCore        (추론 엔진)
    ├── PlannerEngine        (계획 엔진 — 목표→단계→실행→학습)
    ├── SecurityCore         (보안 엔진)
    ├── AuditCore            (감사 엔진)
    ├── AgentRuntime         (에이전트 수명 관리)
    ├── RecoveryEngine       (자가 치유)
    └── Agents               (인지 에이전트들 — CognitiveBus에 연결)
"""

from backend.agents.base_agent import IAgent
from backend.kernel.cognitive_bus import CognitiveBus
from backend.kernel.message import Message, Thought
from backend.kernel.memory_core import MemoryCore
from backend.kernel.reasoning_core import ReasoningCore
from backend.kernel.emotion_engine import EmotionEngine
from backend.kernel.planner_engine import PlannerEngine
from backend.kernel.knowledge_graph import KnowledgeGraph
from backend.kernel.agent_runtime import AgentRuntime
from backend.kernel.recovery_engine import RecoveryEngine
from backend.kernel.security_core import SecurityCore
from backend.kernel.audit_core import AuditCore


class AraKernel:
    """
    ARA 3.0 인지 에이전트 플랫폼의 마이크로커널.
    모든 인지 엔진과 에이전트를 관리하고 CognitiveBus를 통해 연결합니다.
    """

    def __init__(self):
        # =====================================================================
        # 1. Neural Infrastructure
        # =====================================================================

        # CognitiveBus — 중추 신경계 (Pub/Sub + Priority Queue)
        self.cognitive_bus = CognitiveBus()

        # Legacy compatibility: self.bus points to CognitiveBus
        self.bus = self.cognitive_bus

        # =====================================================================
        # 2. Cognitive Engines
        # =====================================================================

        # Memory Core — 5계층 인지 기억
        self.memory_core = MemoryCore()

        # Emotion Engine — 감정 엔진
        self.emotion_engine = EmotionEngine()

        # Knowledge Graph — 지식 그래프
        self.knowledge_graph = KnowledgeGraph()

        # Reasoning Core — 추론 엔진
        self.reasoning_core = ReasoningCore(self.memory_core)

        # Planner Engine — 계획 엔진
        self.planner_engine = PlannerEngine()

        # =====================================================================
        # 3. Security & Audit (기존 유지)
        # =====================================================================
        self.security_core = SecurityCore()
        self.audit_core = AuditCore()

        # =====================================================================
        # 4. Runtime & Recovery
        # =====================================================================
        self.agent_runtime = AgentRuntime(self.cognitive_bus)
        self.recovery_engine = RecoveryEngine(self.agent_runtime)

        # =====================================================================
        # 5. Kernel State
        # =====================================================================
        self.running = False
        self._registered_agent_ids: list[str] = []

        # =====================================================================
        # 6. Wire CognitiveBus Global Hooks
        # =====================================================================
        self._setup_bus_hooks()

    # =========================================================================
    # Agent Registration
    # =========================================================================

    def register_agent(self, agent) -> None:
        """
        에이전트를 커널에 등록합니다.
        ICognitiveAgent와 레거시 IAgent 모두 지원합니다.
        """
        agent.kernel = self

        # Check if it's a cognitive agent (has subscribed_topics)
        is_cognitive = hasattr(agent, 'subscribed_topics') and hasattr(agent, 'on_thought')

        if is_cognitive:
            # Register on the CognitiveBus (topic-based pub/sub)
            self.cognitive_bus.register(agent)
        else:
            # Legacy agent: register on the CognitiveBus with dispatch compatibility
            self.cognitive_bus._agents[agent.id()] = agent
            agent.bus = self.cognitive_bus
            print(f"🌱 [AraKernel] 레거시 에이전트 등록: '{agent.id()}'")

        self._registered_agent_ids.append(agent.id())

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def _setup_bus_hooks(self) -> None:
        """CognitiveBus에 글로벌 훅을 등록합니다."""

        def _emotion_hook(thought: Thought):
            """모든 Thought에 대해 감정 엔진을 업데이트합니다."""
            try:
                self.emotion_engine.update(thought)
            except Exception:
                pass

        def _knowledge_hook(thought: Thought):
            """모든 Thought에서 지식 그래프 개념을 자동 추출합니다."""
            try:
                self.knowledge_graph.auto_extract(thought)
            except Exception:
                pass

        def _memory_hook(thought: Thought):
            """중요한 Thought를 자동으로 기억 시스템에 저장합니다."""
            try:
                if thought.importance >= 0.5 and thought.thought_type != "system":
                    self.memory_core.perceive(
                        source=thought.source,
                        content=thought.content,
                        importance=thought.importance,
                        context=thought.context,
                        thought_type=thought.thought_type,
                    )
            except Exception:
                pass

        self.cognitive_bus.add_hook(_emotion_hook)
        self.cognitive_bus.add_hook(_knowledge_hook)
        self.cognitive_bus.add_hook(_memory_hook)

    def start(self) -> None:
        """커널을 부팅하고 모든 에이전트를 초기화합니다."""
        self.running = True
        self.audit_core.log(
            "SYSTEM_LIFECYCLE", "Kernel", "Startup",
            "ARA 3.0 Cognitive Agent Platform boot sequence initiated."
        )

        # Register default agents (backward compatible imports)
        from backend.agents.memory_agent import memory_agent
        from backend.agents.chat_agent import chat_agent
        from backend.agents.planner_agent import planner_agent

        self.register_agent(memory_agent)
        self.register_agent(chat_agent)
        self.register_agent(planner_agent)

        # Initialize all registered agents
        for agent_id in self._registered_agent_ids:
            agent = self.cognitive_bus._agents.get(agent_id)
            if agent:
                try:
                    agent.initialize()
                except Exception as e:
                    print(f"❌ [AraKernel] 에이전트 '{agent_id}' 초기화 실패: {e}")

        # Start subsystems
        self.cognitive_bus.start()           # 인지 버스 처리 루프
        self.memory_core.start_consolidation()  # 기억 통합 루프
        self.recovery_engine.start()          # 자가 치유 모니터링

        # Emit system boot thought
        boot_thought = Thought(
            source="kernel",
            thought_type="system",
            content="ARA 3.0 Cognitive Kernel 부팅 완료",
            importance=0.9,
            emotion={"confidence": 0.8},
            context={
                "registered_agents": self._registered_agent_ids,
                "bus_stats": self.cognitive_bus.get_stats(),
                "emotion": self.emotion_engine.get_state(),
                "knowledge_concepts": self.knowledge_graph.get_stats()["total_concepts"],
            }
        )
        self.cognitive_bus.publish(boot_thought)

        print("🌱 [AraKernel 3.0] Cognitive Agent Platform 부팅 완료.")
        print(f"   ├── CognitiveBus: {self.cognitive_bus}")
        print(f"   ├── MemoryCore: {self.memory_core}")
        print(f"   ├── EmotionEngine: {self.emotion_engine}")
        print(f"   ├── KnowledgeGraph: {self.knowledge_graph}")
        print(f"   ├── PlannerEngine: {self.planner_engine}")
        print(f"   └── RecoveryEngine: {self.recovery_engine}")

    def stop(self) -> None:
        """커널과 모든 에이전트를 안전하게 종료합니다."""
        self.running = False

        # Stop subsystems in reverse order
        self.recovery_engine.stop()
        self.memory_core.stop_consolidation()
        self.cognitive_bus.stop()

        # Save persistent state
        self.knowledge_graph.save()

        # Shutdown all registered agents
        for agent_id in list(self._registered_agent_ids):
            agent = self.cognitive_bus._agents.get(agent_id)
            if agent:
                try:
                    agent.shutdown()
                except Exception as e:
                    print(f"❌ [AraKernel] 에이전트 '{agent_id}' 종료 오류: {e}")

        self.audit_core.log(
            "SYSTEM_LIFECYCLE", "Kernel", "Shutdown",
            "ARA 3.0 Cognitive Agent Platform shutdown completed."
        )
        print("🌱 [AraKernel 3.0] 종료 완료.")

    # =========================================================================
    # Cognitive Shortcuts
    # =========================================================================

    def think(self, content: str, importance: float = 0.5) -> None:
        """커널 레벨에서 Thought를 발행합니다."""
        thought = Thought(
            source="kernel",
            thought_type="system",
            content=content,
            importance=importance,
        )
        self.cognitive_bus.publish(thought)

    def get_cognitive_state(self) -> dict:
        """커널의 전체 인지 상태를 반환합니다."""
        return {
            "running": self.running,
            "agents": self._registered_agent_ids,
            "bus_stats": self.cognitive_bus.get_stats(),
            "memory_stats": self.memory_core.get_cognitive_stats(),
            "emotion": self.emotion_engine.get_emotional_context(),
            "knowledge_graph": self.knowledge_graph.get_stats(),
            "planner": self.planner_engine.get_stats(),
            "recovery": {
                "snapshots": len(self.recovery_engine._snapshots),
                "recoveries": len(self.recovery_engine._recovery_history),
            },
            "recent_thoughts": self.cognitive_bus.get_recent_thoughts(limit=10),
        }


# ============================================================================
# Global Kernel Coordinator Instance
# ============================================================================
kernel_instance = AraKernel()

