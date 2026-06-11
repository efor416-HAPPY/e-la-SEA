# -*- coding: utf-8 -*-
"""
🧠 ARA AI Cognitive Agent: Reasoning Agent (ARA 3.0)
Autonomous reasoning agent that subscribes to perception Thoughts
and performs deep analysis using ReasoningCore + KnowledgeGraph + Memory.
Unlike ChatAgent (dialogue-focused), this agent does background reasoning.
"""

from backend.agents.base_cognitive_agent import ICognitiveAgent
from backend.kernel.message import Thought
from typing import Optional


class ReasoningCognitiveAgent(ICognitiveAgent):
    """자율 추론 인지 에이전트. 인지 입력을 받아 배경에서 분석합니다."""

    def __init__(self):
        super().__init__()
        self._analysis_count = 0

    def id(self) -> str:
        return "reasoning_agent"

    def subscribed_topics(self) -> list[str]:
        return ["perception", "observation"]

    def initialize(self) -> bool:
        print("🧠 [ReasoningAgent] 추론 인지 에이전트 초기화 완료.")
        return True

    def on_thought(self, thought: Thought) -> Optional[Thought]:
        """
        perception/observation Thought를 받아 자율적으로 분석합니다.
        - 기억 검색으로 맥락 확보
        - KnowledgeGraph로 관련 개념 탐색
        - 종합하여 reasoning Thought 발행
        """
        if thought.importance < 0.6:
            return None  # 중요도 낮은 것은 무시

        analysis_parts = []

        # 1. 기억 검색
        if self.kernel:
            memories = self.kernel.memory_core.search(thought.content)
            if memories:
                mem_context = "; ".join(m.description[:50] for m in memories[:3])
                analysis_parts.append(f"관련 기억: {mem_context}")

            # 2. KnowledgeGraph 탐색
            if hasattr(self.kernel, 'knowledge_graph'):
                concepts = self.kernel.knowledge_graph.auto_extract(thought)
                if concepts:
                    for concept in concepts[:2]:
                        related = self.kernel.knowledge_graph.query_related(concept, depth=1, limit=3)
                        if related:
                            labels = [r["label"] for r in related]
                            analysis_parts.append(f"{concept} 연관: {', '.join(labels)}")

            # 3. 에피소드 기억 검색
            episodes = self.kernel.memory_core.recall_episodes(thought.content, limit=2)
            if episodes:
                for ep in episodes:
                    analysis_parts.append(f"유사 경험: {ep.get('trigger', '')[:30]}")

        if not analysis_parts:
            return None

        self._analysis_count += 1
        analysis = f"[자율 분석 #{self._analysis_count}] {thought.content[:30]}... | " + " | ".join(analysis_parts)

        return thought.derive(
            source=self.id(),
            thought_type="reasoning",
            content=analysis,
            importance=thought.importance * 0.8,
            context={
                "original_source": thought.source,
                "analysis_number": self._analysis_count,
            },
        )

    def get_state(self) -> dict:
        base = super().get_state()
        base["state"]["analysis_count"] = self._analysis_count
        return base

    def shutdown(self) -> None:
        print("🧠 [ReasoningAgent] 종료.")


# Global instance
reasoning_cognitive_agent = ReasoningCognitiveAgent()
