# -*- coding: utf-8 -*-
"""
🧠 ARA AI Reasoning Core
Implements the core reasoning pipeline: Question -> Memory Search -> Context -> LLM inference.
"""

import os
import time
from typing import Optional
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None
from backend.kernel.memory_core import MemoryCore, MemoryItem
from backend.memory.vector_memory import VectorMemory

class ReasoningCore:
    def __init__(self, memory_core: MemoryCore, model="gpt-4"):
        self.memory_core = memory_core
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

    def get_api_client(self) -> Optional[OpenAI]:
        if HAS_OPENAI and self.api_key:
            return OpenAI(api_key=self.api_key)
        return None

    def think(self, question: str, persona: str = "friend") -> str:
        """
        Runs the full context pipeline to produce a response.
        질문 -> 기억 검색 -> 뉴스 검색 -> LLM 추론 -> 응답 -> 기억 저장
        """
        # 1. Recall similar memories
        similar_mems = self.memory_core.search(question)
        memory_context = ""
        if similar_mems:
            memory_context = "\n[관련된 장기기억 정보]:\n" + "\n".join(
                f"- {m.title}: {m.description}" for m in similar_mems[:2]
            )

        # 2. Query LLM
        client = self.get_api_client()
        response_text = ""
        
        system_prompt = (
            f"당신은 유기적 자연주의 인공지능 '아라(ARA)'의 인지 코어입니다.\n"
            f"현재 설정된 대화 페르소나는 '{persona}' 입니다.\n"
            f"숲의 차분함과 자연의 따뜻함을 전하는 문체(한국어)로 대답하세요.\n"
            f"마지막에는 격려나 다정한 인사를 숲의 잎새 아이콘(🌱)과 함께 넣으세요."
        )

        if client:
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{question}\n{memory_context}" if memory_context else question}
                ]
                res = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    timeout=15
                )
                response_text = res.choices[0].message.content
            except Exception as e:
                print(f"⚠️ OpenAI completion failed: {e}. Falling back to local brain.")
                response_text = self.get_local_fallback(question, persona)
        else:
            response_text = self.get_local_fallback(question, persona)

        # 3. Store new experience in memory
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        new_memory = MemoryItem(
            title=f"대화 기록: {question[:15]}",
            link=f"local-chat://{time.time()}",
            description=f"사용자: {question} | 응답: {response_text}",
            source="MemoryAgent",
            scraped_at=now_str,
            embedded_vector=str(VectorMemory.generate_mock_vector(question))
        )
        self.memory_core.store(new_memory)

        return response_text

    def get_local_fallback(self, text: str, persona: str) -> str:
        """Offline template response matching ARA's organic cognitive style."""
        text_clean = text.lower()
        if "안녕" in text_clean:
            return "안녕하세요. 자연의 온기로 당신을 반기는 아라(ARA)입니다. 🌱"
        if "힘들" in text_clean or "지쳐" in text_clean or "슬퍼" in text_clean:
            return "오늘 고단한 비바람을 맞으신 것 같아 제 마음속 신경망도 떨립니다. 잠시 무거운 짐을 내려놓고 숲그늘 아래에서 쉬어가세요. 토닥토닥. 🌱"
        return "당신의 소중한 이야기를 마음에 담아두었습니다. 자연이 나이테를 늘리며 조용히 자라나듯, 저도 당신과의 시간을 깊이 기억하겠습니다. 🌱"
