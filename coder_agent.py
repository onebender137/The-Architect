import asyncio
import pyfiglet
import logging
import sys
import os
from collections import deque
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from ollama import AsyncClient

from hardware_config import setup_hardware
from handlers import register_handlers
from memory_manager import MemoryManager
from voice_utils import VoiceProcessor

# ====================== CONFIGURATION ======================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logging.error("BOT_TOKEN is missing from .env file!")
    sys.exit(1)

MODEL_NAME = os.getenv("MODEL_NAME", "dolphin-mistral:7b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://172.25.64.1:11434")

# ====================== LOGGING ======================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] <%(levelname)s> %(message)s",
    handlers=[
        RotatingFileHandler(
            "architect.log",
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8"
        )
    ]
)

logger = logging.getLogger(__name__)

# ====================== INITIALIZATION ======================
bot = Bot(token=TOKEN)
dp = Dispatcher()
ollama_client = AsyncClient(host=OLLAMA_URL)

# Setup hardware and get device
device = setup_hardware()

# User context (conversation history - last 15 messages)
user_history: dict[int, deque] = {}
pending_skills: dict[str, dict] = {}

# Initialize Neural Memory
memory_manager = MemoryManager()

# Initialize Voice Processor
voice_processor = VoiceProcessor(device=device)

def get_context(user_id: int) -> deque:
    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=15)
    return user_history[user_id]

# Register all handlers
register_handlers(dp, bot, ollama_client, MODEL_NAME, device, user_history, pending_skills, get_context, memory_manager, voice_processor)

# ====================== MAIN ======================
async def main():
    banner = pyfiglet.figlet_format("ARCHITECT", font="slant")
    print(banner)
    logger.info(f"The Architect is booting on MSI Claw {device.upper()}...")
    logger.info(f"Engine: {MODEL_NAME}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
