# -*- coding: utf-8 -*-
"""
💾 ARA AI Agent Layer: Memory Agent
Exposes memory operations (remember, recall) via the AgentBus.
"""

import time
from backend.agents.base_agent import IAgent
from backend.kernel.message import Message
from backend.kernel.memory_core import MemoryItem
from backend.memory.vector_memory import VectorMemory


class MemoryAgent(IAgent):
    def __init__(self):
        self.kernel = None
        self.bus = None

    def id(self) -> str:
        return "memory"

    def initialize(self) -> bool:
        return True

    def process(self, message: Message) -> bool:
        """Handles memory-related messages: 'remember' and 'recall'."""
        if message.action == "remember":
            info = message.payload.get("info", "")
            return self.remember(info)
        elif message.action == "recall":
            query = message.payload.get("query", "")
            if isinstance(message.payload, dict):
                message.payload["result"] = self.recall(query)
            return True
        return False

    def shutdown(self) -> None:
        pass

    def remember(self, info: str) -> bool:
        """Stores a custom intelligence statement into the memory core."""
        if not self.kernel:
            return False
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        item = MemoryItem(
            title=f"기억된 지식: {info[:15]}",
            link=f"local-memo://{time.time()}",
            description=info,
            source="MemoryAgent",
            scraped_at=now_str,
            embedded_vector=str(VectorMemory.generate_mock_vector(info))
        )
        self.kernel.memory_core.store(item)
        return True

    def recall(self, query: str) -> str:
        """Recalls the most relevant description matching the query."""
        if not self.kernel:
            return ""
        items = self.kernel.memory_core.search(query)
        if not items:
            return ""
        return items[0].description


# Global Memory Agent Instance
memory_agent = MemoryAgent()
