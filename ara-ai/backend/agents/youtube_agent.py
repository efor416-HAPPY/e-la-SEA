# -*- coding: utf-8 -*-
"""
🎥 ARA AI Agent Layer: YouTube Agent
Performs YouTube video RSS metadata monitoring and processes messages via the AgentBus.
"""

import time
from backend.agents.base_agent import IAgent
from backend.kernel.message import Message
from backend.kernel.memory_core import MemoryItem


class YouTubeAgent(IAgent):
    def __init__(self, channel_id="UC18xqS40OGGyPVI-4sneOEA"):
        self.channel_id = channel_id
        self.running = False
        self.kernel = None
        self.bus = None

    def id(self) -> str:
        return "youtube"

    def initialize(self) -> bool:
        self.running = True
        return True

    def process(self, message: Message) -> bool:
        """Processes YouTube collection requests received via the AgentBus."""
        if message.action == "collect":
            if not self.kernel:
                return False
            try:
                # Retrieve youtube video items via KnowledgeCore
                videos = self.kernel.knowledge_core.ingest_youtube()
                saved_count = 0
                now_str = time.strftime('%Y-%m-%d %H:%M:%S')

                for video in videos:
                    # Validate safety via SecurityCore
                    text_to_check = f"{video['title']} {video['description']}"
                    is_safe, reason = self.kernel.security_core.check_safety(text_to_check)
                    if not is_safe:
                        print(f"⚠️ [YouTubeAgent] Safety Violation: {reason}")
                        continue

                    # Store in MemoryCore
                    from backend.memory.vector_memory import VectorMemory
                    memory_item = MemoryItem(
                        title=video["title"],
                        link=video["link"],
                        description=f"[YOUTUBE] {video['description']}",
                        source="Ara YouTube Collector",
                        scraped_at=now_str,
                        embedded_vector=str(VectorMemory.generate_mock_vector(video["title"]))
                    )
                    self.kernel.memory_core.store(memory_item)
                    saved_count += 1
                
                print(f"✅ [YouTubeAgent] Ingested {saved_count} videos.")
                return True
            except Exception as e:
                print(f"❌ [YouTubeAgent] Ingestion failed: {e}")
                return False
        return False

    def shutdown(self) -> None:
        self.running = False

    def start_loop(self) -> None:
        """Asynchronous periodic collection loop."""
        print("🎥 [YouTubeAgent] Periodic collection loop started.")
        while self.running:
            if self.kernel:
                # Dispatch collection action to self via the central AgentBus
                msg = Message(source="kernel", target="youtube", action="collect", payload={})
                self.kernel.bus.dispatch(msg)
            
            # Non-blocking sleep for graceful shutdowns
            for _ in range(60):
                if not self.running:
                    break
                time.sleep(1.0)


# Global YouTube Agent Instance
youtube_agent = YouTubeAgent()
