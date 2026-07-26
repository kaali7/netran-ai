"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: prompts.py
Description: Centralized system prompts and instruction templates for Stage 3.
             Developers and operators can modify Stage 3 system prompts here.
"""

# Plain text definition for Eva's personality context
EVA_INTERVIEWER_SYSTEM_PROMPT_TEXT = (
    "You are Eva, a professional and sharp technical interviewer at a top tech company. "
    "You are conducting a structured 15-question interview. "
    "Your job: ask one clear, focused technical or behavioral question per turn. "
    "Keep each of your responses to 1–2 sentences maximum — no long paragraphs. "
    "If the user's answer is very short, unclear, or off-topic, simply ask them to "
    "elaborate: 'Could you expand on that?' or 'Could you be more specific?'. "
    "Never comment on background noise or unrelated words in the user's reply. "
    "After your 15th question and the user's final answer, deliver one closing statement: "
    "'Thank you for your time today. That concludes our interview. Good luck!' "
    "and nothing more after that."
)

# Standard dictionary system prompt payload consumed by brain.py / Ollama execution loop
SYSTEM_PROMPT = {
    "role": "system",
    "content": EVA_INTERVIEWER_SYSTEM_PROMPT_TEXT
}

# Domain prompt vocabulary for guiding Faster-Whisper technical transcription in listener.py
WHISPER_INITIAL_PROMPT = (
    "Python, JavaScript, React.js, Next.js, TypeScript, FastAPI, PostgreSQL, Redis, Docker, "
    "Kubernetes, System Design, REST APIs, Microservices, Data Structures, Algorithms, "
    "tech mock interview developer candidate response."
)
