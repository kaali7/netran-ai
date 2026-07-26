"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: resume_parser.py
Description: Class-based ResumeParser supporting PDF, DOCX, TXT, and JSON files to extract clean candidate resume text.
"""

import json
import os

import docx
from pypdf import PdfReader


class ResumeParser:
    """Class-based resume parser for PDF, DOCX, TXT, and JSON formats."""

    def parse(self, file_path: str) -> str:
        """
        Parses the resume and returns clean text ready for LLM processing.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.lower().split('.')[-1]
        
        if ext == 'pdf':
            raw_text = self._extract_from_pdf(file_path)
        elif ext == 'docx':
            raw_text = self._extract_from_docx(file_path)
        elif ext == 'txt':
            raw_text = self._extract_from_txt(file_path)
        elif ext == 'json':
            raw_text = self._extract_from_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: .{ext}")

        lines = raw_text.splitlines()
        clean_lines = [line.strip() for line in lines if line.strip()]
        return "\n".join(clean_lines)

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        reader = PdfReader(file_path)
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return "\n".join(text)

    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        doc = docx.Document(file_path)
        text = [paragraph.text for paragraph in doc.paragraphs]
        return "\n".join(text)

    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
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


# Backward compatibility wrappers
def extract_text_from_file(file_path: str) -> str:
    return ResumeParser().parse(file_path)

def parse_resume(file_path: str) -> str:
    return ResumeParser().parse(file_path)
