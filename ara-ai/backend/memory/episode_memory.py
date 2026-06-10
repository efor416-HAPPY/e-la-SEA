# -*- coding: utf-8 -*-
"""
📖 ARA AI Memory Subsystem: Episodic Memory
Records sequences of events as "episodes" — structured experiences with
temporal context (when), content (what), and outcome (why/result).

Characteristics:
  - Episodes are time-bounded event sequences
  - Each episode has a trigger, a series of events, and an outcome
  - Similar past episodes can be recalled for reasoning by analogy
  - Stored persistently in JSON for cross-session recall
"""

import os
import json
import time
import threading
from typing import Optional


class EpisodeEvent:
    """에피소드 내 개별 이벤트."""

    def __init__(self, agent_id: str, event_type: str, content: str,
                 importance: float = 0.5, metadata: dict = None):
        self.agent_id = agent_id
        self.event_type = event_type
        self.content = content
        self.importance = importance
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.created_at = time.strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "content": self.content,
            "importance": self.importance,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "created_at": self.created_at,
        }


class Episode:
    """
    에피소드 — 하나의 경험 단위.
    시작 트리거, 이벤트 시퀀스, 결과로 구성됩니다.
    """

    def __init__(self, trigger: str, episode_type: str = "general"):
        self.id = f"ep_{int(time.time() * 1000)}"
        self.trigger = trigger           # 에피소드 시작 원인
        self.episode_type = episode_type  # "dialogue", "analysis", "collection", "planning"
        self.events: list[EpisodeEvent] = []
        self.outcome: Optional[str] = None
        self.outcome_success: Optional[bool] = None
        self.started_at = time.time()
        self.ended_at: Optional[float] = None
        self.tags: list[str] = []

    def add_event(self, agent_id: str, event_type: str, content: str,
                  importance: float = 0.5, metadata: dict = None) -> None:
        """에피소드에 이벤트를 추가합니다."""
        self.events.append(EpisodeEvent(
            agent_id=agent_id,
            event_type=event_type,
            content=content,
            importance=importance,
            metadata=metadata,
        ))

    def end(self, outcome: str, success: bool = True) -> None:
        """에피소드를 종료하고 결과를 기록합니다."""
        self.outcome = outcome
        self.outcome_success = success
        self.ended_at = time.time()

    @property
    def duration(self) -> float:
        """에피소드 지속 시간 (초)."""
        end = self.ended_at or time.time()
        return end - self.started_at

    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    @property
    def avg_importance(self) -> float:
        if not self.events:
            return 0.0
        return sum(e.importance for e in self.events) / len(self.events)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trigger": self.trigger,
            "episode_type": self.episode_type,
            "events": [e.to_dict() for e in self.events],
            "outcome": self.outcome,
            "outcome_success": self.outcome_success,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration": self.duration,
            "tags": self.tags,
            "avg_importance": self.avg_importance,
        }

    def summary(self) -> str:
        """에피소드의 자연어 요약."""
        status = "진행 중" if self.is_active else ("성공" if self.outcome_success else "실패")
        return (
            f"[{self.episode_type}] {self.trigger} → "
            f"{len(self.events)}개 이벤트, {self.duration:.1f}초, {status}"
            f"{': ' + self.outcome if self.outcome else ''}"
        )


class EpisodeMemory:
    """
    에피소드 기억.
    '언제, 무엇을, 왜' 형태의 경험 시퀀스를 기록하고 유사 경험을 검색합니다.

    에피소드 기억은 추론 엔진이 과거 경험에 기반한 판단을 내릴 수 있게 합니다:
      "지난번 금리 인상 뉴스가 들어왔을 때, 경제 분석 → 금값 예측을 수행했고 결과가 좋았다"
    """

    def __init__(self, storage_path: str = "downloads/episode_memory.json", max_episodes: int = 500):
        self._episodes: list[Episode] = []
        self._current_episode: Optional[Episode] = None
        self._storage_path = storage_path
        self._max_episodes = max_episodes
        self._lock = threading.Lock()

        # Load persisted episodes
        self._load()

    def begin_episode(self, trigger: str, episode_type: str = "general", tags: list = None) -> Episode:
        """새 에피소드를 시작합니다."""
        with self._lock:
            # 현재 진행 중인 에피소드가 있으면 자동 종료
            if self._current_episode and self._current_episode.is_active:
                self._current_episode.end("자동 종료 (새 에피소드 시작)", success=True)
                self._episodes.append(self._current_episode)

            episode = Episode(trigger=trigger, episode_type=episode_type)
            if tags:
                episode.tags = tags
            self._current_episode = episode
            return episode

    def add_event(self, agent_id: str, event_type: str, content: str,
                  importance: float = 0.5, metadata: dict = None) -> None:
        """현재 에피소드에 이벤트를 추가합니다."""
        with self._lock:
            if self._current_episode is None:
                # 에피소드가 없으면 자동 생성
                self._current_episode = Episode(trigger="auto", episode_type="auto")

            self._current_episode.add_event(
                agent_id=agent_id,
                event_type=event_type,
                content=content,
                importance=importance,
                metadata=metadata,
            )

    def end_episode(self, outcome: str, success: bool = True) -> Optional[Episode]:
        """현재 에피소드를 종료하고 아카이브합니다."""
        with self._lock:
            if self._current_episode is None:
                return None

            self._current_episode.end(outcome, success)
            completed = self._current_episode
            self._episodes.append(completed)
            self._current_episode = None

            # 용량 제한
            while len(self._episodes) > self._max_episodes:
                self._episodes.pop(0)

            # Persist
            self._save_unlocked()
            return completed

    def recall_similar(self, query: str, limit: int = 5) -> list[dict]:
        """유사한 과거 에피소드를 검색합니다."""
        results = []
        query_lower = query.lower()
        with self._lock:
            for ep in reversed(self._episodes):  # 최근 것부터
                trigger_match = query_lower in ep.trigger.lower()
                event_match = any(
                    query_lower in e.content.lower() for e in ep.events
                )
                tag_match = any(query_lower in t.lower() for t in ep.tags)
                outcome_match = ep.outcome and query_lower in ep.outcome.lower()

                if trigger_match or event_match or tag_match or outcome_match:
                    results.append(ep.to_dict())
                    if len(results) >= limit:
                        break

        return results

    def recall_by_type(self, episode_type: str, limit: int = 10) -> list[dict]:
        """에피소드 유형으로 검색합니다."""
        with self._lock:
            matching = [ep for ep in reversed(self._episodes) if ep.episode_type == episode_type]
            return [ep.to_dict() for ep in matching[:limit]]

    def get_current_episode(self) -> Optional[dict]:
        """현재 진행 중인 에피소드를 반환합니다."""
        with self._lock:
            if self._current_episode:
                return self._current_episode.to_dict()
            return None

    def get_stats(self) -> dict:
        with self._lock:
            total = len(self._episodes)
            successful = sum(1 for ep in self._episodes if ep.outcome_success is True)
            failed = sum(1 for ep in self._episodes if ep.outcome_success is False)
            return {
                "total_episodes": total,
                "successful": successful,
                "failed": failed,
                "current_active": self._current_episode is not None,
            }

    # =========================================================================
    # Persistence
    # =========================================================================

    def _save_unlocked(self) -> None:
        """에피소드를 JSON에 저장합니다 (lock 보유 상태)."""
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            data = [ep.to_dict() for ep in self._episodes[-self._max_episodes:]]
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ [EpisodeMemory] 저장 실패: {e}")

    def _load(self) -> None:
        """저장된 에피소드를 로드합니다."""
        if not os.path.exists(self._storage_path):
            return
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Episodes are stored as dicts — we don't reconstruct full Episode objects
            # for past episodes; they're kept as dict snapshots for recall
            for ep_dict in data[-self._max_episodes:]:
                ep = Episode(trigger=ep_dict.get("trigger", ""), episode_type=ep_dict.get("episode_type", ""))
                ep.id = ep_dict.get("id", ep.id)
                ep.outcome = ep_dict.get("outcome")
                ep.outcome_success = ep_dict.get("outcome_success")
                ep.started_at = ep_dict.get("started_at", 0)
                ep.ended_at = ep_dict.get("ended_at")
                ep.tags = ep_dict.get("tags", [])
                self._episodes.append(ep)
        except Exception as e:
            print(f"⚠️ [EpisodeMemory] 로드 실패: {e}")

    def __repr__(self) -> str:
        return f"EpisodeMemory(total={len(self._episodes)}, active={self._current_episode is not None})"
