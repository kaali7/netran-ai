"""
Netran AI — Workflow Orchestrator
Module: sample_data.py
Description: Demo testing data provider exposing sample resume and job description JSON files.
"""

import os
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_RESUME_PATH = os.path.join(CURRENT_DIR, "sample_resume.json")
SAMPLE_JOB_DETAIL_PATH = os.path.join(CURRENT_DIR, "sample_job_detail.json")
SAMPLE_JD_PATH = SAMPLE_JOB_DETAIL_PATH

def get_sample_resume_text() -> str:
    if os.path.exists(SAMPLE_RESUME_PATH):
        try:
            with open(SAMPLE_RESUME_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("resume_text", "")
        except Exception:
            pass
    return "Sample Resume Content"

def get_sample_jd_text() -> str:
    if os.path.exists(SAMPLE_JOB_DETAIL_PATH):
        try:
            with open(SAMPLE_JOB_DETAIL_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("jd_text", "")
        except Exception:
            pass
    return "Sample Job Description Content"
