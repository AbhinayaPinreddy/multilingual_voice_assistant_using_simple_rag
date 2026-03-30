import os
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
TOKEN_SERVER_URL = "http://127.0.0.1:8000/get-token"

# Latency tuning (env overrides)
# Whisper: "base" is faster than "small"; use "small" if quality drops too much.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
# Fewer RAG hits = shorter LLM prompt and faster generation.
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "72"))