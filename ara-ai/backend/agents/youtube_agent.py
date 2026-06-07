# -*- coding: utf-8 -*-
"""
🎥 ARA AI Agent Layer: YouTube Agent
Orchestrates YouTube RSS scraping, filters content, and indexes videos.
"""

import time
from backend.news.youtube_collector import YouTubeCollector
from backend.security.safety_gate import SafetyGate
from backend.memory.long_memory import long_memory
from backend.memory.vector_memory import VectorMemory

class YouTubeAgent:
    """Monitors YouTube video uploads, filters spam, and archives them."""
    def __init__(self, channel_id="UC18xqS40OGGyPVI-4sneOEA"):
        self.collector = YouTubeCollector(channel_id)
        self.safety_gate = SafetyGate()

    def run_video_ingestion(self) -> int:
        """Runs YouTube updates, screens content safety, and saves to 3-tier memory."""
        print(f"📡 [YouTubeAgent] 유튜브 채널 피드 대기열 갱신 중 -> Channel: {self.collector.channel_id}")
        videos = self.collector.collect_videos(max_items=3)
        saved_count = 0
        
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')

        for video in videos:
            # Check safety
            text_to_check = f"{video['title']} {video['description']}"
            is_safe, reason = self.safety_gate.check_text_safety(text_to_check)
            if not is_safe:
                print(f"⚠️ [YouTubeAgent] Safety Violation: {reason}")
                continue

            # Standardize
            knowledge_packet = {
                "title": video["title"],
                "link": video["link"],
                "description": f"[YOUTUBE] {video['description']}",
                "source": "Ara YouTube Collector",
                "scraped_at": now_str,
                "embedded_vector": str(VectorMemory.generate_mock_vector(video["title"]))
            }

            # Save in long memory
            long_memory.store_wisdom(knowledge_packet)
            saved_count += 1
            
        print(f"✅ [YouTubeAgent] Ingestion Complete. {saved_count} videos archived.")
        return saved_count

# Global YouTube Agent
youtube_agent = YouTubeAgent()
