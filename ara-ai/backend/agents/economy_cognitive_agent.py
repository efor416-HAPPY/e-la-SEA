# -*- coding: utf-8 -*-
"""
📊 ARA AI Cognitive Agent: Economy Agent (ARA 3.0)
Monitors economic indicators (gold, rates, forex) and emits perception Thoughts.
Connects to KnowledgeGraph for relationship-based analysis.
"""

import time
import os
import json
from backend.agents.base_cognitive_agent import ICognitiveAgent
from backend.kernel.message import Thought
from typing import Optional


class EconomyCognitiveAgent(ICognitiveAgent):
    """경제 지표 모니터링 인지 에이전트."""

    def __init__(self):
        super().__init__()
        self._indicators: dict = {}
        self.set_tick_interval(1800.0)  # 30분마다 체크

    def id(self) -> str:
        return "economy"

    def subscribed_topics(self) -> list[str]:
        return ["perception", "plan"]

    def initialize(self) -> bool:
        self._load_indicators()
        print("📊 [EconomyAgent] 경제 인지 에이전트 초기화 완료.")
        return True

    def on_thought(self, thought: Thought) -> Optional[Thought]:
        """경제 관련 인지/계획에 반응합니다."""
        content_lower = thought.content.lower()
        econ_keywords = ["금", "금리", "달러", "환율", "경제", "주식", "인플레이션", "유가", "채권"]

        if any(kw in content_lower for kw in econ_keywords):
            # KnowledgeGraph에서 관련 개념 탐색
            related_concepts = []
            if self.kernel and hasattr(self.kernel, 'knowledge_graph'):
                for kw in econ_keywords:
                    if kw in content_lower:
                        related = self.kernel.knowledge_graph.query_related(kw, depth=1, limit=5)
                        related_concepts.extend([r["label"] for r in related])

            analysis = f"경제 분석: {thought.content[:40]}... 관련 지표: {', '.join(set(related_concepts[:8]))}"

            return thought.derive(
                source=self.id(),
                thought_type="reasoning",
                content=analysis,
                importance=0.7,
                context={
                    "indicators": self._indicators,
                    "related_concepts": list(set(related_concepts[:10])),
                },
            )
        return None

    def on_tick(self) -> None:
        """주기적으로 경제 지표를 갱신합니다."""
        self._load_indicators()
        if self._indicators:
            self.emit_new(
                thought_type="perception",
                content=f"경제 지표 갱신: {json.dumps(self._indicators, ensure_ascii=False)[:100]}",
                importance=0.5,
                context={"indicators": self._indicators},
            )

    def _load_indicators(self) -> None:
        """경제 지표를 로드합니다."""
        cache_path = "downloads/economy_indicators.json"
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    self._indicators = json.load(f)
            except Exception:
                pass

    def shutdown(self) -> None:
        self.stop_tick_loop()
        print("📊 [EconomyAgent] 종료.")


# Global instance
economy_cognitive_agent = EconomyCognitiveAgent()
