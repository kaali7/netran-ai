"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: gemini_evaluator.py
Description: 3-branch Gemini Multimodal Evaluation Engine using `google-genai` SDK (`gemini-3.6-flash`).
             Evaluates Audio Branch (tone, hesitation, verified transcript), Technical Branch (accuracy, missing concepts),
             and Combine Synthesis Branch (final executive hiring report).
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from google import genai
from dotenv import load_dotenv

from .schemas import (
    AudioBranchOutput,
    TechnicalBranchOutput,
    CandidateReportPayload,
    TurnAnalysis,
    PillarScore
)
try:
    from .config import Stage4Config
except ImportError:
    try:
        from model.reports_model.model.config import Stage4Config
    except ImportError:
        from config import Stage4Config

try:
    from .prompts import AUDIO_SYSTEM_PROMPT, TECHNICAL_SYSTEM_PROMPT, COMBINE_SYSTEM_PROMPT
except ImportError:
    try:
        from model.reports_model.model.prompts import AUDIO_SYSTEM_PROMPT, TECHNICAL_SYSTEM_PROMPT, COMBINE_SYSTEM_PROMPT
    except ImportError:
        from prompts import AUDIO_SYSTEM_PROMPT, TECHNICAL_SYSTEM_PROMPT, COMBINE_SYSTEM_PROMPT


class GeminiMultimodalEvaluator:
    def __init__(self, model_name: Optional[str] = None, config: Optional[Stage4Config] = None):
        self.config = config or Stage4Config.from_env()
        api_key = self.config.gemini_api_key
        if not api_key:
            print("[GeminiEvaluator] Warning: GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name or self.config.gemini_model or "gemini-3.6-flash"

    def evaluate_audio_branch(self, turn_id: int, audio_clip_path: Path) -> AudioBranchOutput:
        """
        Branch 1: Audio Branch - uploads audio WAV clip and evaluates speech & tone.
        """
        print(f"[GeminiEvaluator] [Audio Branch] Uploading clip for Turn {turn_id}: {audio_clip_path.name}")
        uploaded_file = self.client.files.upload(file=str(audio_clip_path))

        prompt = f"Analyze turn {turn_id} candidate audio clip. Extract transcript, vocal confidence, hesitation, emotion, filler count, and speech delivery notes."

        interaction = self.client.interactions.create(
            model=self.model_name,
            system_instruction=AUDIO_SYSTEM_PROMPT,
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
        candidate_transcript: str
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

        interaction = self.client.interactions.create(
            model=self.model_name,
            system_instruction=TECHNICAL_SYSTEM_PROMPT,
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
        turns_data: List[Dict[str, Any]],
        audio_outputs: List[AudioBranchOutput],
        technical_outputs: List[TechnicalBranchOutput]
    ) -> CandidateReportPayload:
        """
        Branch 3: Combine Branch - fuses Audio & Technical branch outputs into full CandidateReportPayload.
        """
        print(f"[GeminiEvaluator] [Combine Branch] Synthesizing final report payload for session {session_id}")

        turn_payloads = []
        for i, turn in enumerate(turns_data):
            t_id = turn.get("turn_id", i + 1)
            aud = next((a for a in audio_outputs if a.turn_id == t_id), None)
            tec = next((t for t in technical_outputs if t.turn_id == t_id), None)

            turn_payloads.append({
                "turn_id": t_id,
                "topic": turn.get("topic", "General"),
                "question_text": turn.get("question_text", ""),
                "original_transcript": turn.get("candidate_transcript", ""),
                "audio_eval": aud.model_dump() if aud else {},
                "technical_eval": tec.model_dump() if tec else {}
            })

        combine_input_prompt = f"""
Session ID: {session_id}
Turn Analysis Data:
{json.dumps(turn_payloads, indent=2)}

Please synthesize the final comprehensive CandidateReportPayload adhering strictly to the JSON schema.
Ensure all overall scores, technical pillars, turn evaluations, and hiring signals are populated accurately.
"""

        interaction = self.client.interactions.create(
            model=self.model_name,
            system_instruction=COMBINE_SYSTEM_PROMPT,
            input=combine_input_prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": CandidateReportPayload.model_json_schema()
            }
        )

        output_dict = json.loads(interaction.output_text)
        return CandidateReportPayload.model_validate(output_dict)
