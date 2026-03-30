import edge_tts
import tempfile

# Microsoft Edge neural voices (India) — all female.
VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "te": "te-IN-ShrutiNeural",
}

_DEFAULT_VOICE = "en-IN-NeerjaNeural"


async def generate_audio(text, lang, path):
    voice = VOICE_MAP.get(lang, _DEFAULT_VOICE)
    com = edge_tts.Communicate(text, voice)
    await com.save(path)


async def speak(text, lang):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        path = tmp.name

    await generate_audio(text, lang, path)
    return path