# -*- coding: utf-8 -*-
"""
💾 ARA AI Memory Core 3.0 — 5-Layer Cognitive Memory System
Orchestrates the complete memory hierarchy:
  1. STM  (Short-Term Memory)  — 즉시 컨텍스트 (30s~5min TTL)
  2. MTM  (Medium-Term Memory) — 세션 기억 (1h~24h TTL)
  3. LTM  (Long-Term Memory)   — 영구 저장 (SQLite + JSON)
  4. Vector Memory              — 벡터 유사도 검색
  5. Episodic Memory            — 에피소드(경험) 시퀀스 기억

Memory Consolidation Flow:
    STM → (importance/access decay) → MTM → (frequency consolidation) → LTM
    All layers → Vector index for similarity search
    Actions → Episode recording for reasoning by analogy
"""

import time
import threading
from typing import List, Tuple, Optional, Any
from backend.memory.stm import ShortTermMemory
from backend.memory.mtm import MediumTermMemory
from backend.memory.long_memory import long_memory
from backend.memory.vector_memory import VectorMemory
from backend.memory.episode_memory import EpisodeMemory


# ============================================================================
# Structured Memory Items (backward compatible)
# ============================================================================

class MemoryItem:
    """Base structured item representing gathered knowledge/intelligence."""
    def __init__(self, title: str, link: str, description: str, source: str,
                 scraped_at: str, embedded_vector: str = "[]"):
        self.title = title
        self.link = link
        self.description = description
        self.source = source
        self.scraped_at = scraped_at
        self.embedded_vector = embedded_vector

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "link": self.link,
            "description": self.description,
            "source": self.source,
            "scraped_at": self.scraped_at,
            "embedded_vector": self.embedded_vector
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MemoryItem':
        return cls(
            title=data.get("title", ""),
            link=data.get("link", ""),
            description=data.get("description", ""),
            source=data.get("source", ""),
            scraped_at=data.get("scraped_at", ""),
            embedded_vector=data.get("embedded_vector", "[]")
        )


class DialogueMemoryItem(MemoryItem):
    """Dialogue-specific Memory Item capturing conversation context."""
    def __init__(self, user_msg: str, bot_reply: str, persona: str, timestamp: str = ""):
        if not timestamp:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        desc = f"사용자: {user_msg} | 응답: {bot_reply} | 페르소나: {persona}"
        mock_vec = str(VectorMemory.generate_mock_vector(user_msg))

        super().__init__(
            title=f"대화 기록: {user_msg[:15]}",
            link=f"local-chat://{time.time()}",
            description=desc,
            source="MemoryAgent",
            scraped_at=timestamp,
            embedded_vector=mock_vec
        )
        self.user_msg = user_msg
        self.bot_reply = bot_reply
        self.persona = persona


# ============================================================================
# MemoryCore 3.0 — 5-Layer Cognitive Memory Orchestrator
# ============================================================================

class MemoryCore:
    """
    5계층 인지 기억 시스템 총괄.
    모든 기억 계층을 통합 관리하고, 자동 기억 통합(consolidation)을 수행합니다.

    계층 구조:
        STM (즉시) ←→ MTM (세션) ←→ LTM (영구)
                    ↘         ↗
                   Vector Search
                    ↘         ↗
                   Episode Archive
    """

    def __init__(self):
        # =====================================================================
        # 5 Memory Layers
        # =====================================================================
        self.stm = ShortTermMemory(capacity=20, default_ttl=300.0)
        self.mtm = MediumTermMemory(capacity=200, default_ttl=3600.0)
        self.ltm = long_memory  # 기존 LongTermMemory (Hot/Warm/Cold)
        self.vector = VectorMemory()  # 벡터 유사도 검색
        self.episodic = EpisodeMemory()  # 에피소드 기억

        # Backward compat alias
        self._manager = self.ltm
        self.manager = self.ltm  # main.py에서 memory_core.manager.warm_db 접근

        # =====================================================================
        # Consolidation Thread
        # =====================================================================
        self._consolidation_interval = 60.0  # 60초마다 통합
        self._running = False
        self._consolidation_thread: Optional[threading.Thread] = None

    # =========================================================================
    # Unified Store API
    # =========================================================================

    def store(self, item: MemoryItem) -> None:
        """
        MemoryItem을 모든 관련 기억 계층에 저장합니다.
        - STM: 즉시 컨텍스트로 저장
        - LTM: 영구 보존 (기존 3-tier)
        """
        item_dict = item.to_dict()

        # STM — 즉시 컨텍스트
        self.stm.store(
            key=item.link or item.title,
            value=item_dict,
            importance=0.6
        )

        # LTM — 영구 저장 (기존 store_wisdom)
        self._manager.store_wisdom(item_dict)

    def perceive(self, source: str, content: str, importance: float = 0.5,
                 context: dict = None, thought_type: str = "perception") -> None:
        """
        Thought 기반 인지 입력을 기억 시스템에 저장합니다.
        CognitiveBus의 Thought를 직접 받아 적절한 기억 계층에 분배합니다.
        """
        key = f"{source}:{content[:50]}:{int(time.time())}"
        value = {
            "source": source,
            "content": content,
            "thought_type": thought_type,
            "context": context or {},
            "perceived_at": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        # STM에 항상 저장
        self.stm.store(key=key, value=value, importance=importance)

        # 중요도 높은 인지는 MTM에도 저장
        if importance >= 0.6:
            self.mtm.store(
                key=key, value=value, importance=importance,
                source=source, tags=[thought_type]
            )

        # 매우 중요한 인지는 LTM에 즉시 저장
        if importance >= 0.8:
            self._manager.store_wisdom({
                "title": f"[{thought_type}] {content[:30]}",
                "link": key,
                "description": content,
                "source": source,
                "scraped_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "embedded_vector": str(VectorMemory.generate_mock_vector(content)),
            })

    # =========================================================================
    # Unified Search API
    # =========================================================================

    def search(self, query: str, layers: list = None) -> List[MemoryItem]:
        """
        다계층 통합 검색.
        기본적으로 모든 계층을 검색하고 결과를 통합합니다.
        """
        if layers is None:
            layers = ["stm", "mtm", "ltm"]

        results = []
        seen_keys = set()

        # STM 검색
        if "stm" in layers:
            stm_results = self.stm.search(query)
            for r in stm_results:
                key = str(r.get("key", ""))
                if key not in seen_keys:
                    seen_keys.add(key)
                    # STM 결과를 MemoryItem으로 변환
                    value = r.get("value", {})
                    if isinstance(value, dict) and "title" in value:
                        results.append(MemoryItem.from_dict(value))
                    else:
                        results.append(MemoryItem(
                            title=key[:30],
                            link=key,
                            description=str(value),
                            source="STM",
                            scraped_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                        ))

        # MTM 검색
        if "mtm" in layers:
            mtm_results = self.mtm.search(query)
            for r in mtm_results:
                key = str(r.get("key", ""))
                if key not in seen_keys:
                    seen_keys.add(key)
                    value = r.get("value", {})
                    if isinstance(value, dict) and "title" in value:
                        results.append(MemoryItem.from_dict(value))
                    else:
                        results.append(MemoryItem(
                            title=key[:30],
                            link=key,
                            description=str(value),
                            source="MTM",
                            scraped_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                        ))

        # LTM 검색 (기존 search_memory)
        if "ltm" in layers:
            ltm_results = self._manager.search_memory(query)
            for r in ltm_results:
                link = r.get("link", "")
                if link not in seen_keys:
                    seen_keys.add(link)
                    results.append(MemoryItem.from_dict(r))

        return results

    def recall_episodes(self, query: str, limit: int = 5) -> list[dict]:
        """에피소드 기억에서 유사 경험을 검색합니다."""
        return self.episodic.recall_similar(query, limit=limit)

    # =========================================================================
    # Memory Consolidation (기억 통합)
    # =========================================================================

    def consolidate(self) -> dict:
        """
        기억 통합을 수행합니다.
        STM → MTM: 만료된 중요 기억을 승격
        MTM → LTM: 충분히 접근된 기억을 영구 저장
        """
        stats = {"stm_promoted": 0, "mtm_consolidated": 0}

        # 1. STM → MTM: 만료 + 승격 대상
        promoted_items = self.stm.decay()
        for stm_item in promoted_items:
            self.mtm.promote_from_stm(
                key=stm_item.key,
                value=stm_item.value,
                importance=stm_item.importance,
            )
            stats["stm_promoted"] += 1

        # 2. MTM → LTM: 통합 대상
        consolidated_items = self.mtm.consolidate_to_ltm()
        for mtm_item in consolidated_items:
            value = mtm_item.value
            if isinstance(value, dict):
                self._manager.store_wisdom(value)
            else:
                self._manager.store_wisdom({
                    "title": mtm_item.key[:30],
                    "link": mtm_item.key,
                    "description": str(value),
                    "source": mtm_item.source or "MTM",
                    "scraped_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "embedded_vector": str(VectorMemory.generate_mock_vector(str(value))),
                })
            stats["mtm_consolidated"] += 1

        return stats

    def start_consolidation(self) -> None:
        """백그라운드 기억 통합 루프를 시작합니다."""
        if self._running:
            return
        self._running = True

        def _loop():
            while self._running:
                try:
                    self.consolidate()
                except Exception as e:
                    print(f"❌ [MemoryCore] 기억 통합 오류: {e}")
                time.sleep(self._consolidation_interval)

        self._consolidation_thread = threading.Thread(
            target=_loop,
            name="MemoryCore-Consolidation",
            daemon=True
        )
        self._consolidation_thread.start()
        print("💾 [MemoryCore] 기억 통합 루프 시작 (간격: {:.0f}초)".format(self._consolidation_interval))

    def stop_consolidation(self) -> None:
        """기억 통합 루프를 중지합니다."""
        self._running = False
        if self._consolidation_thread and self._consolidation_thread.is_alive():
            self._consolidation_thread.join(timeout=5)
            self._consolidation_thread = None

    # =========================================================================
    # Statistics (backward compatible)
    # =========================================================================

    def get_stats(self) -> Tuple[int, int, int]:
        """기존 API 호환: (hot, warm, cold) 통계."""
        return self._manager.get_stats()

    def get_cognitive_stats(self) -> dict:
        """5계층 전체 인지 기억 통계."""
        hot, warm, cold = self._manager.get_stats()
        ep_stats = self.episodic.get_stats()
        return {
            "stm_count": self.stm.get_count(),
            "mtm_count": self.mtm.get_count(),
            "ltm_hot": hot,
            "ltm_warm": warm,
            "ltm_cold": cold,
            "episodes": ep_stats,
        }

    def __repr__(self) -> str:
        return (
            f"MemoryCore(STM={self.stm.get_count()}, "
            f"MTM={self.mtm.get_count()}, "
            f"LTM={self.get_stats()})"
        )

