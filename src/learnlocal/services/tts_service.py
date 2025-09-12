"""
Text-to-Speech service with multiple engine support for educational content.
"""

import os
import tempfile
import uuid
from typing import Optional
import pyttsx3
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    from TTS.api import TTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

class TTSService:
    """Text-to-speech service with multiple engine support."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.temp_dir = tempfile.gettempdir()
        
        self.coqui_tts = None
        if COQUI_AVAILABLE:
            try:
                self.coqui_tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
            except Exception as e:
                pass
    
    async def generate_speech(self, text: str, voice_type: str = "default", speed: float = 1.0) -> str:
        """Generate speech from text and return the file path."""
        file_id = uuid.uuid4().hex[:8]
        output_file = os.path.join(self.temp_dir, f"speech_{file_id}.wav")
        
        if voice_type == "neural" and self.coqui_tts:
            await self._generate_with_coqui(text, output_file)
        elif voice_type == "online" and GTTS_AVAILABLE:
            await self._generate_with_gtts(text, output_file)
        else:
            await self._generate_with_pyttsx3(text, output_file, speed)
        
        return output_file
    
    async def _generate_with_pyttsx3(self, text: str, output_file: str, speed: float = 1.0):
        """Generate speech using pyttsx3 (offline)."""
        def _generate():
            engine = pyttsx3.init()
            
            engine.setProperty('rate', int(200 * speed))
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[0].id)
            
            engine.save_to_file(text, output_file)
            engine.runAndWait()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _generate)
    
    async def _generate_with_coqui(self, text: str, output_file: str):
        """Generate speech using Coqui TTS (neural, offline)."""
        def _generate():
            self.coqui_tts.tts_to_file(text=text, file_path=output_file)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _generate)
    
    async def _generate_with_gtts(self, text: str, output_file: str):
        """Generate speech using Google TTS (online)."""
        def _generate():
            tts = gTTS(text=text, lang='en')
            tts.save(output_file)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _generate)
    
    def get_available_engines(self) -> list:
        """Return list of available TTS engines."""
        engines = ["pyttsx3"]
        
        if COQUI_AVAILABLE and self.coqui_tts:
            engines.append("coqui")
        
        if GTTS_AVAILABLE:
            engines.append("gtts")
        
        return engines
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up old temporary audio files."""
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(self.temp_dir):
            if filename.startswith("speech_") and filename.endswith(".wav"):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass