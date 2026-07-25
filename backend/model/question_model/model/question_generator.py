"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: question_generator.py
Description: Core reasoning engine using Gemini 3.6 Flash and Pydantic schemas to generate
             the 15-question tiered interview tree (`interview_questions.json`) and the custom
             latency-constrained system prompt (`system_prompt.txt`).
"""

import json
import logging
import os
from typing import Optional
from pydantic import ValidationError

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_MODEL
from .schemas import Stage2Output
from .prompt_builder import get_system_prompt_instructions
from .resume_parser import parse_resume

logger = logging.getLogger(__name__)

def generate_stage2_output(
    session_id: str,
    jd_text: str,
    resume_path: str,
    target_seniority: str = "Mid",
    output_dir: str = None
) -> Stage2Output:
    """
    Core reasoning engine leveraging Gemini to generate structured interview questions
    and the behavioral system prompt based on JD and Candidate Resume.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 1. Parse the resume
    try:
        resume_text = parse_resume(resume_path)
    except Exception as e:
        logger.error(f"Failed to parse resume: {e}")
        raise

    # 2. Build instructions for prompt generation
    prompt_instructions = get_system_prompt_instructions(target_seniority)

    # 3. Construct the full Gemini prompt
    full_prompt = f"""
You are an expert technical interviewer and AI system designer.
Your task is to analyze the Job Description (JD) and the Candidate's Resume to output a structured JSON containing:
1. An ordered Question Tree (15 questions).
2. The custom System Prompt for the AI interviewer.

### Candidate Resume:
```
{resume_text}
```

### Job Description / Key Pillars:
```
{jd_text}
```

### Instructions for Question Tree:
- Perform Skill Overlap & Gap Matrix mapping. 
- For Strong Overlap, generate high-difficulty production/debugging questions.
- For Missing / Unlisted Skills, generate foundational concept verification questions to detect technical blindspots.
- Probe specific projects from the resume.
- Generate exactly 15 questions, tiered as:
  * Tier 1 (Warmup/Foundations): Questions 1-2
  * Tier 2 (Core Arch/Production): Questions 3-12
  * Tier 3 (Advanced/System Design): Questions 13-15
- Difficulty levels must be "Junior", "Mid", or "Senior".
- Topics must be distinct technical domains.

### Instructions for System Prompt:
{prompt_instructions}

Return exactly the JSON object matching the requested schema.
"""

    logger.info("Calling Gemini for Stage 2 Question Generation...")
    
    try:
        response = None
        last_err = None
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=Stage2Output,
                        temperature=0.2,
                    )
                )
                if response and response.text:
                    break
            except Exception as e:
                last_err = e
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    logger.warning(f"Gemini API rate limit hit (429). Retrying attempt {attempt}/3 in 5s...")
                    import time
                    time.sleep(5)
                else:
                    raise e

        if not response or not response.text:
            raise last_err or ValueError("Empty response from Gemini")
            
        output_text = response.text
        stage2_output = Stage2Output.model_validate_json(output_text)
        
        # Override session_id with the provided one
        stage2_output.session_id = session_id

        # 4. Save artifacts if output_dir is provided
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
            # File 1: Generated 15-question interview tree
            questions_path = os.path.join(output_dir, "interview_questions.json")
            with open(questions_path, "w", encoding="utf-8") as f:
                json.dump([q.model_dump() for q in stage2_output.question_tree], f, indent=2)
                
            # File 2: LLM interviewer behavior & runtime system prompt
            behavior_path = os.path.join(output_dir, "interviewer_behavior.json")
            behavior_payload = {
                "session_id": session_id,
                "persona": "Eva",
                "target_seniority": target_seniority,
                "interviewer_system_prompt": stage2_output.interviewer_system_prompt,
                "behavior_rules": [
                  "Maximum 1-2 sentences per response for low-latency streaming voice execution",
                  "Maintain direct, professional, conversational roleplay persona",
                  "Probe architectural trade-offs, edge cases, and failure modes"
                ]
            }
            with open(behavior_path, "w", encoding="utf-8") as f:
                json.dump(behavior_payload, f, indent=2)
                
            logger.info(f"Stage 2 output artifacts (interview_questions.json & interviewer_behavior.json) saved to {output_dir}")

        return stage2_output

    except ValidationError as ve:
        logger.error(f"Pydantic Validation Error on Gemini Output: {ve}")
        raise
    except Exception as e:
        logger.error(f"Error during Gemini generation: {e}")
        raise
