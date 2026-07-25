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

from .report_schema import (
    AudioBranchOutput,
    TechnicalBranchOutput,
    CandidateReportPayload,
    TurnAnalysis,
    PillarScore
)

backend_dir = Path(__file__).resolve().parents[3]
load_dotenv(backend_dir / ".env")


AUDIO_SYSTEM_PROMPT = """
You are an expert Acoustic & Multimodal Speech Evaluation AI.
Your task is to analyze candidate audio recordings from technical interviews.
You must:
1. Listen closely to the audio clip and provide an accurate, refined transcription (gemini_verified_transcript).
2. Evaluate vocal confidence score (1 to 10 scale, where 1 is extremely hesitant/timid and 10 is confident/clear).
3. Identify hesitation level ('Low', 'Medium', or 'High').
4. Identify primary emotional state ('Calm', 'Stressed', 'Uncertain', or 'Confident').
5. Count approximate filler words (um, ah, like, you know, etc.).
6. Provide concise qualitative audio notes on speech pacing, vocal clarity, and delivery tone.
"""

TECHNICAL_SYSTEM_PROMPT = """
You are a Senior Technical Interview Evaluator.
Your task is to evaluate candidate responses against technical requirements and job rubrics.
You must:
1. Assess technical accuracy score (1 to 10 scale).
2. Identify key technical concepts that were missing or insufficiently explained in the response.
3. Provide concise technical analysis notes highlighting strengths and gaps.
"""

COMBINE_SYSTEM_PROMPT = """
You are an Executive Hiring Assessment Engine for Netran AI.
Your task is to fuse multimodal audio tone analysis with technical content accuracy across interview turns into a unified, structured evaluation report.
You must:
1. Compute aggregated technical score (0-100) and vocal confidence score (0-100).
2. Determine overall hiring signal ('Strong Hire', 'Hire', 'Lean No Hire', 'No Hire').
3. Construct core technical pillar scores and summaries.
4. Synthesize per-turn combined analysis items fusing both technical and acoustic metrics.
5. Write a comprehensive executive summary for hiring managers detailing candidate performance, strengths, and recommended focus areas.
"""


class GeminiMultimodalEvaluator:
    def __init__(self, model_name: str = "gemini-3.6-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[GeminiEvaluator] Warning: GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

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
