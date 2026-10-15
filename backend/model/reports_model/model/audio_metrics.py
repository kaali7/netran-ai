"""
Netran AI — Stage 4: Post-Session Evaluation & Report Generation Engine
Module: audio_metrics.py
Description: Fast deterministic speech delivery analytics computing speaking rate (WPM),
             pause metrics, speech coverage ratio, and filler word density directly
             from transcript text and audio timing metadata with zero external ML overhead.
"""

import re
from pathlib import Path
from typing import Any

FILLER_WORD_PATTERNS = [
    r"\bum\b",
    r"\buh\b",
    r"\buhh\b",
    r"\bah\b",
    r"\ber\b",
    r"\bhmm\b",
    r"\blike\b",
    r"\byou know\b",
    r"\bi mean\b",
    r"\bso yeah\b",
    r"\bactually\b",
    r"\bbasically\b",
]

COMPILED_FILLER_RE = [re.compile(p, re.IGNORECASE) for p in FILLER_WORD_PATTERNS]


def count_filler_words(text: str) -> tuple[int, list[str]]:
    """
    Detects common verbal fillers and stutters in transcript text.
    Returns total count and list of matched filler words.
    """
    if not text:
        return 0, []

    found = []
    total_count = 0
    lower_text = text.lower()

    for pattern in COMPILED_FILLER_RE:
        matches = pattern.findall(lower_text)
        if matches:
            total_count += len(matches)
            found.extend(matches)

    # Detect repeated consecutive words (e.g. "speaking speaking", "the the")
    words = re.findall(r"\b[a-zA-Z]{2,}\b", lower_text)
    for i in range(len(words) - 1):
        if words[i] == words[i + 1] and words[i] not in ["that", "had"]:
            total_count += 1
            found.append(f"{words[i]} {words[i]}")

    return total_count, found


def calculate_audio_metrics(
    transcript: str,
    duration_seconds: float,
    segments: list[dict[str, Any]] | None = None,
    audio_path: Path | str | None = None,
    pause_threshold: float = 0.7,
) -> dict[str, Any]:
    """
    Calculates deterministic vocal delivery metrics from transcript text and turn duration.

    Args:
        transcript: Candidate answer text
        duration_seconds: Total duration of the turn audio clip in seconds
        segments: Optional Faster-Whisper segments with 'start' and 'end' timestamps
        audio_path: Optional path to WAV clip for acoustic energy estimation
        pause_threshold: Minimum gap duration in seconds to classify as a long pause

    Returns:
        Dictionary with speaking_rate_wpm, speech_duration_seconds, silence_seconds,
        speech_coverage_ratio, long_pause_count, filler_word_count, hesitation_level.
    """
    duration = max(float(duration_seconds), 0.1)
    words = re.findall(r"\b[\w'-]+\b", transcript or "")
    word_count = len(words)

    filler_count, fillers_found = count_filler_words(transcript)

    # 1. Segment-based speech interval calculation if segments provided
    long_pause_count = 0
    long_pauses: list[float] = []
    speech_duration = 0.0

    if segments and len(segments) > 0:
        speech_intervals = []
        for seg in segments:
            start = max(float(seg.get("start", 0.0)), 0.0)
            end = min(float(seg.get("end", duration)), duration)
            if end > start:
                speech_intervals.append((start, end))

        speech_intervals.sort(key=lambda x: x[0])

        merged: list[list[float]] = []
        for start, end in speech_intervals:
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])

        # Calculate speech duration
        speech_duration = sum(interval[1] - interval[0] for interval in merged)
        speech_duration = min(speech_duration, duration)

        # Detect gaps between consecutive segments
        for i in range(len(merged) - 1):
            gap = merged[i + 1][0] - merged[i][1]
            if gap >= pause_threshold:
                long_pause_count += 1
                long_pauses.append(round(gap, 2))

        # Check leading silence
        if merged and merged[0][0] >= pause_threshold:
            long_pause_count += 1
            long_pauses.append(round(merged[0][0], 2))

    else:
        # Acoustic heuristic estimation from duration and word count
        # Average conversational speaking rate: ~2.3 words per second of active speech
        estimated_speech = min(duration, max(1.0, word_count / 2.3))
        speech_duration = round(estimated_speech, 2)
        silence_est = max(0.0, duration - speech_duration)
        if silence_est >= pause_threshold * 2:
            long_pause_count = max(1, int(silence_est // pause_threshold))

    silence_seconds = max(0.0, duration - speech_duration)
    speech_coverage = min(1.0, max(0.0, speech_duration / duration))

    # 2. Speaking Rate (Words Per Minute)
    # Measured over speech duration if available, else total duration
    active_minutes = max(speech_duration / 60.0, 0.05)
    wpm = round(word_count / active_minutes, 1) if word_count > 0 else 0.0

    # 3. Hesitation Level Scoring
    # Normal conversational pace: 120-160 WPM. Hesitant: < 110 WPM with high pauses/fillers.
    if wpm < 95 or long_pause_count >= 3 or filler_count >= 5:
        hesitation_level = "High"
    elif wpm < 120 or long_pause_count >= 1 or filler_count >= 2:
        hesitation_level = "Medium"
    else:
        hesitation_level = "Low"

    return {
        "word_count": word_count,
        "duration_seconds": round(duration, 2),
        "speech_duration_seconds": round(speech_duration, 2),
        "silence_seconds": round(silence_seconds, 2),
        "speaking_rate_wpm": wpm,
        "speech_coverage_ratio": round(speech_coverage, 2),
        "long_pause_count": long_pause_count,
        "long_pauses_seconds": long_pauses,
        "filler_word_count": filler_count,
        "filler_words_found": fillers_found,
        "hesitation_level": hesitation_level,
    }
