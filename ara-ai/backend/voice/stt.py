# -*- coding: utf-8 -*-
"""
🎙️ ARA AI Voice Subsystem: STT (Speech-to-Text)
Implements language detection and audio transcription utilizing speech_recognition and langdetect.
"""

import os
import tempfile

try:
    from langdetect import detect
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

class SpeechToTextTranscriber:
    """Manages audio capture, speech recognition, and language detection."""
    def __init__(self):
        self.recognizer = sr.Recognizer() if HAS_SR else None

    def detect_language(self, text: str) -> str:
        """Detects the language of a transcribed text using langdetect."""
        if not text:
            return "ko"  # default
        
        if HAS_LANGDETECT:
            try:
                return detect(text)
            except Exception:
                pass
        
        # Simple fallback based on character ranges
        has_korean = any(0xAC00 <= ord(char) <= 0xD7A3 for char in text)
        return "ko" if has_korean else "en"

    def transcribe_file(self, audio_file_path: str) -> tuple[str, str]:
        """Transcribes a given local audio WAV file."""
        if not HAS_SR or not self.recognizer:
            return "오류: speech_recognition 라이브러리가 로드되지 않았습니다.", "ko"

        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
            # Try Google Web Speech API (free, no key required)
            text = self.recognizer.recognize_google(audio, language="ko-KR")
            lang = self.detect_language(text)
            return text, lang
        except sr.UnknownValueError:
            return "오류: 음성을 인식하지 못했습니다.", "ko"
        except sr.RequestError as e:
            return f"오류: Google STT 서비스 요청 실패: {e}", "ko"
        except Exception as e:
            return f"오류: 음성 파일 처리 중 에러 발생: {e}", "ko"

    def listen_and_transcribe_live(self, timeout=5, phrase_time_limit=20) -> tuple[str, str]:
        """Listens from the microphone source and transcribes (runs synchronously/blocking)."""
        if not HAS_SR or not self.recognizer:
            return "오류: 마이크 및 STT 라이브러리가 비활성화 상태입니다.", "ko"

        try:
            with sr.Microphone() as source:
                print(f"🎤 [Mic listening] (timeout: {timeout}s, limit: {phrase_time_limit}s)...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
            text = self.recognizer.recognize_google(audio, language="ko-KR")
            lang = self.detect_language(text)
            return text, lang
        except Exception as e:
            return f"오류: 실시간 음성 인식 실패: {e}", "ko"

# Global transcriber instance
stt_engine = SpeechToTextTranscriber()
