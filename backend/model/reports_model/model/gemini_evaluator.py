"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: gemini_evaluator.py
Description: 3-branch Gemini Multimodal Evaluation Engine using `google-genai` SDK (`gemini-3.6-flash`).
             Evaluates Audio Branch (tone, hesitation, verified transcript), Technical Branch (accuracy, missing concepts),
             and Combine Synthesis Branch (final executive hiring report) with robust 429 RateLimit auto-retry backoff.
"""

import json
import time
from pathlib import Path
from typing import Any

from google import genai

from .schemas import AudioBranchOutput, CandidateReportPayload, TechnicalBranchOutput

try:
    from .config import Stage4Config
except ImportError:
    try:
        from model.reports_model.model.config import Stage4Config
    except ImportError:
        from config import Stage4Config

try:
    from .prompts import (
        get_audio_prompt,
        get_combine_prompt,
        get_technical_prompt,
    )
except ImportError:
    try:
        from model.reports_model.model.prompts import (
            get_audio_prompt,
            get_combine_prompt,
            get_technical_prompt,
        )
    except ImportError:
        from prompts import (
            get_audio_prompt,
            get_combine_prompt,
            get_technical_prompt,
        )


class GeminiMultimodalEvaluator:
    def __init__(self, model_name: str | None = None, config: Stage4Config | None = None):
        self.config = config or Stage4Config.from_env()
        api_key = self.config.gemini_api_key
        if not api_key:
            print("[GeminiEvaluator] Warning: GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name or self.config.gemini_model or "gemini-3.6-flash"

    def _create_interaction_with_retry(self, **kwargs) -> Any:
        """
        Executes self.client.interactions.create with automatic exponential backoff for 429 RateLimit / Quota Errors.
        """
        max_retries = 5
        base_delay = 6  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                return self.client.interactions.create(**kwargs)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower() or "too many requests" in err_str.lower():
                    if attempt == max_retries:
                        print(f"[GeminiEvaluator] [ERROR] Exceeded max retries ({max_retries}) on RateLimit 429: {e}")
                        raise e
                    sleep_time = base_delay * (2 ** (attempt - 1))  # 6s, 12s, 24s, 48s
                    print(f"[GeminiEvaluator] [RateLimit 429 Warning] Quota exceeded. Retrying attempt {attempt}/{max_retries} in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    raise e

    def evaluate_audio_branch(self, turn_id: int, audio_clip_path: Path, resume_text: str = "", jd_rubric_text: str = "") -> AudioBranchOutput:
        """
        Branch 1: Audio Branch - uploads audio WAV clip and evaluates speech & tone.
        """
        print(f"[GeminiEvaluator] [Audio Branch] Uploading clip for Turn {turn_id}: {audio_clip_path.name}")
        uploaded_file = self.client.files.upload(file=str(audio_clip_path))

        prompt = f"Analyze turn {turn_id} candidate audio clip. Extract transcript, vocal confidence, hesitation, emotion, filler count, and speech delivery notes."

        interaction = self._create_interaction_with_retry(
            model=self.model_name,
            system_instruction=get_audio_prompt(resume_text, jd_rubric_text),
            input=[
                {"type": "text", "text": prompt},
                {
                    "type": "audio",
                    "uri": uploaded_file.uri,
                    "mime_type": "audio/wav"
                }
            ],
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": AudioBranchOutput.model_json_schema()
            }
        )

        output_dict = json.loads(interaction.output_text)
        output_dict["turn_id"] = turn_id
        return AudioBranchOutput.model_validate(output_dict)

    def evaluate_technical_branch(
        self,
        turn_id: int,
        topic: str,
        question_text: str,
        candidate_transcript: str,
        resume_text: str = "",
        jd_rubric_text: str = ""
    ) -> TechnicalBranchOutput:
        """
        Branch 2: Technical Branch - evaluates transcript correctness against topic/question.
        """
        print(f"[GeminiEvaluator] [Technical Branch] Evaluating transcript for Turn {turn_id}")
        prompt = f"""
Topic: {topic}
Interviewer Question: {question_text}
Candidate Answer Transcript: {candidate_transcript}

Evaluate technical depth, correctness, missing concepts, and assign a score (1-10).
"""

        interaction = self._create_interaction_with_retry(
            model=self.model_name,
            system_instruction=get_technical_prompt(resume_text, jd_rubric_text),
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": TechnicalBranchOutput.model_json_schema()
            }
        )

        output_dict = json.loads(interaction.output_text)
        output_dict["turn_id"] = turn_id
        return TechnicalBranchOutput.model_validate(output_dict)

    def evaluate_combine_branch(
        self,
        session_id: str,
        turns_data: list[dict[str, Any]],
        audio_outputs: list[AudioBranchOutput],
        technical_outputs: list[TechnicalBranchOutput],
        resume_text: str = "",
        jd_rubric_text: str = ""
    ) -> CandidateReportPayload:
        """
        Branch 3: Combine Branch - fuses Audio & Technical branch outputs into full CandidateReportPayload.
        """
        print(f"[GeminiEvaluator] [Combine Branch] Synthesizing final report payload for session {session_id}")

        turn_payloads = []
        telemetry_map = {}

        for i, turn in enumerate(turns_data):
            t_id = turn.get("turn_id", i + 1)
            aud = next((a for a in audio_outputs if a.turn_id == t_id), None)
            tec = next((t for t in technical_outputs if t.turn_id == t_id), None)

            silence_sec = turn.get("silence_duration_before_answer_sec", 0.0)
            latency_ms = int(silence_sec * 1000)
            start_sec = turn.get("audio_start_sec", 0.0)
            end_sec = turn.get("audio_end_sec", 0.0)
            duration_sec = round(max(0.0, end_sec - start_sec), 2)

            orig_tx = turn.get("candidate_transcript", "")
            gemini_tx = aud.gemini_verified_transcript if aud else ""

            is_hallucination = False
            if len(orig_tx.split()) > 6 and (
                len(gemini_tx.split()) <= 3
                or "don't know" in gemini_tx.lower()
                or "unclear" in gemini_tx.lower()
                or "short" in gemini_tx.lower()
            ):
                is_hallucination = True

            telemetry_data = {
                "initial_silence_latency_ms": latency_ms,
                "turn_duration_sec": duration_sec,
                "stt_whisper_hallucination_flag": is_hallucination
            }
            telemetry_map[t_id] = telemetry_data

            turn_payloads.append({
                "turn_id": t_id,
                "topic": turn.get("topic", "General"),
                "question_text": turn.get("question_text", ""),
                "original_transcript": orig_tx,
                "telemetry": telemetry_data,
                "audio_eval": aud.model_dump() if aud else {},
                "technical_eval": tec.model_dump() if tec else {}
            })

        combine_input_prompt = f"""
Session ID: {session_id}
Turn Analysis Data:
{json.dumps(turn_payloads, indent=2)}

Please synthesize the final comprehensive CandidateReportPayload adhering strictly to the JSON schema.
Ensure all overall scores, technical pillars, behavioral flags, candidate feedback roadmap, turn evaluations, and hiring signals are populated accurately.
"""

        interaction = self._create_interaction_with_retry(
            model=self.model_name,
            system_instruction=get_combine_prompt(resume_text, jd_rubric_text),
            input=combine_input_prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": CandidateReportPayload.model_json_schema()
            }
        )

        output_dict = json.loads(interaction.output_text)

        # Inject exact telemetry into generated turn_evaluations
        if "turn_evaluations" in output_dict:
            for t_item in output_dict["turn_evaluations"]:
                tid = t_item.get("turn_id")
                if tid in telemetry_map:
                    t_item["telemetry"] = telemetry_map[tid]

        return CandidateReportPayload.model_validate(output_dict)
