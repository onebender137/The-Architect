import whisper
import torch
import os
import logging
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self, device="cpu"):
        self.device = device
        # Use base model for handheld efficiency
        self.model = whisper.load_model("base", device=self.device)
        logger.info(f"Whisper loaded on {self.device}")

    def transcribe(self, audio_path):
        """Transcribes an audio file locally on XPU/CPU."""
        try:
            # Handle potential OGG/Vorbis from Telegram
            if audio_path.endswith(".ogg"):
                wav_path = audio_path.replace(".ogg", ".wav")
                audio = AudioSegment.from_ogg(audio_path)
                audio.export(wav_path, format="wav")
                audio_path = wav_path

            result = self.model.transcribe(audio_path)
            return result["text"].strip()
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
        finally:
            # Cleanup temp wav
            if audio_path.endswith(".wav") and os.path.exists(audio_path):
                os.remove(audio_path)
