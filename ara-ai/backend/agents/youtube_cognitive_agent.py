# -*- coding: utf-8 -*-
"""
📺 ARA AI Cognitive Agent: YouTube Agent (ARA 3.0)
Monitors YouTube content and emits perception Thoughts.
"""

import time
import os
import json
from backend.agents.base_cognitive_agent import ICognitiveAgent
from backend.kernel.message import Thought
from typing import Optional


class YouTubeCognitiveAgent(ICognitiveAgent):
    """YouTube 콘텐츠 수집/분석 인지 에이전트."""

    def __init__(self):
        super().__init__()
        self._video_cache: list[dict] = []
        self.set_tick_interval(900.0)  # 15분마다 체크

    def id(self) -> str:
        return "youtube"

    def subscribed_topics(self) -> list[str]:
        return ["plan"]

    def initialize(self) -> bool:
        print("📺 [YouTubeAgent] YouTube 인지 에이전트 초기화 완료.")
        return True

    def on_thought(self, thought: Thought) -> Optional[Thought]:
        """계획에서 YouTube 콘텐츠 요청이 오면 처리합니다."""
        if thought.thought_type == "plan" and ("유튜브" in thought.content or "영상" in thought.content):
            return thought.derive(
                source=self.id(),
                thought_type="perception",
                content=f"YouTube 콘텐츠 검색 완료 (캐시: {len(self._video_cache)}건)",
                importance=0.6,
                context={"videos": self._video_cache[:5]},
            )
        return None

    def on_tick(self) -> None:
        """주기적으로 YouTube 콘텐츠를 확인합니다."""
        cache_path = "downloads/youtube_cache.json"
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    self._video_cache = json.load(f)
            except Exception:
                pass

    def shutdown(self) -> None:
        self.stop_tick_loop()
        print("📺 [YouTubeAgent] 종료.")


# Global instance
youtube_cognitive_agent = YouTubeCognitiveAgent()
