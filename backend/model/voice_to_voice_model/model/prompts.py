"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: prompts.py
Description: Centralized system prompts, formatting rules, dynamic prompt builders, 
             and Whisper initial prompts for Stage 3 voice execution.
"""

from typing import Dict, Optional

# =====================================================================
# 1. DEFAULT FALLBACK SYSTEM PROMPT
# =====================================================================

DEFAULT_EVA_SYSTEM_PROMPT = (
    "You are Eva, a sharp and professional lead technical interviewer "
    "conducting a structured, turn-by-turn live technical interview.\n\n"
    "MANDATORY RESPONSE FORMAT — YOU MUST FOLLOW THIS EVERY SINGLE TURN:\n\n"
    "<think>\n"
    "[Your brief internal reasoning: What did the candidate say? "
    "How strong was their answer? What is the ideal follow-up?]\n"
    "</think>\n"
    "<speak>\n"
    "[ONLY the words Eva speaks aloud. 1-2 sentences maximum. "
    "Plain English only, no markdown, no action tags.]\n"
    "</speak>\n\n"
    "RULES:\n"
    "1. ALWAYS output both <think> and <speak> blocks — no exceptions.\n"
    "2. The <think> block is hidden from the candidate and NEVER spoken.\n"
    "3. The <speak> block is the ONLY text converted to audio.\n"
    "4. Inside <speak>: never use *, **, #, backticks, or [action tags].\n"
    "5. Inside <speak>: speak naturally. Ask exactly ONE question at a time.\n"
    "6. Never output any text outside these two tags."
)

# Default system payload fallback
SYSTEM_PROMPT: Dict[str, str] = {
    "role": "system",
    "content": DEFAULT_EVA_SYSTEM_PROMPT
}


# =====================================================================
# 2. FASTER-WHISPER DOMAIN VOCABULARY
# =====================================================================

WHISPER_INITIAL_PROMPT = (
    "Python, asyncio, FastAPI, PostgreSQL, B-Tree, Redis, gRPC, Protobuf, HTTP/2, HTTP/1.1, "
    "Docker, Kubernetes, Kafka, System Design, REST APIs, Microservices, Data Structures, "
    "Algorithms, React.js, Next.js, TypeScript, Tailwind CSS, Cache-Aside, Token Bucket, "
    "Sliding Window, Sequential Scan, Query Planner, Mock Interview, Candidate Response."
)


# =====================================================================
# 3. DYNAMIC PROMPT BUILDERS
# =====================================================================

def get_system_prompt(custom_prompt_text: Optional[str] = None) -> Dict[str, str]:
    """
    Constructs the Ollama system prompt payload. Ingests Stage 2 system_prompt.txt 
    if provided and appends mandatory low-latency voice guardrails.
    """
    if custom_prompt_text and custom_prompt_text.strip():
        base_text = custom_prompt_text.strip()
        voice_guardrails = (
            "\n\nMANDATORY RESPONSE FORMAT:\n"
            "<think>[Internal reasoning — never spoken]</think>\n"
            "<speak>[Spoken reply — 1-2 sentences, plain English only]</speak>\n"
            "Always output both tags. Never output text outside these tags."
        )
        full_content = base_text + voice_guardrails
    else:
        full_content = DEFAULT_EVA_SYSTEM_PROMPT

    return {
        "role": "system",
        "content": full_content
    }


def build_question_evaluation_prompt(
    topic: str,
    target_question: str,
    candidate_transcript: str,
    instruction: str
) -> str:
    """
    Formats turn-level evaluation context fed to Qwen2.5 during the live interview loop.
    """
    return (
        f"CURRENT TOPIC: {topic}\n"
        f"TARGET QUESTION: \"{target_question}\"\n"
        f"CANDIDATE TRANSCRIPT: \"{candidate_transcript}\"\n\n"
        f"INSTRUCTION: {instruction}\n"
        f"REMINDER: You must output both <think> and <speak> tags as per system prompt."
    )