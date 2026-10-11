"""
Build content.docx from content.md for the Netran AI college project document.
Uses python-docx to produce a properly formatted, print-ready Word document.
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re

# ── Helpers ────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_table_borders(table):
    """Apply solid borders to every cell in a table."""
    for row in table.rows:
        for cell in row.cells:
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcBorders = OxmlElement("w:tcBorders")
            for edge in ("top", "left", "bottom", "right"):
                tag = OxmlElement(f"w:{edge}")
                tag.set(qn("w:val"), "single")
                tag.set(qn("w:sz"), "6")
                tag.set(qn("w:space"), "0")
                tag.set(qn("w:color"), "333333")
                tcBorders.append(tag)
            tcPr.append(tcBorders)


def cell_text(cell, text, bold=False, italic=False, size=11,
              align=WD_ALIGN_PARAGRAPH.LEFT, color=None):
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor(*color)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


# ── Document Setup ─────────────────────────────────────────────────────────

doc = Document()

# Margins
for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(3.2)
    section.right_margin  = Cm(2.5)

# Default style
ns = doc.styles["Normal"]
ns.font.name = "Times New Roman"
ns.font.size = Pt(12)


# ── Style helpers ──────────────────────────────────────────────────────────

def add_heading1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(6)
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def add_heading2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0x16, 0x21, 0x3e)
    return p


def add_heading3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(3)
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(12.5)
    run.font.color.rgb = RGBColor(0x2c, 0x3e, 0x50)
    return p


def add_para(text, italic=False, bold=False, size=12,
             align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=False):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(4)
    if indent:
        p.paragraph_format.left_indent = Cm(0.6)
    run = p.add_run(text)
    run.italic = italic
    run.bold = bold
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    return p


def add_bullet(text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(0.6 + level * 0.5)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(11.5)
    return p


def add_divider():
    p = doc.add_paragraph("─" * 90)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    for run in p.runs:
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0xcc, 0xcc, 0xcc)


def add_page_break():
    doc.add_page_break()


def build_md_table(rows, col_widths=None, header_bg="E8E1D5"):
    """Build a Word table from a list of row lists."""
    if not rows:
        return
    n_cols = len(rows[0])
    tbl = doc.add_table(rows=len(rows), cols=n_cols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style = "Table Grid"
    set_table_borders(tbl)
    for r_idx, row_data in enumerate(rows):
        for c_idx, cell_data in enumerate(row_data):
            cell = tbl.rows[r_idx].cells[c_idx]
            is_header = (r_idx == 0)
            if is_header:
                set_cell_bg(cell, header_bg)
            align = WD_ALIGN_PARAGRAPH.CENTER if c_idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
            cell_text(cell, str(cell_data).strip("*"), bold=is_header, size=11, align=align)
    if col_widths:
        for c_idx, width in enumerate(col_widths):
            for row in tbl.rows:
                row.cells[c_idx].width = Cm(width)
    doc.add_paragraph("")


def add_code_block(text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.8)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.font.name = "Courier New"
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)


# ══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# ── Cover / Title ──────────────────────────────────────────────────────────

doc.add_paragraph("")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("SHREE RAMCHANDRA COLLEGE OF ENGINEERING, PUNE")
r.bold = True; r.font.size = Pt(14); r.font.name = "Times New Roman"

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Department of Computer Engineering & Artificial Intelligence")
r.italic = True; r.font.size = Pt(12); r.font.name = "Times New Roman"

doc.add_paragraph("")

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("NETRAN AI")
r.bold = True; r.font.size = Pt(22); r.font.name = "Times New Roman"
r.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("An Autonomous, Real-Time AI-Powered Technical Interviewer Platform")
r.italic = True; r.font.size = Pt(12); r.font.name = "Times New Roman"

doc.add_paragraph("")

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Project Report")
r.font.size = Pt(12); r.font.name = "Times New Roman"

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Academic Year: 2025–26")
r.font.size = Pt(12); r.font.name = "Times New Roman"

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("GitHub: https://github.com/kaali7/netran-ai")
r.font.size = Pt(11); r.italic = True; r.font.name = "Times New Roman"
r.font.color.rgb = RGBColor(0x00, 0x56, 0xb3)

add_page_break()


# ── Certificate ─────────────────────────────────────────────────────────────

add_heading1("CERTIFICATE")
add_divider()
add_para(
    "This is to certify that the project entitled \"Netran AI — An Autonomous, Real-Time "
    "AI-Powered Technical Interviewer Platform\" has been successfully completed by the "
    "undersigned students in partial fulfillment of the requirements for the degree of "
    "Bachelor of Engineering in Computer Engineering at Shree Ramchandra College of "
    "Engineering, Pune, affiliated to Savitribai Phule Pune University, during the "
    "academic year 2025–26."
)
doc.add_paragraph("")
add_para("Project Guide: ___________________________", align=WD_ALIGN_PARAGRAPH.LEFT)
add_para("HOD Signature: ___________________________", align=WD_ALIGN_PARAGRAPH.LEFT)
add_para("Date: ___________________________", align=WD_ALIGN_PARAGRAPH.LEFT)
add_page_break()


# ── Acknowledgement ─────────────────────────────────────────────────────────

add_heading1("ACKNOWLEDGEMENT")
add_divider()
add_para(
    "We express our sincere gratitude to our project guide and all faculty members of "
    "the Department of Computer Engineering & Artificial Intelligence at Shree Ramchandra "
    "College of Engineering, Pune, for their continuous support, valuable guidance, and "
    "encouragement throughout the development of this project."
)
add_para(
    "We also acknowledge the open-source communities behind FastAPI, React, Faster-Whisper, "
    "Silero VAD, Kokoro-82M, Ollama, and Google Gemini for providing the powerful tools and "
    "models that made this project possible."
)
add_para(
    "Finally, we thank our families and peers for their unwavering support and motivation "
    "during the course of this project."
)
add_page_break()


# ── Abstract ────────────────────────────────────────────────────────────────

add_heading1("ABSTRACT")
add_divider()
add_para(
    "Netran AI is a production-grade, autonomous, real-time AI-powered technical interviewer "
    "platform designed to bridge the gap between static resume qualifications and high-stakes "
    "corporate interview preparation. Traditional mock interview tools rely on generic question "
    "banks, text-only interfaces, and fail to contextualize questions around specific Job "
    "Descriptions (JDs) and candidate resumes. They also lack real-time conversational voice "
    "responsiveness and suffer from echo bleed-through and timing jitter during voice turn-taking."
)
add_para(
    "Netran AI addresses these limitations through a modular four-stage AI pipeline: "
    "Stage 1 conducts live web research using Tavily Search API and Google Gemini 3.6 Flash "
    "to synthesize contextual hiring rubrics. Stage 2 cross-matches candidate resumes against "
    "job descriptions to build a 15-question adaptive interview tree. Stage 3 executes a "
    "full-duplex voice interview achieving sub-400ms turn latency using Silero VAD, "
    "Faster-Whisper STT, Ollama Qwen 2.5 (3B) LLM, Kokoro-82M TTS, and a Level 2 TurnManager "
    "state machine. Stage 4 performs a 3-branch multimodal Gemini evaluation scoring acoustic "
    "delivery and technical accuracy holistically."
)
add_para(
    "Key Achievements: Sub-250ms Time-To-First-Audio, deterministic echo elimination with 0% "
    "false VAD triggers, 98.8% Whisper technical accuracy with domain vocabulary injection, "
    "and automated post-session multimodal hiring scorecards."
)
add_page_break()


# ── List of Figures ─────────────────────────────────────────────────────────

add_heading1("LIST OF FIGURES")
add_divider()
build_md_table([
    ["Figure No.", "Title", "Page No."],
    ["Fig. 4.1", "System Architecture Overview — Four-Stage AI Pipeline", "23"],
    ["Fig. 4.2", "Data Flow Diagram (DFD) — Level 0 & Level 1", "25"],
    ["Fig. 4.3", "Entity-Relationship (ER) Diagram", "26"],
    ["Fig. 4.4", "Database Schema Design", "27"],
    ["Fig. 5.1", "Stage 1 Research Model — Pipeline Flow", "29"],
    ["Fig. 5.2", "Stage 2 Question Engine — Skill Gap Matrix", "31"],
    ["Fig. 5.3", "Stage 3 Voice Loop — TurnManager State Machine", "33"],
    ["Fig. 5.4", "Stage 4 Evaluation — 3-Branch Gemini Architecture", "36"],
    ["Fig. 5.5", "FastAPI Gateway — Router Architecture", "38"],
    ["Fig. 5.6", "React SPA — Dashboard and Interview Room UI", "40"],
    ["Fig. 6.1", "Voice Pipeline End-to-End Latency Breakdown", "48"],
    ["Fig. 7.1", "Code Quality Audit — Ruff & Bandit Report", "52"],
], col_widths=[2.5, 11.0, 2.5])
add_page_break()


# ── List of Abbreviations ────────────────────────────────────────────────────

add_heading1("LIST OF ABBREVIATIONS")
add_divider()
build_md_table([
    ["Abbreviation", "Full Form"],
    ["AI", "Artificial Intelligence"],
    ["API", "Application Programming Interface"],
    ["DFD", "Data Flow Diagram"],
    ["ER", "Entity Relationship"],
    ["FastAPI", "Fast Application Programming Interface (Python Web Framework)"],
    ["GPU", "Graphics Processing Unit"],
    ["HTTP", "Hypertext Transfer Protocol"],
    ["JD", "Job Description"],
    ["JWT", "JSON Web Token"],
    ["LLM", "Large Language Model"],
    ["ONNX", "Open Neural Network Exchange"],
    ["PCM", "Pulse-Code Modulation"],
    ["RBAC", "Role-Based Access Control"],
    ["REST", "Representational State Transfer"],
    ["RMS", "Root Mean Square"],
    ["SPA", "Single Page Application"],
    ["SQLite", "Structured Query Language (Lightweight)"],
    ["STT", "Speech-to-Text"],
    ["TTS", "Text-to-Speech"],
    ["VAD", "Voice Activity Detection"],
    ["WS", "WebSocket"],
], col_widths=[4.0, 12.0])
add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 1: INTRODUCTION
# ══════════════════════════════════════════════════════════════════════════════

add_heading1("CHAPTER 1: INTRODUCTION")
add_divider()

add_heading2("1.1 Introduction to the Topic")
add_para(
    "The recruitment industry has been increasingly adopting AI-powered tools to automate and "
    "enhance technical screening. However, most existing solutions remain limited to static "
    "question-answer databases, text-based chatbots, or video platforms that require human "
    "interviewers. There is a significant gap in the availability of a truly autonomous, "
    "voice-driven, and context-aware AI interviewer that can dynamically adapt to a specific "
    "candidate's resume and a company's job requirements."
)
add_para(
    "Netran AI (derived from \"Neural Training\") is a full-stack AI platform that embodies "
    "a new paradigm: a conversational AI interviewer named \"Eva\" that conducts real-time, "
    "full-duplex voice-to-voice technical interviews. Eva understands the job description, "
    "reads the candidate's resume, formulates a personalized 15-question tree, and conducts "
    "a natural-sounding voice interview with sub-400ms response latency — all without any "
    "human involvement."
)

add_heading2("1.2 Motivation for the Project")
add_para("The primary motivation behind Netran AI arises from three key pain points:")
add_bullet("Lack of Personalization: Generic mock interview platforms provide the same questions to every candidate, regardless of their specific skill set, target company, or job role.")
add_bullet("No Real Voice Interaction: Text-based platforms fail to train candidates for real-time spoken communication under pressure.")
add_bullet("Static and Outdated Content: Fixed question banks do not reflect current industry hiring standards at target companies.")
add_para(
    "The research question driving the entire engineering effort was: \"How can low-latency "
    "voice-to-voice conversational AI be synchronized with web audio transports to eliminate "
    "false acoustic triggers while maintaining sub-400ms turn transitions in technical interviews?\""
)

add_heading2("1.3 Problem Definition")
add_bullet("Problem 1 — Context Gap: Interview questions not tailored to candidate experience or target company JD.")
add_bullet("Problem 2 — Voice Turn-Taking: Acoustic echo causes false speech detection, leading to the AI interrupting itself.")
add_bullet("Problem 3 — Latency: Voice turn-around latency > 2 seconds makes conversations unnatural.")
add_bullet("Problem 4 — Evaluation Quality: Most AI tools score on a single dimension, missing acoustic delivery quality.")
add_bullet("Problem 5 — Hardware Variability: Different microphone sample rates (44.1kHz, 48kHz) cause VAD false triggers from OS resampling artifacts.")

add_heading2("1.4 Existing Systems")
build_md_table([
    ["System", "Type", "Limitation"],
    ["Pramp", "Peer mock interviews", "Requires human partner, not autonomous"],
    ["Interviewing.io", "Anonymous live coding", "Human-dependent, no voice AI"],
    ["HireVue", "Video interview", "One-way video, no real-time AI conversation"],
    ["ChatGPT (text)", "LLM text mock", "No voice, no JD-context personalization"],
    ["Google Interview Warmup", "Basic voice Q&A", "Generic questions, no adaptive branching"],
    ["Turing / Karat", "Outsourced screening", "Human interviewers required"],
], col_widths=[4.0, 4.5, 7.5])

add_heading2("1.5 Drawbacks of Existing Systems")
add_bullet("No dynamic question generation: Questions are pre-written and don't adapt based on candidate responses.")
add_bullet("No real-time voice conversation: Most tools rely on text or one-way video recording.")
add_bullet("No JD-specific rubric generation: Content not tied to actual job descriptions or company hiring standards.")
add_bullet("No acoustic evaluation: Audio delivery quality (pace, filler words, clarity) is not analyzed.")
add_bullet("No SHA-256 caching: Redundant JD analysis wastes API credits and time.")
add_bullet("Vendor lock-in: Cloud-only solutions create latency, cost, and privacy concerns.")

add_heading2("1.6 Relevance of the Project")
add_bullet("Industry Demand: The global AI recruitment market is projected to exceed $890 million by 2028.")
add_bullet("Educational Relevance: Personalized, voice-based AI coaching tools are unavailable at scale for engineering students.")
add_bullet("Research Contribution: The Level 2 TurnManager is a novel engineering solution to the acoustic echo problem in browser-based voice AI.")
add_bullet("Technical Excellence: Six distinct AI models integrated into one cohesive, low-latency platform.")
add_bullet("Open Source: Built entirely on open-source infrastructure via public GitHub repository.")

add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 2: LITERATURE SURVEY
# ══════════════════════════════════════════════════════════════════════════════

add_heading1("CHAPTER 2: LITERATURE SURVEY")
add_divider()

add_heading2("2.1 Survey of Related Work")

add_heading3("[1] Whisper — Robust Speech Recognition (Radford et al., OpenAI, 2022)")
add_para(
    "OpenAI's Whisper introduced a transformer-based ASR model trained on 680,000 hours of "
    "multilingual audio. The small int8 CTranslate2 quantized variant used in Netran AI achieves "
    "real-time transcription with 350–500ms latency on CPU. The paper's initial prompt conditioning "
    "inspired the whisper_domain_vocabulary injection mechanism in Stage 2 to reduce technical "
    "term hallucination from 18.4% to under 1.2%."
)

add_heading3("[2] Silero VAD (Silero Team, 2021)")
add_para(
    "Silero VAD provides an ONNX-compatible voice activity detection model classifying audio frames "
    "as speech or non-speech with high precision. Its ONNX Runtime optimization allows CPU-only "
    "inference at < 2ms per 30ms frame, making it viable for real-time embedded VAD in Stage 3."
)

add_heading3("[3] Kokoro-82M TTS (HexGrad, 2024)")
add_para(
    "Kokoro-82M is a lightweight PyTorch neural TTS model capable of sub-250ms Time-To-First-Audio "
    "(TTFA) in streaming mode — benchmarked to be 2.4x faster than cloud-hosted TTS alternatives "
    "in low-bandwidth LAN conditions."
)

add_heading3("[4] Qwen 2.5 Technical Report (Alibaba Cloud, 2024)")
add_para(
    "The Qwen 2.5 3B parameter variant served via Ollama at 4-bit quantization achieves 120–180ms "
    "Time-To-First-Token (TTFT), enabling low-latency LLM reasoning for Eva's interview brain."
)

add_heading3("[5] SpeechBrain ECAPA-TDNN Speaker Verification (Desplanques et al., 2020)")
add_para(
    "The ECAPA-TDNN model enables robust speaker verification from short audio segments (≥ 2s). "
    "Netran AI uses this to auto-enroll the candidate's voice print and verify speaker identity "
    "across interview turns."
)

add_heading3("[6] Gemini Multimodal LLM (Google DeepMind, 2024)")
add_para(
    "Google Gemini's multimodal capability to process both audio waveforms and text simultaneously "
    "is leveraged in Stage 4 for the Audio Acoustic Branch evaluation, providing holistic "
    "candidate performance scoring."
)

add_heading2("2.2 Comparative Analysis of Existing Approaches")
build_md_table([
    ["Feature", "Netran AI", "Pramp", "HireVue", "Google Warmup"],
    ["JD-personalized questions", "Yes", "No", "No", "No"],
    ["Real-time voice conversation", "Yes", "Yes (peer)", "No", "Limited"],
    ["Resume cross-analysis", "Yes", "No", "No", "No"],
    ["Autonomous (no human)", "Yes", "No", "No", "Yes"],
    ["Acoustic evaluation", "Yes", "No", "Limited", "No"],
    ["Sub-400ms voice latency", "Yes", "N/A", "N/A", "Limited"],
    ["Offline AI inference", "Yes", "No", "No", "No"],
    ["Keyword branching logic", "Yes", "No", "No", "No"],
    ["Open source", "Yes", "No", "No", "No"],
], col_widths=[5.5, 2.5, 2.5, 2.5, 3.0])

add_heading2("2.3 Identified Research Gap")
add_bullet("Gap 1 — Echo-Free Full-Duplex in Browsers: No published work addresses acoustic echo elimination in browser-based voice AI without hardware AEC chips. The Level 2 TurnManager solves this via Web Audio API event-driven state synchronization.")
add_bullet("Gap 2 — Domain Vocabulary STT Injection: Dynamic per-JD vocabulary injection for real-time interview systems has not been reported. Netran AI reduces technical hallucination from 18.4% to < 1.2%.")
add_bullet("Gap 3 — Multimodal Interview Evaluation: No open-source tool scores both acoustic quality and technical accuracy simultaneously. Netran AI's 3-branch Gemini evaluation fills this gap.")

add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 3: REQUIREMENTS
# ══════════════════════════════════════════════════════════════════════════════

add_heading1("CHAPTER 3: REQUIREMENTS FOR THE PROPOSED SYSTEM")
add_divider()

add_heading2("3.1 Introduction to Requirement Planning")
add_para(
    "Requirements were gathered through three phases: Problem Analysis (identifying gaps in "
    "existing tools), Feature Mapping (pairing each gap to a software feature and AI model), "
    "and Constraint Analysis (hardware, latency, and cost constraints). Requirements are "
    "categorized into Functional and Non-Functional."
)

add_heading2("3.2 Functional Requirements")
build_md_table([
    ["ID", "Requirement", "Priority"],
    ["FR1", "Accept resume uploads in .pdf, .docx, and .txt formats", "High"],
    ["FR2", "Accept raw Job Description text input or file uploads", "High"],
    ["FR3", "Query live hiring benchmarks using Tavily Search API (Stage 1)", "High"],
    ["FR4", "Generate 15-question adaptive interview tree using Gemini (Stage 2)", "High"],
    ["FR5", "Conduct full-duplex real-time voice interview via WebSocket (Stage 3)", "High"],
    ["FR6", "Detect candidate speech using Silero VAD with RMS energy gating", "High"],
    ["FR7", "Transcribe candidate speech using Faster-Whisper STT", "High"],
    ["FR8", "Generate AI interviewer responses using Ollama Qwen 2.5 (3B)", "High"],
    ["FR9", "Synthesize AI voice responses using Kokoro-82M TTS", "High"],
    ["FR10", "Evaluate sessions using 3-branch Gemini Multimodal AI (Stage 4)", "High"],
    ["FR11", "Provide user registration, login, and JWT authentication", "High"],
    ["FR12", "Maintain real-time notification system for pipeline events", "Medium"],
    ["FR13", "Display analytics dashboard with session history and score trends", "Medium"],
    ["FR14", "Support pre-built mock interview templates (Backend, Frontend, Full-Stack)", "Medium"],
    ["FR15", "Support candidate profile and password management", "Low"],
], col_widths=[1.5, 11.0, 2.5])

add_heading2("3.3 Non-Functional Requirements")
build_md_table([
    ["ID", "Requirement", "Specification"],
    ["NFR1", "Latency", "End-to-end voice turn response <= 400ms"],
    ["NFR2", "TTS Speed", "Time-To-First-Audio (TTFA) <= 250ms"],
    ["NFR3", "STT Accuracy", "Technical term recognition >= 99%"],
    ["NFR4", "Scalability", "Modular pipeline decoupling per stage"],
    ["NFR5", "Security", "JWT Bearer Token + Bcrypt password hashing"],
    ["NFR6", "Reliability", "Exponential backoff retry on 429 API errors"],
    ["NFR7", "Offline Capability", "STT, TTS, VAD, LLM must run fully offline"],
    ["NFR8", "Cross-Hardware", "Support 44.1kHz and 48kHz native device rates"],
    ["NFR9", "Browser Compatibility", "Full support for Chromium browsers"],
    ["NFR10", "Code Quality", "Zero Bandit HIGH severity; Ruff > 95%"],
], col_widths=[1.5, 4.0, 10.5])

add_heading2("3.4 Hardware and Software Used & Technologies Used")

add_heading3("Hardware Requirements")
build_md_table([
    ["Component", "Minimum Specification"],
    ["Processor", "Intel Core i5 (8th Gen) / AMD Ryzen 5 or higher"],
    ["RAM", "16 GB DDR4 (32 GB recommended for local LLM)"],
    ["Storage", "20 GB free SSD (Whisper 461MB + Kokoro 330MB + Qwen2.5:3B ~2GB)"],
    ["Microphone", "Any USB or laptop microphone (WASAPI / MME compatible)"],
    ["GPU", "Optional — NVIDIA CUDA GPU accelerates Kokoro TTS"],
    ["OS", "Windows 10/11 (primary), Ubuntu 22.04 (secondary)"],
], col_widths=[4.5, 11.5])

add_heading3("Software & Technology Stack")
build_md_table([
    ["Layer", "Technology", "Version"],
    ["Backend Framework", "FastAPI", "0.115+"],
    ["ASGI Server", "Uvicorn", "0.29+"],
    ["Database ORM", "SQLAlchemy", "2.0+"],
    ["Database", "SQLite 3", "3.45+"],
    ["Auth", "python-jose (JWT) + passlib[bcrypt]", "Latest"],
    ["Cloud AI", "Google Gemini API (gemini-3.6-flash)", "Latest"],
    ["Web Search", "Tavily Search API", "Latest"],
    ["STT Model", "Faster-Whisper (CTranslate2 int8 small)", "1.0+"],
    ["VAD Model", "Silero VAD v3 (ONNX Runtime)", "v3"],
    ["TTS Model", "Kokoro-82M (PyTorch / KPipeline)", "82M"],
    ["Local LLM", "Ollama + Qwen 2.5 (3B)", "0.3+"],
    ["Speaker Verif.", "SpeechBrain ECAPA-TDNN", "Latest"],
    ["Frontend", "React 18 + Vite 5", "18 / 5"],
    ["State Management", "Zustand", "4+"],
    ["Icons", "Lucide React", "Latest"],
    ["Python", "Python 3.12", "3.12+"],
    ["Node.js", "Node.js 18+", "18+"],
], col_widths=[4.0, 8.5, 3.5])

add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 4: SYSTEM DESIGN
# ══════════════════════════════════════════════════════════════════════════════

add_heading1("CHAPTER 4: SYSTEM DESIGN & ARCHITECTURE")
add_divider()

add_heading2("4.1 Methodology Used")
add_para(
    "Netran AI was developed using an Agile Iterative Development methodology with "
    "8 feature-driven sprints: Backend scaffolding, Stage 1 Research Model, Stage 2 "
    "Question Engine, Stage 3 Voice Engine, Level 2 TurnManager, Stage 4 Evaluation, "
    "React 18 Frontend, and Integration & QA. Each sprint followed a Test → Implement "
    "→ Audit cycle using stage-specific test_pipeline.py CLI harnesses and the "
    "scan_code_quality.py automated code quality scanner (Ruff, Pylint, Bandit, Radon)."
)

add_heading2("4.2 System Architecture Overview")
add_para("The system follows a microservice-inspired monorepo pattern:")
add_code_block(
    "React 18 + Vite 5 Web Client (SPA)\n"
    "  Dashboard | Setup | Interview Room | Report | Analytics | Settings\n"
    "  Web Audio API + AudioWorklet (pcm-processor.js: 48kHz → 16kHz PCM)\n"
    "         ↓ REST (JWT) / WebSocket (PCM Audio)\n"
    "FastAPI Gateway (backend/api/)\n"
    "  JWT Auth | Ingestion | Setup | Voice WS | Reports | Notifications\n"
    "    ↓            ↓              ↓                 ↓\n"
    "  [Stage 1]  [Stage 2]     [Stage 3]         [Stage 4]\n"
    "  Research   Question      Voice Loop         Evaluation\n"
    "  Model      Engine        (Eva)              Engine"
)

add_heading2("4.3 Four-Stage AI Pipeline Design")
add_heading3("Stage 1 — Research Model")
add_para("Accepts Job Description text → Tavily domain-restricted web search → Gemini 3.6 Flash synthesizes InterviewRubric JSON. SHA-256 cache prevents redundant API calls.")

add_heading3("Stage 2 — Question Engine")
add_para("Accepts Stage 1 rubric + candidate resume → Dual parallel Planner (15-question tree) and Analyst (skill-gap matrix) → Outputs 3 JSON artifacts: interview_questions.json, interviewer_behavior.json, resume_analysis.json.")

add_heading3("Stage 3 — Voice-to-Voice Model")
add_para("Browser 16kHz PCM → Silero VAD → Faster-Whisper STT → Ollama Qwen 2.5 LLM → Kokoro-82M TTS → Browser audio. Level 2 TurnManager governs all ConversationState transitions.")

add_heading3("Stage 4 — Reports Model")
add_para("Slices recording.wav into per-turn clips → 3-branch Gemini Multimodal Evaluation (Audio Acoustic, Technical Accuracy, Combined Summary) → report.json + evaluation_summary.md.")

add_heading2("4.4 Data Flow Diagram (DFD)")
add_code_block(
    "Level 0 (Context):\n"
    "[Candidate] ── Resume + JD ──▶ [NETRAN AI] ── Evaluation Report ──▶ [Candidate]\n"
    "                                      │\n"
    "                              [Tavily / Gemini APIs]\n\n"
    "Level 1:\n"
    "[Resume] → [Ingest Engine] → [Stage 2: Question Engine]\n"
    "[JD]     → [Stage 1: Research] → [Interview Rubric]\n"
    "                                        ↓\n"
    "                         [interview_questions.json]\n"
    "                         [interviewer_behavior.json]\n"
    "                                        ↓\n"
    "                         [Stage 3: Voice Loop]\n"
    "                         ◀── WebSocket PCM ──▶ [Browser]\n"
    "                                        ↓\n"
    "                         [recording.wav + transcript.json]\n"
    "                                        ↓\n"
    "                         [Stage 4: Evaluation]\n"
    "                                        ↓\n"
    "                         [report.json + scorecard]"
)

add_heading2("4.5 Entity-Relationship (ER) Diagram")
add_para("Four primary entities:")
add_bullet("Users (id PK, email, display_name, hashed_password, role, created_at) — One-to-Many with Sessions")
add_bullet("Sessions (id PK, user_id FK, resume_hash, jd_hash, status, progress_message, created_at) — One-to-One with Session Artifacts")
add_bullet("Session Artifacts (id PK, session_id FK, parsed_resume JSON, parsed_jd JSON, jd_detail JSON, resume_analysis JSON, interview_behavior JSON, question_tree JSON, transcript JSON, evaluation_report JSON)")
add_bullet("Notifications (id PK, user_id FK, title, message, type, link, read, created_at)")

add_heading2("4.6 Database Schema Design")
add_para("SQLite 3 with SQLAlchemy 2.0 ORM and native JSON column support.")
build_md_table([
    ["Table", "Key Columns", "Notes"],
    ["users", "id (UUID PK), email (UNIQUE), display_name, hashed_password, role", "Bcrypt hashed passwords"],
    ["sessions", "id (UUID PK), user_id (FK), resume_hash, jd_hash, status", "SHA-256 deduplication hashes"],
    ["session_artifacts", "session_id (FK), parsed_resume, question_tree, transcript, evaluation_report (JSON)", "All AI outputs as JSON cols"],
    ["notifications", "id (UUID PK), user_id (FK), title, message, type, link, read", "Auto-triggered on Stage 2+4"],
], col_widths=[3.5, 7.5, 5.0])

add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 5: IMPLEMENTATION
# ══════════════════════════════════════════════════════════════════════════════

add_heading1("CHAPTER 5: IMPLEMENTATION OF PROPOSED SYSTEM")
add_divider()

add_heading2("5.1 Stage 1 — Research Model (JD Intelligence Engine)")
add_para("Location: backend/model/research_model/")
add_para("Purpose: Transform a raw Job Description into a structured InterviewRubric enriched with real-time market intelligence.")
add_bullet("JD Parsing (jd_parser.py): Sends JD to Gemini with JD_PARSER_PROMPT_TEMPLATE → structured ParsedJD schema.")
add_bullet("Search Query Generation: 3–5 domain-specific Tavily queries targeting LeetCode, GitHub, Glassdoor, GeeksforGeeks, Blind, ByteByteGo.")
add_bullet("Tavily Search Engine (search_engine.py): Async HTTP queries via httpx + BeautifulSoup4 HTML parsing.")
add_bullet("Rubric Generation (rubric_generator.py): Sends JD + web search results to Gemini → InterviewRubric JSON with assessment topics, difficulty distribution, company culture signals.")
add_bullet("SQLite Caching (cache.py): SHA-256 fingerprint JD → instant cache retrieval < 0.8s on duplicate submissions.")
add_bullet("Output: Single sess_<timestamp>.json artifact.")

add_heading2("5.2 Stage 2 — Question Engine (Adaptive Question Tree)")
add_para("Location: backend/model/question_model/")
add_para("Purpose: Cross-match candidate resume against Stage 1 rubric and generate a 15-question interview tree.")
add_bullet("Resume Parsing (resume_parser.py): Accepts .pdf (pypdf), .docx (python-docx), .txt. Gemini extracts CandidateProfile schema.")
add_bullet("Skill-Gap Cross-Matching: Computes RoleFitScoring matrix across Core Technical (40%), System Design (25%), Behavioral (20%), Domain Knowledge (15%).")
add_bullet("Dual Parallel Pipeline: Planner generates 15-question tree with question_text, expected_keywords, rubric, followup_if_strong, followup_if_weak. Analyst generates resume_analysis.json with skill gaps and red flags.")
add_bullet("Eva Behavior Config: interviewer_behavior.json contains system prompt, behavior_rules, and dynamically generated whisper_domain_vocabulary for STT accuracy.")
add_bullet("Output: interview_questions.json + interviewer_behavior.json + resume_analysis.json in sess_<timestamp>/ directory.")

add_heading2("5.3 Stage 3 — Voice-to-Voice Live Loop (Eva Interviewer)")
add_para("Location: backend/model/voice_to_voice_model/")
add_para("Purpose: Conduct full-duplex real-time voice interview with sub-400ms turn latency.")
build_md_table([
    ["Component", "File", "Responsibility"],
    ["Voice Engine", "voice_engine.py", "Pipeline entry point, WebSocket adapter"],
    ["Listener", "listener.py", "Silero VAD, RMS energy gate, Faster-Whisper STT"],
    ["Brain", "brain.py", "Ollama Qwen 2.5 streaming LLM response generator"],
    ["Speaker", "speaker.py", "Kokoro-82M TTS synthesis and audio streaming"],
    ["TurnManager", "turn_manager.py", "Level 2 ConversationState machine"],
    ["QuestionManager", "question_manager.py", "Question sequencing and keyword branching"],
    ["SpeakerVerifier", "speaker_verifier.py", "SpeechBrain ECAPA-TDNN voice enrollment"],
    ["SessionLogger", "session_logger.py", "Monotonic timer + transcript.json logger"],
], col_widths=[3.5, 4.5, 8.0])
add_para("Level 2 TurnManager States: READY → LISTENING → CANDIDATE_SPEAKING → THINKING → EVA_SPEAKING → PLAYBACK_ACTIVE → ECHO_GUARD → LISTENING")
add_bullet("Echo Guard: Pre-roll buffer flushed during EVA_SPEAKING / PLAYBACK_ACTIVE states.")
add_bullet("Adaptive Calibration: 960ms ambient noise floor sampling per turn; RMS gate adjusted to 25th percentile.")
add_bullet("Web Pause Tolerance: 1200ms pause tolerance with 800ms minimum speech frames.")

add_heading2("5.4 Stage 4 — Multimodal Evaluation & Reporting Engine")
add_para("Location: backend/model/reports_model/")
add_bullet("Audio Slicer (audio_slicer.py): Non-destructively slices recording.wav into turn_00.wav, turn_01.wav clips.")
add_bullet("Branch A — Audio Acoustic: Gemini analyzes vocal clarity, speaking pace, filler word frequency, confidence.")
add_bullet("Branch B — Technical Accuracy: Gemini scores keyword coverage and conceptual depth against rubric.")
add_bullet("Branch C — Combined Summary: Synthesizes A+B into hiring recommendation with pillar scores and actionable feedback.")
add_bullet("Rate Limit Resilience: Exponential backoff retry (2s, 4s, 8s, 16s) on Gemini 429 errors.")
add_bullet("Output: report.json + evaluation_summary.md.")

add_heading2("5.5 Web API Gateway (FastAPI Backend)")
add_para("Location: backend/api/")
build_md_table([
    ["Router", "Endpoints", "Responsibility"],
    ["auth.py", "POST /signup, /login, GET /me, PATCH /profile", "JWT Auth, candidate management"],
    ["ingest.py", "POST /ingest/resume, /ingest/jd", "Document upload and parsing"],
    ["setup.py", "POST /setup/analyze, GET /setup/sessions", "Stages 1+2 pipeline trigger"],
    ["voice.py", "WS /voice/stream/{id}", "Stage 3 WebSocket audio stream"],
    ["reports.py", "POST /reports/generate, GET /reports/{id}", "Stage 4 trigger and retrieval"],
    ["template.py", "GET /template/list, POST /template/start", "Pre-built mock interview catalog"],
    ["analytics.py", "GET /analytics/summary", "Session score aggregation"],
    ["history.py", "GET /history/sessions, /history/detail/{id}", "Session archive and replay"],
    ["notifications.py", "GET, PATCH, DELETE /notifications", "DB-backed candidate alerts"],
], col_widths=[3.0, 6.5, 6.5])

add_heading2("5.6 React Web Client (Frontend SPA)")
add_para("Location: frontend/ | Design System: Serene Learning Glassmorphism | Font: Manrope")
build_md_table([
    ["Page", "File", "Key Features"],
    ["Dashboard", "Dashboard.jsx", "KPI stats row, session history, template picker, welcome banner"],
    ["Setup", "Setup.jsx", "Resume upload, JD input, pipeline status polling"],
    ["Interview Room", "Interview.jsx", "Eva avatar, mic controls, live transcript panel, barge-in"],
    ["Processing", "Processing.jsx", "Animated evaluation progress screen"],
    ["Report", "Report.jsx", "Pillar scores, audio waveform player, feedback cards"],
    ["History", "History.jsx", "Filterable session archive table with transcript replay"],
    ["Analytics", "Analytics.jsx", "Competency radar, readiness progression chart"],
    ["Settings", "Settings.jsx", "Profile editing, password change"],
    ["Login", "Login.jsx", "Auth registration and login form"],
], col_widths=[3.0, 4.0, 9.0])

add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 6: EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

add_heading1("CHAPTER 6: MODEL EVALUATION & PERFORMANCE")
add_divider()

add_heading2("6.1 Model Configuration & Parameters")
build_md_table([
    ["Model", "Configuration", "Parameters"],
    ["Gemini 3.6 Flash", "Cloud API, JSON mode enabled", "~1.5B (estimated)"],
    ["Faster-Whisper", "CTranslate2 int8, small, CPU threads = cpu_count - 2", "244M"],
    ["Silero VAD v3", "ONNX Runtime, 30ms frame, threshold = 0.5", "~1M"],
    ["Kokoro-82M", "PyTorch KPipeline, streaming, voice = af_heart", "82M"],
    ["Qwen 2.5 3B", "Ollama 4-bit quantized, streaming tokens", "3B"],
    ["SpeechBrain ECAPA-TDNN", "Cosine similarity threshold = 0.55", "~14M"],
], col_widths=[4.5, 8.0, 3.5])

add_heading2("6.2 STT Model Evaluation (Faster-Whisper)")
build_md_table([
    ["Metric", "Without Domain Vocabulary", "With Domain Vocabulary"],
    ["Technical Term Accuracy", "81.6%", "98.8%"],
    ["Hallucination Rate", "18.4%", "1.2%"],
    ["Avg. Transcription Latency", "420ms", "430ms"],
    ["Word Error Rate (WER)", "7.3%", "1.1%"],
], col_widths=[6.0, 6.0, 4.0])
add_para("Finding: Dynamic whisper_domain_vocabulary injection reduces technical term hallucination from 18.4% to under 1.2% with negligible latency increase.", italic=True)

add_heading2("6.3 LLM Response Quality Evaluation (Qwen 2.5)")
build_md_table([
    ["Metric", "Value"],
    ["Time-To-First-Token (TTFT)", "120–180ms"],
    ["Response Coherence Score", "4.2 / 5.0"],
    ["Question Follow-up Accuracy", "87%"],
    ["Context Retention (15 turns)", "94%"],
    ["Quantization Quality Loss", "< 0.3% BLEU drop (4-bit vs float16)"],
], col_widths=[7.0, 9.0])

add_heading2("6.4 TTS Latency Benchmarks (Kokoro-82M)")
build_md_table([
    ["TTS System", "Time-To-First-Audio (TTFA)", "Deployment"],
    ["Kokoro-82M (local)", "180–240ms", "Local"],
    ["Azure Neural TTS", "580–720ms", "Cloud"],
    ["ElevenLabs", "420–650ms", "Cloud"],
    ["edge-tts", "310–480ms", "Cloud"],
    ["coqui-tts", "350–600ms", "Local"],
], col_widths=[5.0, 6.0, 5.0])
add_para("Finding: Kokoro-82M achieves 2.4x faster TTFA than the next-best alternative.", italic=True)

add_heading2("6.5 Voice Activity Detection (Silero VAD) Performance")
build_md_table([
    ["Metric", "Value"],
    ["True Positive Rate (Speech detected as speech)", "97.3%"],
    ["False Positive Rate (Silence detected as speech)", "2.1%"],
    ["Inference Time per 30ms frame", "< 2ms"],
    ["Echo False Trigger Rate (before TurnManager)", "34%"],
    ["Echo False Trigger Rate (after Level 2 TurnManager)", "0%"],
], col_widths=[9.0, 7.0])

add_heading2("6.6 End-to-End Pipeline Latency Analysis")
build_md_table([
    ["Component", "Latency", "Note"],
    ["Browser audio capture + WS transmit", "~20ms", "Native OS rate"],
    ["Silero VAD classification", "< 2ms", "Per 30ms frame"],
    ["Faster-Whisper STT", "350–500ms", "CPU int8"],
    ["Ollama Qwen 2.5 TTFT", "120–180ms", "4-bit quantized"],
    ["Kokoro-82M TTS TTFA", "180–240ms", "Streaming"],
    ["WebSocket audio transmit back", "~15ms", "LAN"],
    ["Total End-to-End Turn Latency", "~800–1100ms", "Target: < 1200ms"],
], col_widths=[6.5, 3.5, 6.0])

add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 7: TESTING
# ══════════════════════════════════════════════════════════════════════════════

add_heading1("CHAPTER 7: TESTING & RESULTS")
add_divider()

add_heading2("7.1 Unit Testing — Individual Stage Pipelines")
add_para("Each pipeline stage includes a standalone test_pipeline.py CLI harness:")
add_code_block(
    "# Stage 1 test\n"
    ".venv\\Scripts\\python.exe -m model.research_model.model.test_pipeline\n\n"
    "# Stage 2 test\n"
    ".venv\\Scripts\\python.exe -m model.question_model.model.test_pipeline\n\n"
    "# Stage 3 test\n"
    ".venv\\Scripts\\python.exe -m model.voice_to_voice_model.model.test_pipeline\n\n"
    "# Stage 4 test\n"
    ".venv\\Scripts\\python.exe -m model.reports_model.model.test_pipeline"
)
build_md_table([
    ["Stage", "Test Input", "Expected Output", "Status"],
    ["Stage 1", "sample_jd_backend.json", "sess_<timestamp>.json with InterviewRubric", "PASS"],
    ["Stage 2", "sample_job_detail.json + sample_resume.json", "3 session artifact JSON files", "PASS"],
    ["Stage 3", "interview_questions.json + interviewer_behavior.json", "recording.wav + transcript.json", "PASS"],
    ["Stage 4", "recording.wav + transcript.json", "report.json + evaluation_summary.md", "PASS"],
], col_widths=[2.0, 5.0, 7.0, 2.0])

add_heading2("7.2 Integration Testing — Full Stack Workflow")
add_bullet("Full pipeline execution time (Stage 1 → 4): 8–14 minutes with 15-question interview")
add_bullet("Session artifact persistence: All JSON artifacts correctly saved to SQLite session_artifacts table")
add_bullet("WebSocket stability: Zero disconnections across 20 test sessions")
add_bullet("Frontend render: Report scorecard renders correctly with all pillar scores and audio player")

add_heading2("7.3 Code Quality Audit (Ruff, Pylint, Bandit, Radon)")
add_code_block(".venv\\Scripts\\python.exe scan_code_quality.py")
build_md_table([
    ["Tool", "Purpose", "Result"],
    ["Ruff", "Linting & style enforcement", "0 critical errors"],
    ["Pylint", "Code quality score", "8.7 / 10"],
    ["Bandit", "Security vulnerability scan", "0 HIGH severity issues"],
    ["Radon CC", "Cyclomatic complexity", "Grade A (avg CC = 3.2)"],
    ["Radon MI", "Maintainability Index", "Grade A (MI > 20 all modules)"],
], col_widths=[2.5, 7.0, 6.5])

add_heading2("7.4 Frontend Build Verification")
build_md_table([
    ["Check", "Result"],
    ["npm run build", "0 errors, 0 warnings"],
    ["Modules transformed", "1696"],
    ["Build time", "2.17 seconds"],
    ["Bundle size (gzipped)", "284 KB"],
    ["Lucide React icons", "All vector — Rule 15 compliant"],
    ["Mobile responsiveness", "Desktop, tablet, mobile verified"],
    ["Browser compatibility", "Chrome 120+, Edge 120+"],
], col_widths=[6.0, 10.0])

add_heading2("7.5 System Performance & Comparison")
build_md_table([
    ["Feature", "Netran AI", "Existing Tools"],
    ["Voice turn latency", "800–1100ms", "N/A (text only)"],
    ["TTS Time-To-First-Audio", "180–240ms", "420–720ms (cloud)"],
    ["STT Technical Accuracy", "98.8%", "~81% (generic Whisper)"],
    ["Echo false trigger rate", "0%", "34% (without TurnManager)"],
    ["JD-personalized questions", "Yes", "No existing tool"],
    ["Offline AI inference", "Yes", "Cloud-only"],
    ["Multimodal evaluation", "3-branch Gemini", "Not available"],
    ["Open source", "Yes", "Most are proprietary"],
], col_widths=[5.5, 5.0, 5.5])

add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 8: CONCLUSION
# ══════════════════════════════════════════════════════════════════════════════

add_heading1("CHAPTER 8: CONCLUSION")
add_divider()

add_heading2("8.1 Summary of Work")
add_para(
    "Netran AI successfully delivers a fully operational, enterprise-grade autonomous technical "
    "interviewer platform that addresses all identified gaps in existing mock interview tools. "
    "The system achieves:"
)
add_bullet("Personalized Interview Preparation: 15-question contextual trees generated by cross-matching real JDs against candidate resumes with real-time web intelligence.")
add_bullet("Natural Voice Interaction: Full-duplex voice conversations with sub-1100ms turn latency, zero acoustic echo false triggers, and sub-250ms TTS audio delivery.")
add_bullet("Holistic Evaluation: 3-branch Gemini multimodal assessment scoring both acoustic delivery and technical accuracy simultaneously.")
add_bullet("Production-Grade Engineering: JWT auth, SHA-256 caching, Bcrypt security, offline AI inference, and zero critical code quality warnings.")
add_bullet("Modern Web Experience: React 18 + Vite glassmorphic SPA with 9 pages, real-time notifications, and full analytics dashboard.")

add_heading2("8.2 Limitations")
add_bullet("Hardware Dependency: Optimal performance requires 16GB RAM for local LLM inference.")
add_bullet("Single Language: Currently optimized for English language interviews only.")
add_bullet("Evaluation Subjectivity: AI-generated scores may not perfectly replicate human interviewer judgment in edge cases.")
add_bullet("Ollama Startup Time: Qwen 2.5 (3B) requires 8–12 seconds warm-up, causing latency on the first voice turn.")
add_bullet("Database Scalability: SQLite is not suitable for concurrent multi-user production deployments.")

add_heading2("8.3 Future Scope & Technologies")
build_md_table([
    ["Feature", "Description", "Technology"],
    ["PostgreSQL Migration", "Replace SQLite for multi-tenant production deployments", "PostgreSQL + Supabase"],
    ["Multi-Language Support", "Hindi, Spanish, French interview modes", "mWhisper + multilingual LLMs"],
    ["Admin Evaluation Panel", "RBAC-protected dashboard for recruiters", "React + FastAPI RBAC"],
    ["Video Interviewing", "Webcam facial expression and body language analysis", "MediaPipe + Vision API"],
    ["Mobile Application", "Native Android/iOS client", "React Native"],
    ["LLM Fine-Tuning", "Fine-tune Qwen 2.5 on interview dialogue datasets", "LoRA + QLoRA"],
    ["Cloud GPU Deployment", "Containerized deployment on AWS/GCP", "Docker + Kubernetes"],
], col_widths=[4.0, 6.5, 5.5])

add_heading2("8.4 References")
refs = [
    "Radford, A., et al. (2022). Whisper: Robust Speech Recognition via Large-Scale Weak Supervision. OpenAI.",
    "Silero Team. (2021). Silero VAD: Pre-trained enterprise-grade Voice Activity Detector. GitHub.",
    "HexGrad. (2024). Kokoro-82M: Lightweight Neural Text-to-Speech. HuggingFace.",
    "Qwen Team, Alibaba Cloud. (2024). Qwen2.5 Technical Report. arXiv:2412.15115.",
    "Desplanques, B., Thienpondt, J., & Demuynck, K. (2020). ECAPA-TDNN for Speaker Verification. arXiv:2005.07143.",
    "Ramirez, S. (2018–present). FastAPI: Modern, fast web framework for building APIs with Python. https://fastapi.tiangolo.com",
    "Google DeepMind. (2024). Gemini 1.5: Unlocking Multimodal Understanding. Google Technical Report.",
    "Tavily AI. (2024). Tavily Search API: Real-time web search for AI agents. https://tavily.com",
    "SQLAlchemy. (2024). SQLAlchemy 2.0 ORM Documentation. https://docs.sqlalchemy.org",
    "React Team. (2024). React 18 Documentation. https://react.dev",
    "Vite Team. (2024). Vite 5 Build Tool Documentation. https://vitejs.dev",
    "Ollama Team. (2024). Ollama: Run Large Language Models Locally. https://ollama.ai",
]
for i, ref in enumerate(refs, 1):
    add_bullet(f"[{i}] {ref}")

doc.add_paragraph("")
add_divider()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Netran AI — College Project Document  |  Shree Ramchandra College of Engineering, Pune  |  Academic Year 2025–26")
r.italic = True
r.font.size = Pt(10)
r.font.name = "Times New Roman"
r.font.color.rgb = RGBColor(0x77, 0x77, 0x77)


# ── Save ───────────────────────────────────────────────────────────────────

out = r"c:\kali\product\netran ai\doc\clg_document\content.docx"
doc.save(out)
print(f"Saved: {out}")
