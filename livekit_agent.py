import asyncio
import math
import os
import requests
import struct
import tempfile
import wave

import av
from livekit import rtc

import config
from stt import transcribe
from tts import speak
from translator import to_english, from_english
from retriever import retrieve
from llm import generate


# LiveKit outgoing audio (must match WebRTC expectations; 48k mono is standard).
AGENT_PLAYBACK_SR = 48000
AGENT_PLAYBACK_CH = 1

# Filled in main() after publish — used to play TTS into the room.
_agent_audio_source: rtc.AudioSource | None = None


#  Get token from backend
def get_token():
    res = requests.get(
        config.TOKEN_SERVER_URL,
        params={"identity": "agent1", "room": "voice-room"}
    )
    return res.json()["token"]


#  Build RAG context
def build_context(results):
    if not results:
        return "No products found."

    return "\n".join([
        f"{p['name']} ₹{p['price']} - {p['description']}"
        for p in results
    ])


def _pcm16le_rms(pcm: bytes) -> float:
    """RMS of int16 mono (or de-interleaved as mono chunk) PCM."""
    if len(pcm) < 2:
        return 0.0
    n = len(pcm) // 2
    samples = struct.unpack_from(f"<{n}h", pcm, 0)
    if not samples:
        return 0.0
    acc = sum(s * s for s in samples)
    return math.sqrt(acc / len(samples))


def _chunk_duration_ms(pcm: bytes, sample_rate: int, channels: int) -> float:
    if sample_rate <= 0 or channels <= 0:
        return 0.0
    samples = len(pcm) // (2 * channels)
    return 1000.0 * samples / float(sample_rate)


def mp3_to_pcm48_mono(path: str) -> bytes:
    """Decode MP3 (edge-tts) to 48 kHz s16le mono for LiveKit AudioSource."""
    out = bytearray()
    with av.open(path) as container:
        stream = container.streams.audio[0]
        resampler = av.audio.resampler.AudioResampler(
            format="s16", layout="mono", rate=AGENT_PLAYBACK_SR
        )
        for packet in container.demux(stream):
            for frame in packet.decode():
                for rf in resampler.resample(frame):
                    arr = rf.to_ndarray()
                    if arr.ndim == 2:
                        arr = arr[0]
                    out.extend(arr.tobytes())
    return bytes(out)


async def play_mp3_to_livekit(source: rtc.AudioSource, mp3_path: str) -> None:
    """Stream decoded TTS to the room as 10 ms PCM frames."""
    pcm = await asyncio.to_thread(mp3_to_pcm48_mono, mp3_path)
    if not pcm:
        print(" No PCM decoded from TTS; skipping playback")
        return

    source.clear_queue()

    samples_per_ch = 480  # 10 ms @ 48 kHz
    frame_bytes = samples_per_ch * AGENT_PLAYBACK_CH * 2
    offset = 0
    while offset < len(pcm):
        chunk = pcm[offset : offset + frame_bytes]
        if len(chunk) < frame_bytes:
            chunk = chunk + b"\x00" * (frame_bytes - len(chunk))
        frame = rtc.AudioFrame(
            chunk,
            AGENT_PLAYBACK_SR,
            AGENT_PLAYBACK_CH,
            samples_per_ch,
        )
        # capture_frame is async in current livekit-python; must await (not to_thread).
        await source.capture_frame(frame)
        offset += frame_bytes
        await asyncio.sleep(0.0095)


# Whisper often hallucinates these on noise / near-silence; skip replying.
# One utterance at a time so STT/LLM don't fight for CPU and replies stay ordered.
_utterance_sem = asyncio.Semaphore(1)

_JUNK_TRANSCRIPTS = frozenset(
    x.lower()
    for x in (
        "you",
        "you.",
        "uh",
        "oh",
        "mm",
        "mmm",
        "thanks for watching.",
        "subscribe",
    )
)


async def _process_utterance(audio_path: str) -> None:
    async with _utterance_sem:
        mp3_path: str | None = None
        try:
            text, lang = await asyncio.to_thread(transcribe, audio_path)

            t = (text or "").strip()
            if not t:
                return
            if len(t) <= 4 and t.lower() in _JUNK_TRANSCRIPTS:
                print("⏭ Skipping junk / noise transcript:", repr(t))
                return

            print(" User:", t, "| Lang:", lang)

            # RAG uses multilingual embeddings on the raw transcript; English query for LLM in parallel.
            if lang == "en":
                query_en = t
                results = await asyncio.to_thread(retrieve, t)
            else:
                query_en, results = await asyncio.gather(
                    asyncio.to_thread(to_english, t, lang),
                    asyncio.to_thread(retrieve, t),
                )
            context = build_context(results)
            answer_en = await asyncio.to_thread(generate, context, query_en)
            final = await asyncio.to_thread(from_english, answer_en, lang)

            print(" Bot:", final)

            mp3_path = await speak(final, lang)
            print(" TTS file:", mp3_path)

            src = _agent_audio_source
            if src is not None:
                await play_mp3_to_livekit(src, mp3_path)
                print(" Agent audio sent to the meeting")
            else:
                print(" No AudioSource; only saved file above")
        finally:
            try:
                os.unlink(audio_path)
            except OSError:
                pass
            if mp3_path:
                try:
                    os.unlink(mp3_path)
                except OSError:
                    pass


def _write_wav(path: str, pcm: bytes, sample_rate: int, channels: int) -> None:
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)


#  Handle audio stream (silence-based endpointing — full sentence, not 1s slices)
async def handle_audio(room, track):
    print(" Track received")

    if not isinstance(track, rtc.RemoteAudioTrack):
        print(" Not an audio track, skipping...")
        return

    print(" Audio track confirmed")

    stream = rtc.AudioStream(track)

    sample_rate = 16000
    channels = 1

    # Endpointing: start on speech-like RMS, end after sustained silence.
    speech_start_rms = 95.0
    silence_rms = 62.0
    end_silence_ms = 520.0
    min_utterance_ms = 380.0
    max_utterance_ms = 18000.0
    min_flush_rms = 72.0

    speech_buf = bytearray()
    in_speech = False
    silence_ms = 0.0

    async for event in stream:
        frame = getattr(event, "frame", event)
        chunk = getattr(frame, "data", None)

        if chunk is None:
            continue

        if isinstance(chunk, memoryview):
            chunk = chunk.tobytes()
        elif not isinstance(chunk, (bytes, bytearray)):
            chunk = bytes(chunk)

        if hasattr(frame, "sample_rate"):
            sample_rate = frame.sample_rate
        if hasattr(frame, "num_channels"):
            channels = frame.num_channels

        dur_ms = _chunk_duration_ms(chunk, sample_rate, channels)
        rms = _pcm16le_rms(chunk)

        if not in_speech:
            if rms >= speech_start_rms:
                in_speech = True
                speech_buf.clear()
                speech_buf += chunk
                silence_ms = 0.0
            continue

        speech_buf += chunk

        if rms < silence_rms:
            silence_ms += dur_ms
        else:
            silence_ms = 0.0

        ut_ms = _chunk_duration_ms(bytes(speech_buf), sample_rate, channels)

        should_flush = (
            silence_ms >= end_silence_ms and ut_ms >= min_utterance_ms
        ) or (ut_ms >= max_utterance_ms)

        if not should_flush:
            continue

        pcm = bytes(speech_buf)
        speech_buf.clear()
        in_speech = False
        silence_ms = 0.0

        overall_rms = _pcm16le_rms(pcm)
        if overall_rms < min_flush_rms:
            continue

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name
        _write_wav(wav_path, pcm, sample_rate, channels)
        asyncio.create_task(_process_utterance(wav_path))


#  Main function
async def main():
    global _agent_audio_source

    room = rtc.Room()

    token = get_token()

    await room.connect(config.LIVEKIT_URL, token)

    _agent_audio_source = rtc.AudioSource(AGENT_PLAYBACK_SR, AGENT_PLAYBACK_CH)
    agent_track = rtc.LocalAudioTrack.create_audio_track("agent-voice", _agent_audio_source)
    pub_opts = rtc.TrackPublishOptions()
    pub_opts.source = rtc.TrackSource.SOURCE_MICROPHONE
    await room.local_participant.publish_track(agent_track, pub_opts)
    print(" Agent running... Mic published for TTS; waiting for user audio...")

    @room.on("track_subscribed")
    def on_track(track, publication, participant):
        if participant.identity == room.local_participant.identity:
            return
        print(" Track subscribed")

        if track.kind == rtc.TrackKind.KIND_AUDIO:
            asyncio.create_task(handle_audio(room, track))
        else:
            print("⏭ Skipping non-audio track")

    await asyncio.Future()


# Run
if __name__ == "__main__":
    asyncio.run(main())
