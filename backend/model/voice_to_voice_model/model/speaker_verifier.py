"""
Netran AI — Stage 3: Speaker Verification Engine
Module: speaker_verifier.py

Uses SpeechBrain ECAPA-TDNN (speechbrain/spkrec-ecapa-voxceleb) to verify
that detected speech belongs to the enrolled candidate before forwarding
to Whisper STT.

Architecture:
  - Enrollment: auto-enroll from first ICEBREAKER utterance (>= 2 seconds).
    Compute mean 192-dim speaker embedding and store in memory.
  - Verification: compute embedding from each completed utterance,
    compare cosine similarity against enrolled embedding.
      score >= ACCEPT_THRESHOLD -> candidate speaking -> forward to STT
      score < ACCEPT_THRESHOLD  -> foreign speaker    -> reject, return ""

Performance:
  - Model: ~100MB disk, runs on CPU
  - Inference: ~15-25ms per utterance (run once per completed speech segment,
    NOT per 32ms VAD frame)
  - Does NOT affect TTFT/TTFA benchmarks

Auto-Enrollment (Option B — Human-Like):
  If no manual enrollment recording exists, the verifier auto-enrolls from
  the FIRST accepted utterance that passes VAD AND is longer than 2 seconds.
  This lets the ICEBREAKER turn bootstrap speaker identity silently.
  Until enrollment completes, verify() returns (True, 1.0) — all speech
  is accepted to avoid blocking the initial conversation flow.
"""

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING
import numpy as np
from dotenv import load_dotenv

if TYPE_CHECKING:
    import torch

# Load .env
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)



class SpeakerVerifier:
    """
    Offline ECAPA-TDNN speaker verification engine.

    Usage in front.py:
        verifier = SpeakerVerifier()
        # Pass to listen_and_transcribe() — auto-enrolls on first long utterance
        transcript = listen_and_transcribe(..., speaker_verifier=verifier)
    """

    # Default cosine similarity threshold (tunable via .env SV_THRESHOLD, default 0.30 for browser audio)
    ACCEPT_THRESHOLD = float(os.getenv("SV_THRESHOLD", "0.30"))

    def __init__(self, model_source: str = "speechbrain/spkrec-ecapa-voxceleb"):
        """
        Initialize the ECAPA-TDNN speaker encoder.

        Args:
            model_source: HuggingFace model ID or local path. Loaded offline
                          from HF cache if HF_HUB_OFFLINE=1.
        """
        self._classifier = None
        self._model_source = model_source
        self._enrolled_embedding = None  # Shape: [1, 1, 192] torch tensor
        self._is_enrolled = False
        self._load_failed = False

    @property
    def is_enrolled(self) -> bool:
        """Returns True if a candidate voice has been enrolled."""
        return self._is_enrolled

    @property
    def is_available(self) -> bool:
        """Returns True if the model loaded successfully."""
        return self._classifier is not None and not self._load_failed

    def _ensure_loaded(self) -> bool:
        """Lazy-loads the SpeechBrain ECAPA-TDNN model on first use."""
        if self._classifier is not None:
            return True
        if self._load_failed:
            return False

        try:
            from speechbrain.inference.speaker import EncoderClassifier

            print("[SpeakerVerifier] Loading ECAPA-TDNN model (offline)...", flush=True)
            t0 = time.monotonic()
            self._classifier = EncoderClassifier.from_hparams(
                source=self._model_source,
                run_opts={"device": "cpu"},
            )
            elapsed = (time.monotonic() - t0) * 1000
            print(f"[SpeakerVerifier] Model loaded in {elapsed:.0f}ms", flush=True)
            return True
        except Exception as exc:
            print(
                f"[SpeakerVerifier] ECAPA-TDNN model load failed: {exc}. "
                f"Speaker verification DISABLED for this session.",
                flush=True,
            )
            self._load_failed = True
            return False

    def _compute_embedding(self, audio_np: np.ndarray) -> "torch.Tensor | None":
        """
        Compute 192-dim speaker embedding from raw 16kHz float32 numpy array.

        Args:
            audio_np: 1D float32 array at 16kHz sample rate.

        Returns:
            Embedding tensor of shape [1, 1, 192] or None on failure.
        """
        if not self._ensure_loaded():
            return None

        import torch

        # SpeechBrain encode_batch expects [batch, time] tensor
        signal = torch.from_numpy(audio_np.astype(np.float32)).unsqueeze(0)
        wav_lens = torch.tensor([1.0])

        with torch.no_grad():
            embedding = self._classifier.encode_batch(signal, wav_lens=wav_lens)

        return embedding  # Shape: [1, 1, 192]

    def enroll(self, audio_np: np.ndarray) -> bool:
        """
        Enroll the candidate's voice from a numpy audio array.

        Called automatically from listener.py on the first utterance >= 2 seconds
        that passes VAD (the ICEBREAKER turn). Can also be called manually.

        Args:
            audio_np: 1D float32 array at 16kHz, at least 2 seconds long.

        Returns:
            True if enrollment succeeded, False otherwise.
        """
        if len(audio_np) < 16000 * 1.5:  # Minimum 1.5 seconds for robust enrollment
            print(f"[SpeakerVerifier] Enrollment audio too short ({len(audio_np)/16000:.1f}s < 1.5s)", flush=True)
            return False

        embedding = self._compute_embedding(audio_np)
        if embedding is None:
            return False

        self._enrolled_embedding = embedding
        self._is_enrolled = True
        print(
            f"[SpeakerVerifier] ✅ Candidate voice enrolled "
            f"({len(audio_np)/16000:.1f}s audio, 192-dim embedding captured)",
            flush=True,
        )
        return True

    def verify(self, audio_np: np.ndarray) -> tuple[bool, float]:
        """
        Verify if the given audio matches the enrolled candidate.

        Args:
            audio_np: 1D float32 array at 16kHz.

        Returns:
            (is_candidate, similarity_score):
                is_candidate: True if cosine similarity >= threshold.
                similarity_score: float in [-1.0, 1.0] (higher = more similar).

            If not enrolled yet, returns (True, 1.0) to allow the ICEBREAKER
            turn through without blocking.
        """
        if not self._is_enrolled:
            return True, 1.0  # Pass-through until enrolled

        if not self._ensure_loaded():
            return True, 1.0  # Model unavailable — fail-open

        # Skip short audio segments (< 1.2s) — not enough for reliable verification, pass through
        if len(audio_np) < 16000 * 1.2:
            return True, 1.0

        import torch

        test_embedding = self._compute_embedding(audio_np)
        if test_embedding is None:
            return True, 1.0  # Compute failed — fail-open

        # Cosine similarity between enrolled and test embeddings
        sim = torch.nn.functional.cosine_similarity(
            self._enrolled_embedding.squeeze(),
            test_embedding.squeeze(),
            dim=0,
        ).item()

        is_candidate = sim >= self.ACCEPT_THRESHOLD
        return is_candidate, float(sim)


# ── Standalone Diagnostic ────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    print("=" * 60)
    print("  NETRAN AI — Speaker Verifier Diagnostic")
    print("=" * 60)

    verifier = SpeakerVerifier()
    if not verifier._ensure_loaded():
        print("\n[FAIL] Could not load ECAPA-TDNN model. Check HF cache.")
        sys.exit(1)

    print(f"\n[OK] Model loaded. Threshold: {verifier.ACCEPT_THRESHOLD}")
    print(f"[INFO] Enrolled: {verifier.is_enrolled}")

    # Test with synthetic audio
    fake_audio = np.random.randn(16000 * 3).astype(np.float32) * 0.01
    print("\n[TEST] Computing embedding from 3s synthetic audio...")
    success = verifier.enroll(fake_audio)
    print(f"[TEST] Enrollment: {'SUCCESS' if success else 'FAILED'}")

    if success:
        is_same, score = verifier.verify(fake_audio)
        print(f"[TEST] Self-verify: is_candidate={is_same}, score={score:.4f}")

        different_audio = np.random.randn(16000 * 3).astype(np.float32) * 0.01
        is_same2, score2 = verifier.verify(different_audio)
        print(f"[TEST] Different voice: is_candidate={is_same2}, score={score2:.4f}")

    print("\n[DONE] Speaker verifier diagnostic complete.")
