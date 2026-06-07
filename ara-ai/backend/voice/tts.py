# -*- coding: utf-8 -*-
"""
🔊 ARA AI Voice Subsystem: TTS (Text-to-Speech)
Handles speech synthesis using OpenAI TTS or local system/mock fallbacks.
"""

import os
from openai import OpenAI

class TextToSpeechSynthesizer:
    """Generates audio speech output from raw text strings."""
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    def synthesize(self, text: str, output_path: str = "downloads/output.mp3") -> bool:
        """Synthesizes text into an audio file (MP3/WAV)."""
        if not text:
            return False

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if self.api_key:
            try:
                client = OpenAI(api_key=self.api_key)
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=text
                )
                response.stream_to_file(output_path)
                return True
            except Exception as e:
                print(f"❌ OpenAI TTS synthesis failed: {e}")
                # Fall through to local fallback

        # Simple Local Mock Fallback: print to console or system beep
        print(f"🔊 [TTS Fallback] Speaking: '{text}' (saved as placeholder to {output_path})")
        
        # Write a tiny dummy mp3 header or text placeholder
        try:
            with open(output_path, 'wb') as f:
                f.write(b"MOCK_MP3_DATA_FOR_" + text.encode('utf-8'))
            return True
        except Exception:
            return False

# Global TTS engine
tts_engine = TextToSpeechSynthesizer()
