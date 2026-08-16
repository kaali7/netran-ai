"""
Netran AI — Gemini JSON Extraction Service.
Parses raw resume text and raw JD text into structured CandidateProfile
and ParsedJD schemas using Google Gemini with enforced JSON output.
"""

import json
from fastapi import HTTPException, status
from api.config import settings


# ── Prompt Templates ────────────────────────────────────────────────────────

RESUME_PROMPT = """You are an expert HR data extraction system. Extract structured information from the resume text below.

Return ONLY a valid JSON object with exactly this schema (use null for any missing fields):
{{
  "name": "Full name of the candidate (string or null)",
  "email": "Email address (string or null)",
  "phone": "Phone number (string or null)",
  "location": "City, Country or full address (string or null)",
  "summary": "Professional summary or objective (string or null)",
  "technical_skills": ["list", "of", "technical", "skills"],
  "soft_skills": ["list", "of", "soft", "skills"],
  "work_history": [
    {{
      "company": "Company name",
      "role": "Job title",
      "duration": "e.g. Jan 2022 - Mar 2024",
      "responsibilities": ["key responsibility 1", "key responsibility 2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "institution": "University or school name",
      "year": "Graduation year or range",
      "gpa": "GPA if mentioned, else null"
    }}
  ],
  "projects": ["Project 1 description", "Project 2 description"],
  "certifications": ["Certification 1", "Certification 2"],
  "languages": ["English", "Hindi"],
  "raw_text_length": {raw_text_length}
}}

Resume Text:
---
{raw_text}
---
"""

JD_PROMPT = """You are an expert job requirements extraction system. Extract structured information from the job description text below.

Return ONLY a valid JSON object with exactly this schema (use null for any missing fields):
{{
  "role_title": "Exact job title (string or null)",
  "company": "Company name (string or null)",
  "seniority_level": "One of: Junior, Mid-Level, Senior, Lead, Principal, Manager, Director, VP (string or null)",
  "employment_type": "One of: Full-time, Part-time, Contract, Internship, Freelance (string or null)",
  "location": "City, Country or Remote (string or null)",
  "required_skills": ["must-have skill 1", "must-have skill 2"],
  "optional_skills": ["nice-to-have skill 1", "nice-to-have skill 2"],
  "responsibilities": ["key responsibility 1", "key responsibility 2"],
  "qualifications": ["required qualification 1", "required qualification 2"],
  "experience_years_min": 2,
  "experience_years_max": 5,
  "domain": "e.g. Backend Engineering, Data Science, DevOps, ML/AI (string or null)",
  "raw_text_length": {raw_text_length}
}}

Job Description Text:
---
{raw_text}
---
"""


# ── Extraction Functions ─────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> dict:
    """
    Send a structured extraction prompt to Gemini and return parsed JSON.

    Raises:
        HTTPException(503): If Gemini API key is missing or API call fails.
        HTTPException(422): If Gemini response cannot be parsed as valid JSON.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key is not configured. Set GEMINI_API_KEY in backend/.env",
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,      # Low temperature for structured extraction
                max_output_tokens=4096,
            ),
        )
        raw_json = response.text.strip()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gemini API call failed: {exc}",
        ) from exc

    # Parse and validate JSON response
    try:
        # Strip markdown code fences if Gemini wraps response
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]
            raw_json = raw_json.strip()
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Gemini returned invalid JSON: {exc}. Raw response: {raw_json[:300]}",
        ) from exc


def parse_resume(raw_text: str) -> dict:
    """
    Extract a structured CandidateProfile JSON from raw resume text using Gemini.

    Args:
        raw_text: Plain text extracted from the uploaded resume file.

    Returns:
        dict: Structured CandidateProfile payload.
    """
    prompt = RESUME_PROMPT.format(
        raw_text=raw_text[:12000],  # Truncate to ~12k chars to stay within token budget
        raw_text_length=len(raw_text),
    )
    result = _call_gemini(prompt)
    result["raw_text_length"] = len(raw_text)
    return result


def parse_jd(raw_text: str) -> dict:
    """
    Extract a structured ParsedJD JSON from raw job description text using Gemini.

    Args:
        raw_text: Plain text of the job description.

    Returns:
        dict: Structured ParsedJD payload.
    """
    prompt = JD_PROMPT.format(
        raw_text=raw_text[:8000],  # JD texts are generally shorter
        raw_text_length=len(raw_text),
    )
    result = _call_gemini(prompt)
    result["raw_text_length"] = len(raw_text)
    return result
