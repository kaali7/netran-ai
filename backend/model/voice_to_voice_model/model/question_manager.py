"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: question_manager.py
Description: State machine and dynamic branching engine tracking question progression,
             scoring keyword density on STT candidate transcripts, and selecting
             adaptive follow-up branches (strong_followup, weak_followup, next_topic).
"""

import re

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
    def __init__(self, questions: list[InterviewQuestionInput]):
        self.questions = questions
        self.current_index = 0
        # State phases: 'ICEBREAKER' -> 'TECHNICAL' -> 'LAST_QUESTION' -> 'COMPLETED'
        self.phase = "ICEBREAKER"
        self.icebreaker_turn_count = 0
        self.retries_on_current_q = 0

    def get_current_question(self) -> InterviewQuestionInput | None:
        """Returns the current active question object or None if sequence is complete."""
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def get_next_question(self) -> InterviewQuestionInput | None:
        """Returns the next question object in sequence or None if at the end."""
        if self.current_index + 1 < len(self.questions):
            return self.questions[self.current_index + 1]
        return None

    def is_on_last_question(self) -> bool:
        """Returns True if pointer is currently on the final question in sequence."""
        return self.current_index == len(self.questions) - 1

    def is_finished(self) -> bool:
        """Returns True if all questions in the sequence have been processed or phase is COMPLETED."""
        return self.current_index >= len(self.questions) or self.phase == "COMPLETED"

    def advance_question(self) -> str:
        """
        Advances question index safely and updates phase state.
        Returns status: 'advanced', 'reached_last', or 'completed'
        """
        self.retries_on_current_q = 0

        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            if self.is_on_last_question():
                self.phase = "LAST_QUESTION"
                return "reached_last"
            return "advanced"
        else:
            self.phase = "COMPLETED"
            return "completed"

    def is_candidate_requesting_skip(self, transcript: str) -> bool:
        """Detects if candidate is asking to skip or move to the next question."""
        skip_pattern = re.compile(
            r"\b(don'?t know|no idea|not sure|didn'?t study|skip|next question|pass|move on)\b", 
            re.IGNORECASE
        )
        clean_text = (transcript or "").lower().strip()
        return bool(skip_pattern.search(clean_text))

    def classify_turn_intent(self, transcript: str, was_barge_in: bool = False) -> str:
        """
        Classifies candidate turns into Universal Intent Taxonomy:
        TECHNICAL_ANSWER, ICEBREAKER, CANDIDATE_META_QUERY, SKIP_REQUEST, AUDIO_CHECK_OR_PAUSE, BARGE_IN_INTERRUPTION, END_INTERVIEW_REQUEST
        """
        if was_barge_in:
            return "BARGE_IN_INTERRUPTION"

        clean = (transcript or "").lower().strip()

        # 0. Candidate explicitly requesting to stop the interview
        # Avoid standalone words like 'end' or 'stop' to prevent false positives with 'back-end', 'front-end', or 'stop working'
        stop_pattern = re.compile(
            r"\b(quit|terminate|bye|goodbye|stop the interview|stop this interview|end the interview|i want to stop|i need to stop|let's stop)\b", 
            re.IGNORECASE
        )
        if stop_pattern.search(clean):
            return "END_INTERVIEW_REQUEST"

        # 1. Candidate Meta-Intent Override (Explicit Skip / Pass)
        if self.is_candidate_requesting_skip(clean):
            return "SKIP_REQUEST"

        # 2. Candidate meta questions about Eva / Role / Location / Origin / Process
        meta_pattern = re.compile(
            r"\b(who are you|what is your name|are you real|where are you from|who created you|tell me about yourself|where do you live|what is your role|are you an? ai|how many questions)\b", 
            re.IGNORECASE
        )
        if meta_pattern.search(clean):
            return "CANDIDATE_META_QUERY"

        # 3. Audio / Connectivity checks
        audio_check_patterns = [
            r"\bcan\s+you\s+hear\s+me\b",
            r"\bam\s+i\s+audible\b",
            r"\bmic\s+check\b",
            r"\bare\s+you\s+there\b",
            r"\bcan\s+you\s+listen\b"
        ]
        if any(re.search(pat, clean) for pat in audio_check_patterns):
            return "AUDIO_CHECK_OR_PAUSE"

        # 4. Thinking pauses / Filler remarks
        pause_patterns = [
            r"\bgive\s+me\s+a\s+(second|moment|min|minute)\b",
            r"\blet\s+me\s+think\b",
            r"\bhold\s+on\b",
            r"\bgood\s+question\b",
            r"\bthat'?s\s+a\s+tough\s+one\b",
            r"\bjust\s+a\s+sec\b"
        ]
        if any(re.search(pat, clean) for pat in pause_patterns):
            return "AUDIO_CHECK_OR_PAUSE"

        # 5. Icebreaker Phase
        if self.phase == "ICEBREAKER":
            return "ICEBREAKER"

        return "TECHNICAL_ANSWER"

    def calculate_keyword_density(self, transcript: str, keywords: list[str]) -> float:
        """Calculates match density of expected keywords in candidate transcript."""
        if not keywords:
            return 0.0
        clean_tx = (transcript or "").lower()
        matches = sum(1 for kw in keywords if kw.lower() in clean_tx)
        return matches / len(keywords)

    def evaluate_transcript(self, transcript: str) -> str:
        """
        Evaluates turn intent and determines branching without losing question context.
        Meta intents (CANDIDATE_META_QUERY, AUDIO_CHECK_OR_PAUSE) return immediately without advancing questions.
        """
        if self.phase == "COMPLETED":
            return "interview_completed"

        raw_intent = self.classify_turn_intent(transcript)

        if raw_intent == "END_INTERVIEW_REQUEST":
            self.phase = "COMPLETED"
            return "interview_completed"

        # Meta questions / audio checks never advance question index or phase
        if raw_intent in ("CANDIDATE_META_QUERY", "interviewer_meta"):
            return "interviewer_meta"
        if raw_intent in ("AUDIO_CHECK_OR_PAUSE", "audio_check"):
            return "audio_check"

        # Handle Icebreaker Phase Transition
        if self.phase == "ICEBREAKER" or raw_intent == "ICEBREAKER":
            self.icebreaker_turn_count += 1
            if self.icebreaker_turn_count >= 1:
                self.phase = "LAST_QUESTION" if len(self.questions) == 1 else "TECHNICAL"
            return "icebreaker_response"

        # Explicit Candidate Skip
        if raw_intent in ("SKIP_REQUEST", "next_topic"):
            status = self.advance_question()
            return "interview_completed" if status == "completed" else "next_topic"

        current_q = self.get_current_question()
        if not current_q:
            self.phase = "COMPLETED"
            return "interview_completed"

        match_score = self.calculate_keyword_density(transcript, current_q.expected_keywords or [])

        if match_score >= 0.50 and current_q.followup_if_strong:
            return "strong_followup"
        elif match_score < 0.20:
            self.retries_on_current_q += 1
            # Auto-advance after 2 weak attempts to prevent repetition loops
            if self.retries_on_current_q >= 2:
                status = self.advance_question()
                return "interview_completed" if status == "completed" else "next_topic"
            
            return "weak_followup" if current_q.followup_if_weak else "next_topic"
        else:
            status = self.advance_question()
            return "interview_completed" if status == "completed" else "next_topic"

    def format_prompt_context(
        self, 
        branch_taken: str, 
        candidate_transcript: str,
        resume_highlights: dict | None = None
    ) -> tuple[str, str]:
        llm_prompt, target_q = self._format_prompt_context_internal(branch_taken, candidate_transcript, resume_highlights)
        llm_prompt += "\n\nFORMAT REQUIREMENT: You MUST respond starting EXACTLY with TONE: <tone> and SPEAK: <text>"
        return llm_prompt, target_q

    def _format_prompt_context_internal(
        self, 
        branch_taken: str, 
        candidate_transcript: str,
        resume_highlights: dict | None = None
    ) -> tuple[str, str]:
        """
        Constructs natural LLM instructions for Qwen 2.5 3B and returns:
        (llm_prompt_string, logged_target_question_text)
        """
        current_q = self.get_current_question()

        # 1. FINAL INTERVIEW CONCLUSION
        if branch_taken == "interview_completed":
            closing_text = (
                "That concludes our technical evaluation for today! "
                "Thank you so much for your time, and we will follow up with detailed feedback shortly."
            )
            instruction = (
                f"React warmly and professionally to the candidate's last response (or request to finish). "
                f"Then conclude the interview smoothly by saying: '{closing_text}'"
            )
            return f"Candidate Final Answer: '{candidate_transcript}'\nInstruction: {instruction}", closing_text

        target_logged_q = current_q.question_text if current_q else ""

        # 2. ICEBREAKER PHASE
        if branch_taken == "icebreaker_response":
            instruction = (
                "React warmly to the candidate's introduction in 1 short sentence, "
                f"then smoothly pivot to ask this question in your own natural words: '{target_logged_q}'"
            )
            return f"Candidate Intro: '{candidate_transcript}'\nInstruction: {instruction}", target_logged_q

        # 3. INTERVIEWER META QUESTIONS (Role, Location, Identity)
        if branch_taken == "interviewer_meta":
            instruction = (
                f"The candidate asked a meta question: '{candidate_transcript}'. "
                f"Answer their question directly and warmly in 1 short sentence (you are Eva, an AI technical interviewer), then ask if they are ready to return to: '{target_logged_q}'."
            )
            return f"Instruction: {instruction}", target_logged_q

        # 4. AUDIO & PAUSE CHECKS
        if branch_taken == "audio_check":
            instruction = "Reassure the candidate warmly in 1 short sentence (e.g., 'Loud and clear! Go right ahead.')"
            return f"Candidate: '{candidate_transcript}'\nInstruction: {instruction}", target_logged_q

        if branch_taken == "thinking_pause":
            instruction = "Acknowledge empathetically (e.g., 'Take your time, no rush at all!') and wait."
            return f"Candidate: '{candidate_transcript}'\nInstruction: {instruction}", target_logged_q

        # 5. EXPLICIT SKIP
        if branch_taken == "next_topic" and self.is_candidate_requesting_skip(candidate_transcript):
            next_q = self.get_current_question()
            target_q = next_q.question_text if next_q else target_logged_q
            instruction = (
                f"The candidate wants to skip or doesn't know the answer.\n"
                f"Briefly reassure them empathetically (e.g., 'No worries at all!'), then smoothly pivot to ask this question in your own natural words: '{target_q}'"
            )
            return f"Candidate Answer: '{candidate_transcript}'\nInstruction: {instruction}", target_q

        # 6. TECHNICAL EVALUATION BRANCHES
        if branch_taken == "strong_followup":
            target_q = current_q.followup_if_strong if (current_q and current_q.followup_if_strong) else target_logged_q
            resume_ref = ""
            if resume_highlights:
                relevant_achievement = resume_highlights.get("key_achievements", [None])[0]
                if relevant_achievement:
                    resume_ref = f" (Note: their resume confirms: '{relevant_achievement[:80]}...')"
            instruction = (
                f"The candidate just said: '{candidate_transcript[:60]}...'.{resume_ref}\n"
                f"Briefly validate their answer in 1 warm sentence referencing what they just said, "
                f"then ask this follow-up question in your own words: '{target_q}'.\n"
                f"CRITICAL: Ask ONLY this single question. Do NOT add any bridging questions of your own."
            )
        elif branch_taken == "weak_followup":
            target_q = current_q.followup_if_weak if (current_q and current_q.followup_if_weak) else target_logged_q
            instruction = (
                f"Acknowledge sympathetically that this topic is tricky, then ask this simplifying follow-up in your own words: '{target_q}'. "
                f"CRITICAL: Ask ONLY this single question. Do NOT add any extra questions."
            )
        else:  # standard next_topic
            next_q = self.get_current_question()
            target_q = next_q.question_text if next_q else target_logged_q
            instruction = (
                f"The candidate just said: '{candidate_transcript[:60]}...'.\n"
                f"Briefly acknowledge their point (1 sentence), then naturally pivot to ask this question in your own words: '{target_q}'.\n"
                f"CRITICAL: Ask ONLY this single question."
            )

        llm_prompt = (
            f"Candidate Answer: '{candidate_transcript}'\n"
            f"Instruction: {instruction}\n"
            f"Constraint: Sound natural and concise. Keep SPEAK: under 35 words."
        )

        return llm_prompt, target_q


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
