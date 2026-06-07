# -*- coding: utf-8 -*-
"""
📰 ARA AI Agent Layer: News Agent
Coordinates news aggregation, safety validation, and long term indexing of scraped articles.
"""

import time
from backend.news.rss_collector import RSSCollector
from backend.security.safety_gate import SafetyGate
from backend.memory.long_memory import long_memory
from backend.memory.vector_memory import VectorMemory

class NewsAgent:
    """Scrapes academic/intellectual news, filters, and indexes them."""
    def __init__(self, default_feed="https://www.openculture.com/feed"):
        self.collector = RSSCollector(default_feed)
        self.safety_gate = SafetyGate()

    def run_news_ingestion(self) -> int:
        """Runs news scraping, validates safety, and saves to 3-tier memory."""
        print("📰 [NewsAgent] 학술 뉴스 피드 대기열 갱신 중...")
        items = self.collector.collect_items(max_items=3)
        saved_count = 0
        
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')

        for item in items:
            # Check SafetyGate
            text_to_check = f"{item['title']} {item['description']}"
            is_safe, reason = self.safety_gate.check_text_safety(text_to_check)
            if not is_safe:
                print(f"⚠️ [NewsAgent] Safety Violation: {reason}")
                continue

            # Standardize item packet
            knowledge_packet = {
                "title": item["title"],
                "link": item["link"],
                "description": f"[NEWS] {item['description']}",
                "source": "Ara News Collector",
                "scraped_at": now_str,
                "embedded_vector": str(VectorMemory.generate_mock_vector(item["title"]))
            }

            # Store in long memory
            long_memory.store_wisdom(knowledge_packet)
            saved_count += 1
            
        print(f"✅ [NewsAgent] Ingestion Complete. {saved_count} new entries archived.")
        return saved_count

# Global News Agent
news_agent = NewsAgent()
