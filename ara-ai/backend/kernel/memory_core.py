# -*- coding: utf-8 -*-
"""
💾 ARA AI Memory Core (Systematic Object-Oriented memory)
Defines structured MemoryItem representations, DialogueMemoryItem subclasses,
and encapsulates database and JSON storage access in an isolated, thread-safe model.
"""

import time
from typing import List, Tuple
from backend.memory.long_memory import long_memory
from backend.memory.vector_memory import VectorMemory


class MemoryItem:
    """Base structured item representing gathered knowledge/intelligence."""
    def __init__(self, title: str, link: str, description: str, source: str, scraped_at: str, embedded_vector: str = "[]"):
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
    """Dialogue-specific Memory Item capturing conversation context systematically."""
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


class MemoryCore:
    """
    Object-oriented facade encapsulating Hot RAM, SQLite DB, and Cold JSON storage.
    Guarantees thread safety and isolates database mutations from other domains.
    """
    def __init__(self):
        # Wraps the local manager safely
        self._manager = long_memory

    def store(self, item: MemoryItem) -> None:
        """Stores any structured MemoryItem across the 3-tier system."""
        self._manager.store_wisdom(item.to_dict())

    def search(self, query: str) -> List[MemoryItem]:
        """Searches indexed memories matching the search string."""
        results = self._manager.search_memory(query)
        return [MemoryItem.from_dict(r) for r in results]

    def get_stats(self) -> Tuple[int, int, int]:
        """Gathers metrics from Hot Cache, Warm DB, and Cold File storage."""
        return self._manager.get_stats()
