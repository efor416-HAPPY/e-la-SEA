# -*- coding: utf-8 -*-
"""
📰 ARA AI Agent Layer: News Agent
Performs news RSS ingestion and processes messages via the AgentBus.
"""

import time
from backend.agents.base_agent import IAgent
from backend.kernel.message import Message
from backend.kernel.memory_core import MemoryItem


class NewsAgent(IAgent):
    def __init__(self, default_feed="https://www.openculture.com/feed"):
        self.default_feed = default_feed
        self.running = False
        self.kernel = None
        self.bus = None

    def id(self) -> str:
        return "news"

    def initialize(self) -> bool:
        self.running = True
        return True

    def process(self, message: Message) -> bool:
        """Processes news collection requests received via the AgentBus."""
        if message.action == "collect":
            if not self.kernel:
                return False
            try:
                # Retrieve news items via KnowledgeCore
                items = self.kernel.knowledge_core.ingest_news()
                saved_count = 0
                now_str = time.strftime('%Y-%m-%d %H:%M:%S')

                for item in items:
                    # Validate safety via SecurityCore
                    text_to_check = f"{item['title']} {item['description']}"
                    is_safe, reason = self.kernel.security_core.check_safety(text_to_check)
                    if not is_safe:
                        print(f"⚠️ [NewsAgent] Safety Violation: {reason}")
                        continue

                    # Store in MemoryCore
                    from backend.memory.vector_memory import VectorMemory
                    memory_item = MemoryItem(
                        title=item["title"],
                        link=item["link"],
                        description=f"[NEWS] {item['description']}",
                        source="Ara News Collector",
                        scraped_at=now_str,
                        embedded_vector=str(VectorMemory.generate_mock_vector(item["title"]))
                    )
                    self.kernel.memory_core.store(memory_item)
                    saved_count += 1
                
                print(f"✅ [NewsAgent] Ingested {saved_count} news articles.")
                return True
            except Exception as e:
                print(f"❌ [NewsAgent] Ingestion failed: {e}")
                return False
        return False

    def shutdown(self) -> None:
        self.running = False

    def start_loop(self) -> None:
        """Asynchronous periodic collection loop."""
        print("📰 [NewsAgent] Periodic collection loop started.")
        while self.running:
            if self.kernel:
                # Dispatch collection action to self via the central AgentBus
                msg = Message(source="kernel", target="news", action="collect", payload={})
                self.kernel.bus.dispatch(msg)
            
            # Non-blocking sleep for graceful shutdowns
            for _ in range(60):
                if not self.running:
                    break
                time.sleep(1.0)


# Global News Agent Instance
news_agent = NewsAgent()
