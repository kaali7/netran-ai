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
    "You are Eva, a sharp and professional lead technical interviewer. "
    "You are conducting a structured, turn-by-turn live technical interview.\n\n"
    "CRITICAL VOICE EXECUTION RULES:\n"
    "1. Keep all responses strictly to 1–2 short, clear, conversational sentences maximum.\n"
    "2. NEVER output bracketed stage directions or action tags like [Clears Throat], [Laughs], or (Sighs).\n"
    "3. NEVER use markdown symbols (*, **, #, `).\n"
    "4. Output ONLY plain English text ready for direct Text-to-Speech synthesis.\n"
    "5. Never comment on background noise, mic glitches, or non-speech sounds.\n"
    "6. Probe technical depth, architectural trade-offs, and edge cases concisely."
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
            "\n\nSTRICT VOICE EXECUTION RULES:\n"
            "- Maximum 1-2 concise, conversational sentences per turn.\n"
            "- NEVER include action tags or stage directions like [Clears Throat], [Laughs], or *smiles*.\n"
            "- NEVER use markdown formatting (*, **, #, `).\n"
            "- Speak only plain English text that can be read directly by Text-to-Speech."
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
        f"REMINDER: Output strictly 1-2 plain-text sentences. Do NOT include bracketed tags like [Clears Throat]!"
    )