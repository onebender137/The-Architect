import whisper
import torch
import os
import logging
import gc
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self, device="cpu"):
        self.device = device
        # Lazy loading: model is not loaded in __init__ to save memory
        self.model = None
        logger.info(f"VoiceProcessor initialized on {self.device} (Lazy Load)")

    def transcribe(self, audio_path):
        """Transcribes an audio file locally on XPU/CPU, then unloads the model."""
        model = None
        try:
            # Load model into a local variable for thread safety
            logger.info(f"Loading Whisper 'base' model on {self.device}...")
            model = whisper.load_model("base", device=self.device)

            # Handle potential OGG/Vorbis from Telegram
            if audio_path.endswith(".ogg"):
                wav_path = audio_path.replace(".ogg", ".wav")
                audio = AudioSegment.from_ogg(audio_path)
                audio.export(wav_path, format="wav")
                audio_path = wav_path

            result = model.transcribe(audio_path)
            return result["text"].strip()
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
        finally:
            # Unload local model to free memory
            if model is not None:
                logger.info("Unloading Whisper model...")
                del model
                gc.collect()
                if self.device == "xpu":
                    try:
                        import torch.xpu
                        if torch.xpu.is_available():
                            torch.xpu.empty_cache()
                    except (ImportError, AttributeError):
                        pass

            # Cleanup temp wav
            if audio_path.endswith(".wav") and os.path.exists(audio_path):
                os.remove(audio_path)
