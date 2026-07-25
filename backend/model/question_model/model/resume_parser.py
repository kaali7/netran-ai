"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: resume_parser.py
Description: Multimodal document extractor supporting PDF (`pypdf`), DOCX (`python-docx`),
             and TXT files to extract clean candidate resume text.
"""

import os
import docx
from pypdf import PdfReader

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text from a given PDF, DOCX, or TXT file.
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

def parse_resume(file_path: str) -> str:
    """
    Parses the resume and returns clean text ready for LLM processing.
    """
    raw_text = extract_text_from_file(file_path)
    # Basic cleaning
    lines = raw_text.splitlines()
    clean_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(clean_lines)
