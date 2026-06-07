# -*- coding: utf-8 -*-
"""
💾 ARA AI Memory Core
Orchestrates storage and retrieval across the 3-tier memory (RAM, SQLite, JSON).
"""

from typing import List, Dict, Tuple
from backend.memory.long_memory import long_memory

class MemoryItem:
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


class MemoryCore:
    def __init__(self):
        self.manager = long_memory

    def store(self, item: MemoryItem) -> None:
        """Stores memory into the 3-tier system."""
        self.manager.store_wisdom(item.to_dict())

    def search(self, query: str) -> List[MemoryItem]:
        """Searches memory logs matching query."""
        results = self.manager.search_memory(query)
        return [MemoryItem.from_dict(r) for r in results]

    def get_stats(self) -> Tuple[int, int, int]:
        """Returns hot, warm, cold stats."""
        return self.manager.get_stats()
