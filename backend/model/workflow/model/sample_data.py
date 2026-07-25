import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_RESUME_PATH = os.path.join(CURRENT_DIR, "sample_resume.txt")
SAMPLE_JD_PATH = os.path.join(CURRENT_DIR, "sample_jd.txt")

def get_sample_resume_text() -> str:
    if os.path.exists(SAMPLE_RESUME_PATH):
        with open(SAMPLE_RESUME_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "Sample Resume Content"

def get_sample_jd_text() -> str:
    if os.path.exists(SAMPLE_JD_PATH):
        with open(SAMPLE_JD_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "Sample Job Description Content"
