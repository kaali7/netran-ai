"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: config.py
Description: Configuration loader for Stage 3. Enforces Stage3Config object model.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Search for .env file up to backend root
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Force offline HuggingFace mode to prevent network overhead
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

USER_HOME = os.environ.get("USERPROFILE", os.path.expanduser("~"))

# Local model snapshot paths
DEFAULT_WHISPER_SNAPSHOT = os.path.join(
    USER_HOME,
    r".cache\huggingface\hub\models--Systran--faster-whisper-small\snapshots\536b0662742c02347bc0e980a01041f333bce120"
)

DEFAULT_KOKORO_SNAPSHOT = os.path.join(
    USER_HOME,
    r".cache\huggingface\hub\models--hexgrad--Kokoro-82M\snapshots\f3ff3571791e39611d31c381e3a41a3af07b4987"
)


def resolve_whisper_model_path() -> str:
    """Returns local snapshot path if present on disk, else fallback model string."""
    env_override = os.getenv("WHISPER_MODEL_PATH")
    if env_override and os.path.exists(env_override):
        return env_override
    if os.path.exists(DEFAULT_WHISPER_SNAPSHOT):
        return DEFAULT_WHISPER_SNAPSHOT
    return os.getenv("WHISPER_MODEL", "small")


def resolve_kokoro_model_path() -> str:
    """Returns HF repo ID string (Kokoro pipeline requires valid repo_id format)."""
    return os.getenv("KOKORO_MODEL", "hexgrad/Kokoro-82M")


@dataclass
class Stage3Config:
    """Stage 3 configuration data class."""
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:3b"))
    whisper_model: str = field(default_factory=resolve_whisper_model_path)
    kokoro_model: str = field(default_factory=resolve_kokoro_model_path)
    max_questions: int = field(default=15)

    @classmethod
    def from_env(cls) -> "Stage3Config":
        """Factory method creating config instance from environment variables."""
        return cls()

# Backward compatibility module-level exports
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
WHISPER_MODEL = resolve_whisper_model_path()
KOKORO_MODEL = resolve_kokoro_model_path()
MAX_QUESTIONS = 15


def auto_select_mic_device() -> int | None:
    """
    Auto-selects the best available microphone input device index for sounddevice.

    Priority order (highest to lowest) — ordered for 16kHz Silero VAD compatibility:
      1. MME Headset/USB mic
         Windows kernel mixer (KMixer) transparently resamples to any sample rate
         including 16kHz. Most reliable for Silero VAD on Windows.
      2. DirectSound Headset/USB mic
         DirectSound also supports flexible sample rates via KMixer.
      3. WASAPI Headset/USB mic  (LAST for headsets)
         WASAPI shared mode locks to the Windows Audio Session native rate (usually
         44100 or 48000 Hz). Requesting 16kHz on a 48kHz WASAPI device causes
         aliased click-noise glitches that Silero VAD cannot classify as speech
         (prob stays 0.000 even for loud audio). Only falls back to WASAPI if
         no MME/DirectSound headset is available.
      4. WASAPI built-in mic array (Intel Smart Sound Technology)
         Produces silence via MME but may work via WASAPI at its native rate.
      5. System default (None — let sounddevice pick)

    Skips known-problematic devices:
      - Intel Smart Sound Technology via MME (produces silence at 16kHz mono)
      - Virtual/loopback devices (Stereo Mix, PC Speaker input)
      - Bluetooth SCO low-quality input

    Returns device index (int) or None to use the sounddevice default.
    """
    try:
        import sounddevice as sd

        TARGET_RATE = 16000
        SKIP_KEYWORDS = ("stereo mix", "pc speaker", "what u hear", "loopback", "airbase", "airbass")
        PREFER_KEYWORDS = ("headset", "headphone", "usb", "zeb", "zebronics", "jabra", "realtek hd audio mic")
        BUILTIN_KEYWORDS = ("microphone array", "intel", "smart sound")

        devs = sd.query_devices()
        default_idx = sd.default.device[0]

        candidates_wasapi_16k_headset = []
        candidates_mme_headset = []
        candidates_ds_headset = []
        candidates_wasapi_headset = []
        candidates_ds_builtin = []
        candidates_wasapi_builtin = []

        print("[MicSelector] Scanning input devices:", flush=True)
        for i, d in enumerate(devs):
            if d["max_input_channels"] < 1:
                continue
            name_lower = d["name"].lower()
            api_info = sd.query_hostapis(d["hostapi"])
            api_name = api_info["name"]
            native_rate = int(d.get("default_samplerate", 0))
            rate_note = f"native={native_rate}Hz" + (" [OK] 16k" if native_rate == TARGET_RATE else " [MISMATCH]")

            # Skip virtual/loopback/bluetooth SCO
            if any(kw in name_lower for kw in SKIP_KEYWORDS):
                continue

            is_preferred = any(kw in name_lower for kw in PREFER_KEYWORDS)
            is_builtin = any(kw in name_lower for kw in BUILTIN_KEYWORDS)
            is_mme = "MME" in api_name
            is_ds = "DirectSound" in api_name
            is_wasapi = "WASAPI" in api_name
            is_wdm = "WDM-KS" in api_name

            # Skip Intel mic array via MME (produces silence at 16kHz mono)
            if is_builtin and is_mme:
                print(f"  [{i}] SKIP (Intel MME silent): {d['name']} | {api_name} | {rate_note}", flush=True)
                continue

            print(f"  [{i}] {d['name']} | {api_name} | {rate_note}", flush=True)

            if is_preferred:
                if is_wasapi and native_rate == TARGET_RATE:
                    candidates_wasapi_16k_headset.append(i)
                elif is_mme:
                    candidates_mme_headset.append(i)
                elif is_ds:
                    candidates_ds_headset.append(i)
                elif is_wasapi:
                    candidates_wasapi_headset.append(i)
            elif is_builtin:
                if is_ds:
                    candidates_ds_builtin.append(i)
                elif is_wasapi:
                    candidates_wasapi_builtin.append(i)

        # Return best candidate in priority order:
        # 1. MME / DirectSound — KMixer resamples cleanly (most robust fallback).
        # 2. WASAPI 16kHz native — bit-perfect, but often broken on Bluetooth headsets.
        for label, group in (
            ("MME headset", candidates_mme_headset),
            ("DirectSound headset", candidates_ds_headset),
            ("WASAPI 16kHz headset", candidates_wasapi_16k_headset),
            ("WASAPI headset", candidates_wasapi_headset),
            ("WASAPI built-in", candidates_wasapi_builtin),
            ("DirectSound built-in", candidates_ds_builtin),
        ):
            if group:
                chosen = group[0]
                chosen_dev = devs[chosen]
                api_name = sd.query_hostapis(chosen_dev["hostapi"])["name"]
                native_rate = int(chosen_dev.get("default_samplerate", 0))
                print(
                    f"[MicSelector] [*] Selected [{label}] device [{chosen}]: "
                    f"'{chosen_dev['name']}' ({api_name}) native={native_rate}Hz",
                    flush=True
                )
                if native_rate != TARGET_RATE and "WASAPI" in api_name:
                    print(
                        f"[MicSelector] [!] WARNING: Device native rate {native_rate}Hz != {TARGET_RATE}Hz target. "
                        f"WASAPI may not resample cleanly. If VAD prob stays 0.000, override with "
                        f"MIC_DEVICE_INDEX=<MME or DirectSound device index> in .env",
                        flush=True
                    )
                return chosen

        # Fall back to system default
        print(
            f"[MicSelector] Using system default device [{default_idx}]: "
            f"'{devs[default_idx]['name']}'",
            flush=True
        )
        return None

    except Exception as exc:
        print(f"[MicSelector] Device auto-select failed ({exc}), using default.", flush=True)
        return None


# Resolved mic device index (None = sounddevice system default)
MIC_DEVICE_INDEX: int | None = int(os.getenv("MIC_DEVICE_INDEX")) if os.getenv("MIC_DEVICE_INDEX") else None
