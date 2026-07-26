"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: resume_parser.py
Description: Multimodal document extractor supporting PDF (`pypdf`), DOCX (`python-docx`),
             TXT, and JSON files to extract clean candidate resume text.
"""

import os
import json
import docx
from pypdf import PdfReader

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text from a given PDF, DOCX, TXT, or JSON file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = file_path.lower().split('.')[-1]
    
    if ext == 'pdf':
        return _extract_from_pdf(file_path)
    elif ext == 'docx':
        return _extract_from_docx(file_path)
    elif ext == 'txt':
        return _extract_from_txt(file_path)
    elif ext == 'json':
        return _extract_from_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: .{ext}")

def _extract_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return "\n".join(text)

def _extract_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    text = [paragraph.text for paragraph in doc.paragraphs]
    return "\n".join(text)

def _extract_from_txt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def _extract_from_json(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, dict):
            if "resume_text" in data:
                return str(data["resume_text"])
            return json.dumps(data, indent=2)
        elif isinstance(data, list):
            return "\n".join([str(item) for item in data])
        return str(data)

def parse_resume(file_path: str) -> str:
    """
    Parses the resume and returns clean text ready for LLM processing.
    """
    raw_text = extract_text_from_file(file_path)
    # Basic cleaning
    lines = raw_text.splitlines()
    clean_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(clean_lines)
