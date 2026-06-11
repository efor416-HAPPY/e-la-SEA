# -*- coding: utf-8 -*-
"""
🎤 ARA AI Cognitive Agent: Voice Agent (ARA 3.0)
Handles voice input (STT) and output (TTS) as perception/action Thoughts.
"""

from backend.agents.base_cognitive_agent import ICognitiveAgent
from backend.kernel.message import Thought
from typing import Optional


class VoiceCognitiveAgent(ICognitiveAgent):
    """음성 입출력 인지 에이전트."""

    def __init__(self):
        super().__init__()

    def id(self) -> str:
        return "voice"

    def subscribed_topics(self) -> list[str]:
        return ["reasoning", "dialogue"]  # 추론/대화 결과를 받아서 TTS로 출력

    def initialize(self) -> bool:
        print("🎤 [VoiceAgent] 음성 인지 에이전트 초기화 완료.")
        return True

    def on_thought(self, thought: Thought) -> Optional[Thought]:
        """추론/대화 결과를 받으면 TTS로 음성 출력합니다."""
        if thought.context.get("needs_voice", False):
            text = thought.content
            success = self._speak(text)
            if success:
                return thought.derive(
                    source=self.id(),
                    thought_type="action",
                    content=f"음성 출력 완료: {text[:30]}",
                    importance=0.3,
                )
        return None

    def perceive_voice(self, audio_path: str) -> Optional[Thought]:
        """음성 입력을 텍스트로 변환하고 dialogue Thought로 발행합니다."""
        text = self._listen(audio_path)
        if text:
            thought = Thought(
                source=self.id(),
                thought_type="dialogue",
                content=text,
                importance=0.7,
                context={"input_type": "voice", "audio_path": audio_path},
            )
            self.emit(thought)
            return thought
        return None

    def _speak(self, text: str) -> bool:
        """TTS 출력."""
        try:
            from backend.voice.tts import tts_engine
            return tts_engine.synthesize(text)
        except Exception as e:
            print(f"⚠️ [VoiceAgent] TTS 오류: {e}")
            return False

    def _listen(self, audio_path: str) -> str:
        """STT 입력."""
        try:
            from backend.voice.stt import stt_engine
            return stt_engine.transcribe(audio_path)
        except Exception as e:
            print(f"⚠️ [VoiceAgent] STT 오류: {e}")
            return ""

    def shutdown(self) -> None:
        print("🎤 [VoiceAgent] 종료.")


# Global instance
voice_cognitive_agent = VoiceCognitiveAgent()
