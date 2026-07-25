"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: audio_slicer.py
Description: Non-destructive WAV slicing utility using standard Python `wave` module to extract per-turn
             audio clips (`turn_01.wav`, `turn_02.wav`, etc.) based on `session_manifest.json` millisecond timestamps.
"""

import json
import wave
from pathlib import Path
from typing import Dict, Any, Union


def slice_audio(
    wav_path: Union[str, Path],
    manifest: Dict[str, Any],
    output_dir: Union[str, Path]
) -> Dict[int, Path]:
    """
    Slices continuous_mic_input.wav into per-turn WAV clips based on session_manifest.json timestamps.

    Args:
        wav_path: Path to continuous_mic_input.wav
        manifest: Loaded session_manifest.json data dictionary
        output_dir: Directory where sliced turn WAVs will be written

    Returns:
        Dict mapping turn_id (int) to the sliced clip Path object.
    """
    wav_path = Path(wav_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sliced_clips: Dict[int, Path] = {}

    if not wav_path.exists():
        raise FileNotFoundError(f"Continuous audio recording not found at: {wav_path}")

    turns = manifest.get("turns", [])
    if not turns:
        print("[AudioSlicer] Warning: No turns found in manifest.")
        return sliced_clips

    with wave.open(str(wav_path), "rb") as wf:
        sample_rate = wf.getframerate()
        num_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        total_frames = wf.getnframes()
        total_duration = total_frames / sample_rate

        for turn in turns:
            turn_id = turn.get("turn_id", 1)
            start_sec = turn.get("audio_start_sec", 0.0)
            end_sec = turn.get("audio_end_sec", 0.0)

            # If timestamp exceeds recording length (e.g. wall-clock shift or short test clip), adjust to available audio
            if start_sec >= total_duration:
                clip_duration = end_sec - start_sec if (end_sec > start_sec) else total_duration
                actual_start_sec = max(0.0, total_duration - clip_duration)
                actual_end_sec = total_duration
                print(f"[AudioSlicer] Note: turn {turn_id} timestamps [{start_sec}s..{end_sec}s] exceed audio length ({total_duration:.2f}s). Mapping to [{actual_start_sec:.2f}s..{actual_end_sec:.2f}s].")
            else:
                actual_start_sec = start_sec
                actual_end_sec = min(end_sec, total_duration) if end_sec > start_sec else total_duration

            # Convert seconds to frame numbers
            start_frame = int(actual_start_sec * sample_rate)
            end_frame = int(actual_end_sec * sample_rate)

            # Ensure non-zero frame count
            if end_frame <= start_frame:
                start_frame = 0
                end_frame = total_frames

            num_frames_to_read = end_frame - start_frame

            wf.setpos(start_frame)
            raw_frames = wf.readframes(num_frames_to_read)

            clip_filename = f"turn_{turn_id:02d}.wav"
            clip_path = output_dir / clip_filename

            with wave.open(str(clip_path), "wb") as out_wf:
                out_wf.setnchannels(num_channels)
                out_wf.setsampwidth(sample_width)
                out_wf.setframerate(sample_rate)
                out_wf.writeframes(raw_frames)

            sliced_clips[turn_id] = clip_path
            print(f"[AudioSlicer] Successfully created {clip_path.name} ({num_frames_to_read} frames, {num_frames_to_read/sample_rate:.2f}s)")

    return sliced_clips
