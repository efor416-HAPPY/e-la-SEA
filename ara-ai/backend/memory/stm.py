# -*- coding: utf-8 -*-
"""
⚡ ARA AI Memory Subsystem: Short-Term Memory (STM)
Working memory for immediate conversational and task context.
TTL-based automatic decay with importance-weighted promotion to MTM.

Characteristics:
  - Capacity: ~20 items (configurable)
  - TTL: 30 seconds ~ 5 minutes
  - Access pattern: LRU with importance bias
  - Promotion: High-importance items survive decay → MTM
"""

import time
import threading
from collections import OrderedDict
from typing import Any, Optional


class STMItem:
    """단기기억 항목."""
    __slots__ = ['key', 'value', 'importance', 'created_at', 'last_accessed', 'access_count', 'ttl']

    def __init__(self, key: str, value: Any, importance: float = 0.5, ttl: float = 300.0):
        self.key = key
        self.value = value
        self.importance = max(0.0, min(1.0, importance))
        self.created_at = time.time()
        self.last_accessed = self.created_at
        self.access_count = 0
        self.ttl = ttl  # seconds

    def is_expired(self) -> bool:
        """TTL 만료 여부. 중요도가 높을수록 TTL이 연장됨."""
        effective_ttl = self.ttl * (1.0 + self.importance)  # 중요도 0.8 → TTL 1.8배
        return (time.time() - self.last_accessed) > effective_ttl

    def should_promote(self) -> bool:
        """MTM으로 승격해야 하는지 판단."""
        # 중요도 0.7 이상이고 2회 이상 접근된 기억은 승격 대상
        return self.importance >= 0.7 or self.access_count >= 3

    def touch(self) -> None:
        """접근 기록 갱신."""
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
            "ttl": self.ttl,
        }


class ShortTermMemory:
    """
    단기기억 (STM) — 작업 메모리.
    현재 대화/작업의 즉시 컨텍스트를 유지합니다.

    특징:
      - OrderedDict 기반 LRU 캐시
      - TTL 만료 시 자동 소멸 (importance 가중 연장)
      - 중요 항목은 decay 시 MTM으로 승격 후보로 반환
      - Thread-safe
    """

    def __init__(self, capacity: int = 20, default_ttl: float = 300.0):
        self._buffer: OrderedDict[str, STMItem] = OrderedDict()
        self._capacity = capacity
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._promotion_candidates: list[STMItem] = []

    def store(self, key: str, value: Any, importance: float = 0.5) -> None:
        """단기기억에 항목을 저장합니다."""
        with self._lock:
            if key in self._buffer:
                # 기존 항목 갱신
                item = self._buffer[key]
                item.value = value
                item.importance = max(item.importance, importance)
                item.touch()
                self._buffer.move_to_end(key)
            else:
                # 새 항목 추가
                item = STMItem(key=key, value=value, importance=importance, ttl=self._default_ttl)
                self._buffer[key] = item

                # 용량 초과 시 가장 오래된(덜 중요한) 항목 제거
                while len(self._buffer) > self._capacity:
                    evicted_key, evicted_item = self._buffer.popitem(last=False)
                    if evicted_item.should_promote():
                        self._promotion_candidates.append(evicted_item)

    def recall(self, key: str) -> Optional[Any]:
        """키로 단기기억을 검색합니다."""
        with self._lock:
            item = self._buffer.get(key)
            if item is None:
                return None
            if item.is_expired():
                del self._buffer[key]
                if item.should_promote():
                    self._promotion_candidates.append(item)
                return None
            item.touch()
            self._buffer.move_to_end(key)
            return item.value

    def search(self, query: str) -> list[dict]:
        """키워드로 단기기억을 검색합니다."""
        results = []
        query_lower = query.lower()
        with self._lock:
            for key, item in self._buffer.items():
                if item.is_expired():
                    continue
                value_str = str(item.value).lower()
                if query_lower in key.lower() or query_lower in value_str:
                    item.touch()
                    results.append(item.to_dict())
        return results

    def get_active_context(self) -> list[dict]:
        """현재 활성화된 모든 단기기억을 반환합니다."""
        with self._lock:
            return [item.to_dict() for item in self._buffer.values() if not item.is_expired()]

    def decay(self) -> list[STMItem]:
        """
        TTL 만료 항목을 정리하고, MTM 승격 후보를 반환합니다.
        커널이 주기적으로 호출합니다.
        """
        promoted = []
        with self._lock:
            expired_keys = []
            for key, item in self._buffer.items():
                if item.is_expired():
                    expired_keys.append(key)
                    if item.should_promote():
                        promoted.append(item)

            for key in expired_keys:
                del self._buffer[key]

            # 승격 대기열에서도 수집
            promoted.extend(self._promotion_candidates)
            self._promotion_candidates.clear()

        return promoted

    def get_count(self) -> int:
        """현재 단기기억 항목 수."""
        with self._lock:
            return len(self._buffer)

    def clear(self) -> None:
        """단기기억을 모두 비웁니다."""
        with self._lock:
            self._buffer.clear()
            self._promotion_candidates.clear()

    def __repr__(self) -> str:
        return f"ShortTermMemory(items={self.get_count()}, capacity={self._capacity})"
