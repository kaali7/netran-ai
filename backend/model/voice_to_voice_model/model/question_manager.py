"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: question_manager.py
Description: State machine and dynamic branching engine tracking question progression,
             scoring keyword density on STT candidate transcripts, and selecting
             adaptive follow-up branches (strong_followup, weak_followup, next_topic).
"""

import re
from typing import List, Optional

try:
    from .schemas import InterviewQuestionInput
except ImportError:
    try:
        from model.voice_to_voice_model.model.schemas import InterviewQuestionInput
    except ImportError:
        from schemas import InterviewQuestionInput


class QuestionManager:
    """
    Manages the question sequence state, computes transcript keyword coverage,
    and determines adaptive branching paths for Stage 3 voice interviews.
    """
    def __init__(self, questions: List[InterviewQuestionInput]):
        self.questions = questions
        self.current_index = 0

    def get_current_question(self) -> Optional[InterviewQuestionInput]:
        """Returns the current active question object or None if sequence is complete."""
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def is_finished(self) -> bool:
        """Returns True if all questions in the sequence have been processed."""
        return self.current_index >= len(self.questions)

    def evaluate_transcript(self, transcript: str) -> str:
        """
        Evaluates candidate STT transcript against current question's expected keywords.

        Rules:
        - Score >= 50% keyword match & followup_if_strong exists -> "strong_followup"
        - Score < 20% keyword match & followup_if_weak exists   -> "weak_followup"
        - Otherwise                                             -> "next_topic"

        :param transcript: Candidate's spoken transcript text.
        :return: Branch identifier ("strong_followup" | "weak_followup" | "next_topic").
        """
        q = self.get_current_question()
        if not q:
            return "next_topic"

        normalized_transcript = (transcript or "").strip().lower()

        keywords = q.expected_keywords or []
        if not keywords:
            return "next_topic"

        matched_count = 0
        for kw in keywords:
            kw_clean = kw.strip().lower()
            if not kw_clean:
                continue
            # Regex word-boundary or simple substring match
            pattern = re.escape(kw_clean)
            if re.search(pattern, normalized_transcript):
                matched_count += 1

        match_ratio = matched_count / len(keywords)

        if match_ratio >= 0.50 and q.followup_if_strong:
            return "strong_followup"
        elif match_ratio < 0.20 and q.followup_if_weak:
            return "weak_followup"
        else:
            return "next_topic"

    def format_prompt_context(self, branch: str, transcript: str) -> str:
        """
        Formats instructions and context for Ollama LLM prompt generation
        based on evaluation branch outcome.

        :param branch: Branch outcome ("strong_followup", "weak_followup", "next_topic").
        :param transcript: Candidate transcript text.
        :return: Context instruction string for LLM.
        """
        q = self.get_current_question()
        if not q:
            return f"Candidate transcript: '{transcript}'. Session is concluding."

        if branch == "strong_followup" and q.followup_if_strong:
            return (
                f"Candidate answer to '{q.question_text}': '{transcript}'.\n"
                f"Evaluation: Strong answer (high keyword coverage).\n"
                f"Follow-up instruction: Ask this escalating probe next: \"{q.followup_if_strong}\""
            )
        elif branch == "weak_followup" and q.followup_if_weak:
            return (
                f"Candidate answer to '{q.question_text}': '{transcript}'.\n"
                f"Evaluation: Weak or vague answer (low keyword coverage).\n"
                f"Follow-up instruction: Ask this simplifying clarifying question next: \"{q.followup_if_weak}\""
            )
        else:
            # Next topic branch
            next_idx = self.current_index + 1
            if next_idx < len(self.questions):
                next_q = self.questions[next_idx]
                return (
                    f"Candidate answer: '{transcript}'.\n"
                    f"Evaluation: Topic complete. Transition concisely and ask the next question: \"{next_q.question_text}\""
                )
            else:
                return (
                    f"Candidate answer: '{transcript}'.\n"
                    f"Evaluation: Final topic complete. Wrap up the interview professionally in 1 short sentence."
                )

    def advance_question(self):
        """Advances question index pointer to the next topic in sequence."""
        self.current_index += 1


if __name__ == "__main__":
    print("Testing QuestionManager Module...")
    sample_qs = [
        InterviewQuestionInput(
            id=1,
            topic="AsyncIO",
            question_text="How does event loop work?",
            expected_keywords=["event loop", "asyncio", "coroutine"],
            followup_if_strong="How do you handle blocking calls in executor?",
            followup_if_weak="What is the difference between time.sleep and asyncio.sleep?"
        )
    ]
    qm = QuestionManager(sample_qs)
    
    strong_ans = "The asyncio event loop runs single-threaded coroutines using asyncio non-blocking routines."
    weak_ans = "It runs things fast in parallel."

    print("Strong Evaluation:", qm.evaluate_transcript(strong_ans))
    print("Weak Evaluation:", qm.evaluate_transcript(weak_ans))
