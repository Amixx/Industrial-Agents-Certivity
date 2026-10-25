"""Spoken answers in an ElevenLabs voice instead of the browser's. Off unless ELEVENLABS_API_KEY
is set; without it the report falls back to the browser's own speech.

Only answers the server wrote can be spoken: /api/ask remembers each answer's text under a
random id and /api/speak/{id} voices that text, so the key can't be used to read anything else.
"""

import json
import logging
import os
import secrets
import threading
import urllib.request
from collections import OrderedDict
from collections.abc import Iterator
from typing import Any

VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_flash_v2_5")
# Answers are three short sentences; this caps what one call can bill.
MAX_CHARS = 1000
KEEP = 100

log = logging.getLogger("uvicorn.error")

# id -> [text, mp3 once voiced], oldest first. The audio is kept so a replay doesn't bill again.
_answers: OrderedDict[str, list[str | bytes | None]] = OrderedDict()
_lock = threading.Lock()


def enabled() -> bool:
    return bool(os.environ.get("ELEVENLABS_API_KEY"))


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _plain(text: str) -> str:
    return " ".join(text.split()).casefold()


def readable(selection: str, report: Any) -> str:
    """The lines of a selection that are the report's own prose. Labels, ids and page numbers are
    left out, and so is anything not in the report, so the key only ever voices the report."""
    prose = "\n".join(s for s in _strings(report) if len(s) >= 20)
    corpus = _plain(prose)
    lines = (" ".join(line.split()) for line in selection.splitlines())
    keep = [line for line in lines if len(line.split()) >= 2 and _plain(line) in corpus]
    return " ".join(keep)


def remember(text: str) -> str:
    speech_id = secrets.token_urlsafe(12)
    with _lock:
        _answers[speech_id] = [text[:MAX_CHARS], None]
        while len(_answers) > KEEP:
            _answers.popitem(last=False)
    return speech_id


def audio(speech_id: str) -> bytes:
    """MP3 of a remembered answer. KeyError for an unknown id, OSError when ElevenLabs fails."""
    with _lock:
        text, mp3 = _answers[speech_id]
    if isinstance(mp3, bytes):
        return mp3
    assert isinstance(text, str)
    mp3 = _synthesize(text)
    with _lock:
        if speech_id in _answers:
            _answers[speech_id][1] = mp3
    return mp3


def _synthesize(text: str) -> bytes:
    request = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": MODEL}).encode(),
        headers={
            "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        mp3: bytes = response.read()
    log.info("speak: %s characters, voice %s, %s", len(text), VOICE_ID, MODEL)
    return mp3
