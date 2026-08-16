"""
Netran AI — Document Text Extraction Service.
Handles PDF, DOCX, TXT, and TEX resume file formats.
"""

import io
from fastapi import HTTPException, status


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".tex"}


def extract_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text from a PDF file using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())
        raw_text = "\n".join(text_parts)
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="PDF file appears to be image-only or empty. Please upload a text-based PDF.",
            )
        return raw_text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text from PDF: {exc}",
        ) from exc


def extract_from_docx(file_bytes: bytes) -> str:
    """Extract raw text from a DOCX Word document using python-docx."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())
        # Also extract table cell text
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_parts.append(cell.text.strip())
        raw_text = "\n".join(text_parts)
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="DOCX file is empty or has no readable text content.",
            )
        return raw_text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text from DOCX: {exc}",
        ) from exc


def extract_from_txt(file_bytes: bytes) -> str:
    """Extract raw text from a plain text or LaTeX file."""
    try:
        # Try UTF-8 first, fall back to latin-1
        try:
            raw_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raw_text = file_bytes.decode("latin-1")

        # Strip LaTeX commands for .tex files (basic sanitization)
        import re
        raw_text = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", raw_text)  # \cmd{...}
        raw_text = re.sub(r"\\[a-zA-Z]+", " ", raw_text)            # \cmd
        raw_text = re.sub(r"[{}]", " ", raw_text)                   # curly braces
        raw_text = re.sub(r"\s{2,}", " ", raw_text)                 # collapse whitespace
        raw_text = raw_text.strip()

        if not raw_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Text file is empty.",
            )
        return raw_text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to read text file: {exc}",
        ) from exc


def extract_text(filename: str, file_bytes: bytes) -> str:
    """
    Dispatch file bytes to the correct extractor based on file extension.

    Args:
        filename: Original upload filename (used for extension detection).
        file_bytes: Raw file content bytes.

    Returns:
        str: Extracted plain text content.

    Raises:
        HTTPException(415): If file type is not supported.
    """
    import pathlib
    ext = pathlib.Path(filename).suffix.lower()

    if ext == ".pdf":
        return extract_from_pdf(file_bytes)
    elif ext in {".docx", ".doc"}:
        return extract_from_docx(file_bytes)
    elif ext in {".txt", ".tex"}:
        return extract_from_txt(file_bytes)
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            ),
        )
