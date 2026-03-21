import edge_tts
import asyncio
import tempfile
import pygame
import os

pygame.mixer.init()

VOICE_MAP = {
    "en": "en-US-JennyNeural",
    "hi": "hi-IN-SwaraNeural",
    "te": "te-IN-ShrutiNeural"
}

async def _generate(text, voice, path):
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(path)

def speak(text, lang):
    voice = VOICE_MAP.get(lang, "en-US-JennyNeural")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        path = tmp.name

    #  Safe async handling for both Windows & Linux
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        loop.run_until_complete(_generate(text, voice, path))
    else:
        asyncio.run(_generate(text, voice, path))

    pygame.mixer.music.load(path)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.wait(50)

    pygame.mixer.music.unload()
    os.remove(path)