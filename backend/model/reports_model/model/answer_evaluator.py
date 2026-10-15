"""
Netran AI — Stage 4: Post-Session Evaluation & Report Generation Engine
Module: answer_evaluator.py
Description: High-speed technical answer intelligence evaluator using Groq cloud LLM
             (`openai/gpt-oss-120b`) with resilient automatic fallback to local Ollama
             and offline deterministic evaluation rules.
"""

import json
import logging
import os
import re
from typing import Any

from .schemas import (
    BehavioralFlag,
    CandidateFeedback,
    PillarScore,
    TechnicalBranchOutput,
)

logger = logging.getLogger("netran.stage4.evaluator")

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import ollama
except ImportError:
    ollama = None


class AnswerEvaluator:
    """Evaluates candidate technical answers against Stage 1/2 rubrics with Groq & Ollama."""

    def __init__(
        self,
        groq_api_key: str | None = None,
        groq_model: str | None = None,
        ollama_model: str | None = None,
    ):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.groq_model = groq_model or os.getenv("GROQ_EVALUATION_MODEL", "openai/gpt-oss-120b")
        self.ollama_model = ollama_model or os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

        self.groq_client = None
        if self.groq_api_key and Groq is not None:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
            except Exception as e:
                logger.warning(f"[AnswerEvaluator] Failed to initialize Groq client: {e}")

    def evaluate_turn(
        self,
        turn_id: int,
        topic: str,
        question_text: str,
        candidate_transcript: str,
        resume_text: str = "",
        jd_rubric_text: str = "",
    ) -> TechnicalBranchOutput:
        """
        Evaluates a single interview turn's technical answer accuracy, depth, and missing concepts.
        """
        # 1. Quick check for empty or abort answer
        lower_trans = (candidate_transcript or "").strip().lower()
        if not lower_trans or lower_trans in ["eva stop", "stop", "stop the interview", "can we stop the interview right now?"]:
            return TechnicalBranchOutput(
                turn_id=turn_id,
                technical_score=1,
                missing_concepts=["Response omitted or session prematurely halted."],
                technical_notes="Candidate did not provide a technical explanation or requested to stop the interview.",
                resume_verification_note="Turn halted by candidate.",
            )

        # 2. Try Groq Cloud Evaluation
        if self.groq_client:
            try:
                return self._evaluate_with_groq(
                    turn_id=turn_id,
                    topic=topic,
                    question_text=question_text,
                    candidate_transcript=candidate_transcript,
                    resume_text=resume_text,
                    jd_rubric_text=jd_rubric_text,
                )
            except Exception as exc:
                logger.warning(f"[AnswerEvaluator] Groq evaluation failed for turn {turn_id}: {exc}. Trying Ollama...")

        # 3. Try Local Ollama Fallback
        if ollama is not None:
            try:
                return self._evaluate_with_ollama(
                    turn_id=turn_id,
                    topic=topic,
                    question_text=question_text,
                    candidate_transcript=candidate_transcript,
                    resume_text=resume_text,
                    jd_rubric_text=jd_rubric_text,
                )
            except Exception as exc:
                logger.warning(f"[AnswerEvaluator] Ollama evaluation failed for turn {turn_id}: {exc}. Using rule fallback...")

        # 4. Deterministic Rule Fallback (Guaranteed to succeed)
        return self._evaluate_rule_fallback(
            turn_id=turn_id,
            topic=topic,
            question_text=question_text,
            candidate_transcript=candidate_transcript,
        )

    def _evaluate_with_groq(
        self,
        turn_id: int,
        topic: str,
        question_text: str,
        candidate_transcript: str,
        resume_text: str = "",
        jd_rubric_text: str = "",
    ) -> TechnicalBranchOutput:
        """Evaluates turn with Groq API."""
        prompt = f"""You are Eva, an expert technical interviewer evaluating a mock interview answer.
Assess the candidate answer based on technical correctness, depth, and the provided rubric.

TOPIC: {topic}
INTERVIEWER QUESTION: {question_text}
CANDIDATE TRANSCRIPT: {candidate_transcript}
JOB RUBRIC / EXPECTATIONS: {jd_rubric_text[:600] if jd_rubric_text else 'Standard engineering best practices'}
CANDIDATE RESUME CONTEXT: {resume_text[:400] if resume_text else 'None supplied'}

Return a valid JSON object with EXACTLY these keys:
{{
  "technical_score": <integer from 1 to 10>,
  "missing_concepts": [<list of 1-4 key technical concepts omitted or weakly answered>],
  "technical_notes": "<concise 2-3 sentence technical critique explaining what was strong and what was lacking>",
  "resume_verification_note": "<short note evaluating whether this supports claimed skills, or 'Supported' / 'No resume attached'>"
}}"""

        response = self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=[
                {"role": "system", "content": "You evaluate technical interview responses rigorously and objectively. Always respond with pure JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=600,
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        score = max(1, min(10, int(data.get("technical_score", 5))))
        missing = data.get("missing_concepts", [])
        if isinstance(missing, str):
            missing = [missing]

        return TechnicalBranchOutput(
            turn_id=turn_id,
            technical_score=score,
            missing_concepts=missing,
            technical_notes=data.get("technical_notes", "Candidate provided response evaluated against domain benchmarks."),
            resume_verification_note=data.get("resume_verification_note", "Evaluated against role rubric."),
        )

    def _evaluate_with_ollama(
        self,
        turn_id: int,
        topic: str,
        question_text: str,
        candidate_transcript: str,
        resume_text: str = "",
        jd_rubric_text: str = "",
    ) -> TechnicalBranchOutput:
        """Evaluates turn with local Ollama daemon."""
        prompt = f"""You are Eva, an expert technical interviewer. Evaluate this answer in JSON format:
TOPIC: {topic}
QUESTION: {question_text}
ANSWER: {candidate_transcript}

Respond ONLY in JSON with format:
{{
  "technical_score": <1-10>,
  "missing_concepts": ["concept1", "concept2"],
  "technical_notes": "critique text",
  "resume_verification_note": "verification text"
}}"""

        resp = ollama.chat(
            model=self.ollama_model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.1, "num_predict": 400},
        )
        content = resp["message"]["content"]
        data = json.loads(content)

        return TechnicalBranchOutput(
            turn_id=turn_id,
            technical_score=max(1, min(10, int(data.get("technical_score", 5)))),
            missing_concepts=data.get("missing_concepts", []),
            technical_notes=data.get("technical_notes", "Evaluated via local Ollama engine."),
            resume_verification_note=data.get("resume_verification_note", "Verified."),
        )

    def _evaluate_rule_fallback(
        self,
        turn_id: int,
        topic: str,
        question_text: str,
        candidate_transcript: str,
    ) -> TechnicalBranchOutput:
        """Deterministic rule fallback when external LLMs are unreachable."""
        words = re.findall(r"\b\w+\b", candidate_transcript or "")
        word_count = len(words)

        if word_count < 10:
            score = 3
            notes = "Brief response providing minimal technical architecture or reasoning details."
            missing = ["In-depth technical rationale", "Concrete architectural examples"]
        elif word_count < 35:
            score = 6
            notes = f"Candidate covered baseline points for {topic} but lacked deep system design implementation depth."
            missing = ["Edge-case handling", "Scale and performance considerations"]
        else:
            score = 8
            notes = f"Thorough explanation demonstrating practical grasp of {topic} domain concepts."
            missing = ["Quantitative performance metrics"]

        return TechnicalBranchOutput(
            turn_id=turn_id,
            technical_score=score,
            missing_concepts=missing,
            technical_notes=notes,
            resume_verification_note="Evaluated via rule heuristics.",
        )

    def evaluate_combine_branch(
        self,
        session_id: str,
        turns_data: list[dict[str, Any]],
        audio_outputs: list[Any],
        technical_outputs: list[TechnicalBranchOutput],
        resume_text: str = "",
        jd_rubric_text: str = "",
    ) -> dict[str, Any]:
        """
        Synthesizes the overall executive report, pillar scores, hiring recommendation,
        and candidate growth roadmap.
        """
        # Calculate aggregate numerical scores
        tech_scores = [t.technical_score for t in technical_outputs] if technical_outputs else [5]
        vocal_scores = [getattr(a, "vocal_confidence_score", 6) for a in audio_outputs] if audio_outputs else [6]

        overall_tech = round((sum(tech_scores) / (len(tech_scores) * 10.0)) * 100)
        overall_vocal = round((sum(vocal_scores) / (len(vocal_scores) * 10.0)) * 100)

        # Determine hiring recommendation
        if overall_tech >= 85 and overall_vocal >= 70:
            hiring_signal = "Strong Hire"
        elif overall_tech >= 70:
            hiring_signal = "Hire"
        elif overall_tech >= 50:
            hiring_signal = "Lean No Hire"
        else:
            hiring_signal = "No Hire"

        # Detect behavioral flags (e.g. abort requests)
        behavioral_flags: list[BehavioralFlag] = []
        for turn in turns_data:
            trans = (turn.get("candidate_transcript") or "").lower()
            t_id = turn.get("turn_id", 1)
            if "stop" in trans and ("interview" in trans or "can we stop" in trans or "eva, stop" in trans):
                behavioral_flags.append(
                    BehavioralFlag(
                        type="SESSION_ABORT_REQUEST",
                        severity="MEDIUM",
                        turn_id=t_id,
                        description="Candidate verbally requested to end or abort the interview session.",
                    )
                )

        # Build Domain Technical Pillars
        # Group turns by topic
        topic_scores: dict[str, list[int]] = {}
        for t_data, t_out in zip(turns_data, technical_outputs):
            topic = t_data.get("topic", "General Technical")
            topic_scores.setdefault(topic, []).append(t_out.technical_score)

        pillars: list[PillarScore] = []
        for topic, scores in topic_scores.items():
            p_score = round((sum(scores) / (len(scores) * 10.0)) * 100)
            if p_score >= 80:
                summary = f"Strong command of {topic} principles with articulate problem decomposition."
            elif p_score >= 60:
                summary = f"Working knowledge of {topic} demonstrated; would benefit from deeper systems focus."
            else:
                summary = f"Foundational gaps identified in {topic}; recommend targeted concept review."

            pillars.append(PillarScore(pillar_name=topic, score=p_score, summary=summary))

        if not pillars:
            pillars.append(PillarScore(pillar_name="Core Technical Architecture", score=overall_tech, summary="Overall technical domain assessment."))

        # Compile Candidate Feedback
        all_missing = []
        for t in technical_outputs:
            all_missing.extend(t.missing_concepts)

        # Unique missing concepts
        unique_missing = list(dict.fromkeys(all_missing))[:5]

        key_strengths = []
        if overall_tech >= 70:
            key_strengths.append("Demonstrated solid problem-solving foundation across evaluated technical domains.")
        if overall_vocal >= 70:
            key_strengths.append("Articulate vocal delivery with steady speech pace and clear communication.")
        else:
            key_strengths.append("Willingness to address unfamiliar architecture challenges under interview conditions.")

        primary_growth = []
        if overall_tech < 75:
            primary_growth.append("Deepen hands-on familiarity with distributed systems, telemetry, and platform bottlenecks.")
        if overall_vocal < 65:
            primary_growth.append("Practice structured verbal delivery (STAR format) to reduce pauses during technical explanations.")

        recommended_study = unique_missing if unique_missing else [
            "Distributed Systems Observability & Telemetry",
            "Real-Time WebSocket & Audio Streaming Architecture",
            "High-Throughput Database Caching Strategies",
        ]

        feedback = CandidateFeedback(
            key_strengths=key_strengths,
            primary_growth_areas=primary_growth,
            recommended_topics_to_study=recommended_study,
        )

        executive_summary = (
            f"The candidate completed an {len(turns_data)}-turn technical mock interview session. "
            f"Demonstrated an overall technical score of {overall_tech}/100 and vocal delivery confidence of {overall_vocal}/100. "
            f"Overall evaluation signal is '{hiring_signal}'. "
            f"Key growth focus should center on {', '.join(recommended_study[:2])}."
        )

        return {
            "overall_technical_score": overall_tech,
            "overall_vocal_confidence_score": overall_vocal,
            "overall_hiring_signal": hiring_signal,
            "executive_summary": executive_summary,
            "technical_pillars": pillars,
            "behavioral_flags": behavioral_flags,
            "candidate_feedback": feedback,
        }
