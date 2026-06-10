# -*- coding: utf-8 -*-
"""
🧠 ARA AI Memory Subsystem: Medium-Term Memory (MTM)
Session-level memory for intermediate consolidation between STM and LTM.

Characteristics:
  - Capacity: ~200 items
  - TTL: 1 hour ~ 24 hours
  - Access-frequency weighted consolidation to LTM
  - Bridges the gap between fleeting STM and persistent LTM
"""

import time
import threading
from typing import Any, Optional


class MTMItem:
    """중기기억 항목."""
    __slots__ = ['key', 'value', 'importance', 'created_at', 'last_accessed',
                 'access_count', 'source', 'tags', 'ttl']

    def __init__(self, key: str, value: Any, importance: float = 0.5,
                 source: str = "", tags: list = None, ttl: float = 3600.0):
        self.key = key
        self.value = value
        self.importance = max(0.0, min(1.0, importance))
        self.created_at = time.time()
        self.last_accessed = self.created_at
        self.access_count = 1
        self.source = source
        self.tags = tags or []
        self.ttl = ttl  # default: 1 hour

    def is_expired(self) -> bool:
        """TTL 만료 여부. 접근 빈도가 높을수록 연장."""
        access_bonus = min(self.access_count * 0.2, 2.0)  # 최대 2배 연장
        effective_ttl = self.ttl * (1.0 + access_bonus)
        return (time.time() - self.last_accessed) > effective_ttl

    def should_consolidate(self) -> bool:
        """LTM으로 통합(영구 저장)해야 하는지 판단."""
        # 5회 이상 접근되었거나, 중요도 0.8 이상이면 LTM 대상
        return self.access_count >= 5 or self.importance >= 0.8

    def touch(self) -> None:
        self.last_accessed = time.time()
        self.access_count += 1

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "importance": self.importance,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "source": self.source,
            "tags": self.tags,
        }


class MediumTermMemory:
    """
    중기기억 (MTM) — 세션 메모리.
    STM에서 승격된 기억을 보관하고, 충분히 강화된 기억은 LTM으로 통합합니다.

    인지 기억 통합 흐름:
        STM (30s~5m) → MTM (1h~24h) → LTM (영구)
    """

    def __init__(self, capacity: int = 200, default_ttl: float = 3600.0):
        self._memories: dict[str, MTMItem] = {}
        self._capacity = capacity
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def promote_from_stm(self, key: str, value: Any, importance: float = 0.5,
                         source: str = "", tags: list = None) -> None:
        """STM에서 승격된 기억을 저장합니다."""
        with self._lock:
            if key in self._memories:
                item = self._memories[key]
                item.value = value
                item.importance = max(item.importance, importance)
                item.touch()
            else:
                item = MTMItem(key=key, value=value, importance=importance,
                               source=source, tags=tags, ttl=self._default_ttl)
                self._memories[key] = item

                # 용량 초과 시 가장 오래된 항목 제거
                if len(self._memories) > self._capacity:
                    self._evict_least_important()

    def store(self, key: str, value: Any, importance: float = 0.5,
              source: str = "", tags: list = None) -> None:
        """직접 중기기억에 저장합니다."""
        self.promote_from_stm(key, value, importance, source, tags)

    def recall(self, key: str) -> Optional[Any]:
        """키로 중기기억을 검색합니다."""
        with self._lock:
            item = self._memories.get(key)
            if item is None:
                return None
            if item.is_expired():
                del self._memories[key]
                return None
            item.touch()
            return item.value

    def search(self, query: str) -> list[dict]:
        """키워드로 중기기억을 검색합니다."""
        results = []
        query_lower = query.lower()
        with self._lock:
            for key, item in self._memories.items():
                if item.is_expired():
                    continue
                value_str = str(item.value).lower()
                if query_lower in key.lower() or query_lower in value_str:
                    item.touch()
                    results.append(item.to_dict())
        return results

    def consolidate_to_ltm(self) -> list[MTMItem]:
        """
        LTM으로 통합해야 할 기억을 반환하고 MTM에서 제거합니다.
        커널이 주기적으로 호출합니다.
        """
        to_consolidate = []
        with self._lock:
            expired_keys = []
            consolidate_keys = []

            for key, item in self._memories.items():
                if item.is_expired():
                    expired_keys.append(key)
                elif item.should_consolidate():
                    consolidate_keys.append(key)
                    to_consolidate.append(item)

            for key in expired_keys:
                del self._memories[key]
            for key in consolidate_keys:
                del self._memories[key]

        return to_consolidate

    def _evict_least_important(self) -> None:
        """가장 덜 중요한 항목을 제거합니다 (lock 보유 상태에서 호출)."""
        if not self._memories:
            return
        # importance가 가장 낮고, 접근 빈도가 낮은 항목을 제거
        worst_key = min(
            self._memories,
            key=lambda k: (self._memories[k].importance, self._memories[k].access_count)
        )
        del self._memories[worst_key]

    def get_count(self) -> int:
        with self._lock:
            return len(self._memories)

    def get_all(self) -> list[dict]:
        with self._lock:
            return [item.to_dict() for item in self._memories.values() if not item.is_expired()]

    def clear(self) -> None:
        with self._lock:
            self._memories.clear()

    def __repr__(self) -> str:
        return f"MediumTermMemory(items={self.get_count()}, capacity={self._capacity})"
