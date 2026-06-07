# -*- coding: utf-8 -*-
"""
📈 ARA AI Agent Layer: Economy Agent
Monitors macroeconomic data (KOSPI, exchange rate) and dispatches updates via the AgentBus.
"""

import time
from backend.agents.base_agent import IAgent
from backend.kernel.message import Message
from backend.kernel.memory_core import MemoryItem
from backend.news.economic_collector import EconomicCollector


class EconomyAgent(IAgent):
    def __init__(self):
        self.collector = EconomicCollector()
        self.running = False
        self.kernel = None
        self.bus = None

    def id(self) -> str:
        return "economy"

    def initialize(self) -> bool:
        self.running = True
        return True

    def process(self, message: Message) -> bool:
        """Processes economic data collection requests received via the AgentBus."""
        if message.action == "collect":
            if not self.kernel:
                return False
            try:
                # Retrieve indicators
                indicators = self.collector.collect_indicators()
                now_str = time.strftime('%Y-%m-%d %H:%M:%S')

                text_to_check = f"KOSPI: {indicators['kospi']} Exchange Rate: {indicators['us_krw_exchange_rate']}"
                is_safe, reason = self.kernel.security_core.check_safety(text_to_check)
                if not is_safe:
                    print(f"⚠️ [EconomyAgent] Safety Violation: {reason}")
                    return False

                # Store in MemoryCore
                from backend.memory.vector_memory import VectorMemory
                memory_item = MemoryItem(
                    title="거시경제 실시간 지표",
                    link=f"local-economy://{time.time()}",
                    description=f"[ECONOMY] 환율: {indicators['us_krw_exchange_rate']}원, 코스피: {indicators['kospi']} ({indicators['kospi_change']}), 한국기준금리: {indicators['interest_rate_kr']}%",
                    source="Ara Economy Collector",
                    scraped_at=now_str,
                    embedded_vector=str(VectorMemory.generate_mock_vector("거시경제 실시간 지표"))
                )
                self.kernel.memory_core.store(memory_item)
                print("✅ [EconomyAgent] Ingested latest macroeconomic metrics.")
                return True
            except Exception as e:
                print(f"❌ [EconomyAgent] Ingestion failed: {e}")
                return False
        return False

    def shutdown(self) -> None:
        self.running = False

    def start_loop(self) -> None:
        """Asynchronous periodic collection loop."""
        print("📈 [EconomyAgent] Periodic collection loop started.")
        while self.running:
            if self.kernel:
                # Dispatch collection action to self via the central AgentBus
                msg = Message(source="kernel", target="economy", action="collect", payload={})
                self.kernel.bus.dispatch(msg)
            
            # Non-blocking sleep for graceful shutdowns
            for _ in range(60):
                if not self.running:
                    break
                time.sleep(1.0)


# Global Economy Agent Instance
economy_agent = EconomyAgent()
