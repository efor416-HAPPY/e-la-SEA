# -*- coding: utf-8 -*-
"""
📰 ARA AI Cognitive Agent: News Agent (ARA 3.0)
Periodically collects news and emits perception Thoughts into CognitiveBus.
Other agents (Memory, Planner, Reasoning) react automatically.
"""

import time
import os
import json
from backend.agents.base_cognitive_agent import ICognitiveAgent
from backend.kernel.message import Thought
from typing import Optional


class NewsCognitiveAgent(ICognitiveAgent):
    """뉴스 수집 인지 에이전트. 외부 뉴스를 인지(perception)하여 CognitiveBus에 전파합니다."""

    def __init__(self):
        super().__init__()
        self._news_cache: list[dict] = []
        self._collection_count = 0
        self.set_tick_interval(600.0)  # 10분마다 뉴스 수집

    def id(self) -> str:
        return "news"

    def subscribed_topics(self) -> list[str]:
        return ["plan"]  # 계획에서 뉴스 수집 요청을 받을 수 있음

    def initialize(self) -> bool:
        print("📰 [NewsAgent] 뉴스 인지 에이전트 초기화 완료.")
        return True

    def on_thought(self, thought: Thought) -> Optional[Thought]:
        """계획에서 뉴스 수집 요청이 오면 즉시 수집합니다."""
        if thought.thought_type == "plan" and "뉴스" in thought.content:
            articles = self._fetch_news()
            if articles:
                return thought.derive(
                    source=self.id(),
                    thought_type="perception",
                    content=f"뉴스 {len(articles)}건 수집: {articles[0].get('title', '')}",
                    importance=0.7,
                    context={"articles": articles[:5]},
                )
        return None

    def on_tick(self) -> None:
        """주기적으로 뉴스를 수집하고 CognitiveBus에 발행합니다."""
        articles = self._fetch_news()
        if articles:
            for article in articles[:3]:  # 상위 3건만 발행
                self.emit_new(
                    thought_type="perception",
                    content=f"[뉴스] {article.get('title', '제목 없음')}",
                    importance=0.65,
                    context={
                        "source_url": article.get("link", ""),
                        "description": article.get("description", ""),
                        "news_source": article.get("source", ""),
                    },
                )
            self._collection_count += 1

    def _fetch_news(self) -> list[dict]:
        """뉴스를 수집합니다. (RSS/API 또는 캐시 파일)"""
        # 캐시된 뉴스 파일 확인
        cache_path = "downloads/news_cache.json"
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    self._news_cache = data
                    return data
            except Exception:
                pass

        # 캐시가 없으면 빈 목록 반환 (실제 API 연동 시 확장)
        return self._news_cache

    def get_state(self) -> dict:
        base = super().get_state()
        base["state"]["collection_count"] = self._collection_count
        base["state"]["cache_size"] = len(self._news_cache)
        return base

    def shutdown(self) -> None:
        self.stop_tick_loop()
        print("📰 [NewsAgent] 종료.")


# Global instance
news_cognitive_agent = NewsCognitiveAgent()
