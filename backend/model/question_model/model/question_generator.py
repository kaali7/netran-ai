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
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Stage2Output,
                temperature=0.2,
            )
        )
        
        output_text = response.text
        if not output_text:
            raise ValueError("Empty response from Gemini")
            
        stage2_output = Stage2Output.model_validate_json(output_text)
        
        # Override session_id with the provided one
        stage2_output.session_id = session_id

        # 4. Save artifacts if output_dir is provided
        if output_dir:
            if output_dir.lower().endswith(".json"):
                artifact_path = output_dir
            elif os.path.isdir(output_dir):
                artifact_path = os.path.join(output_dir, "stage2_output.json")
            else:
                artifact_path = f"{output_dir}.json"

            parent_dir = os.path.dirname(os.path.abspath(artifact_path))
            os.makedirs(parent_dir, exist_ok=True)
            
            with open(artifact_path, "w", encoding="utf-8") as f:
                f.write(stage2_output.model_dump_json(indent=2))
                
            logger.info(f"Stage 2 single JSON artifact saved cleanly to {artifact_path}")

        return stage2_output

    except ValidationError as ve:
        logger.error(f"Pydantic Validation Error on Gemini Output: {ve}")
        raise
    except Exception as e:
        logger.error(f"Error during Gemini generation: {e}")
        raise
