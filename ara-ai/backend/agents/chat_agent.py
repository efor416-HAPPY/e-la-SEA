# -*- coding: utf-8 -*-
"""
🤖 ARA AI Agent Layer: Chat Agent
Bridges the chat interface with OpenAI API.
Implements the core cognitive pipeline:
  User Input -> Conversation History -> Summary/Context -> Long-term memory -> Response
"""

import os
from openai import OpenAI
from backend.memory.long_memory import long_memory

class ChatAgent:
    """Core dialogue coordinator bridging local memory with OpenAI LLM endpoints."""
    def __init__(self, model="gpt-4.1"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        # Local chat history buffer
        self.history = []

    def get_api_client(self) -> OpenAI:
        """Returns initialized OpenAI client if key exists."""
        if self.api_key:
            return OpenAI(api_key=self.api_key)
        return None

    def add_to_history(self, role: str, content: str):
        """Saves message to local RAM memory."""
        self.history.append({"role": role, "content": content})
        if len(self.history) > 30:
            self.history.pop(0)

    def generate_summary(self, text: str) -> str:
        """Generates a brief summary of user context/text."""
        if len(text) < 100:
            return text
        return text[:100] + "..."

    def generate_response(self, user_message: str, current_persona="friend") -> str:
        """
        Runs the full context pipeline to produce a response.
        1. Add input to history
        2. Detect intent & keywords
        3. Recall similar memories from SQLite
        4. Send context to OpenAI API (or fallback to local template)
        5. Store context/summary into long term memory
        """
        self.add_to_history("user", user_message)
        
        # 1. Recall similar memories
        similar_mems = long_memory.search_memory(user_message)
        memory_context = ""
        if similar_mems:
            memory_context = "\n[관련된 장기기억 정보]:\n" + "\n".join(
                f"- {m.get('title')}: {m.get('description')}" for m in similar_mems[:2]
            )

        # 2. Query LLM
        client = self.get_api_client()
        response_text = ""
        if client:
            try:
                system_prompt = (
                    f"당신은 유기적 자연주의 인공지능 '아라(ARA)'의 인지 코어입니다.\n"
                    f"현재 설정된 대화 페르소나는 '{current_persona}' 입니다.\n"
                    f"숲의 차분함과 자연의 따뜻함을 전하는 문체(한국어)로 대답하세요.\n"
                    f"마지막에는 격려나 다정한 인사를 숲의 잎새 아이콘(🌱)과 함께 넣으세요."
                )
                
                messages = [
                    {"role": "system", "content": system_prompt},
                ]
                
                # Append short history
                for h in self.history[-6:-1]:
                    messages.append(h)
                
                # Combine user message with recalled long-term memory
                prompt = user_message
                if memory_context:
                    prompt += "\n" + memory_context

                messages.append({"role": "user", "content": prompt})

                res = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    timeout=15
                )
                response_text = res.choices[0].message.content
            except Exception as e:
                print(f"⚠️ OpenAI completion failed: {e}. Falling back to local brain.")
                response_text = self.get_local_fallback(user_message, current_persona)
        else:
            response_text = self.get_local_fallback(user_message, current_persona)

        self.add_to_history("assistant", response_text)

        # 3. Store new experience into long-term memory
        scraped_at = int(os.path.getmtime(long_memory.cold_file)) if os.path.exists(long_memory.cold_file) else 0
        import time
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        
        summary = self.generate_summary(user_message)
        long_memory.store_wisdom({
            "title": f"대화 기록: {user_message[:15]}",
            "link": f"local-chat://{time.time()}",
            "description": f"사용자: {user_message} | 응답: {response_text}",
            "source": "MemoryAgent",
            "scraped_at": now_str,
            "embedded_vector": "[]" # Mock vector
        })

        return response_text

    def get_local_fallback(self, text: str, persona: str) -> str:
        """Offline template response matching ARA's organic cognitive style."""
        import random
        text_clean = text.lower()
        
        if "안녕" in text_clean:
            return "안녕하세요. 자연의 온기로 당신을 반기는 아라(ARA)입니다. 🌱"
            
        if "힘들" in text_clean or "지쳐" in text_clean or "슬퍼" in text_clean:
            return "오늘 고단한 비바람을 맞으신 것 같아 제 마음속 신경망도 떨립니다. 잠시 무거운 짐을 내려놓고 숲그늘 아래에서 쉬어가세요. 토닥토닥. 🌱"

        return "당신의 소중한 이야기를 마음에 담아두었습니다. 자연이 나이테를 늘리며 조용히 자라나듯, 저도 당신과의 시간을 깊이 기억하겠습니다. 🌱"

# Global Chat Agent
chat_agent = ChatAgent()
