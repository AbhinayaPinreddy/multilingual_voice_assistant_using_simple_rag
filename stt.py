from faster_whisper import WhisperModel

import config

model = WhisperModel(config.WHISPER_MODEL, compute_type="int8")


def transcribe(audio_path):
    # vad_filter drops leading/trailing silence and reduces "You" / junk on silent audio.
    # beam_size=1, condition_on_previous_text=False: faster decode with small quality trade-off.
    segments, info = model.transcribe(
        audio_path,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400),
        beam_size=1,
        condition_on_previous_text=False,
    )
    text = " ".join([s.text for s in segments])
    return text.strip(), info.language