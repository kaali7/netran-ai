"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: prompts.py
Description: Centralized system prompts and instruction templates for Stage 1.
             Developers and operators can modify Stage 1 system prompts here.
"""

# Prompt template used by jd_parser.py to extract role details, tech stack, and search queries
JD_PARSER_PROMPT_TEMPLATE = """
Analyze the following Job Description (JD) text and extract:
1. Role title
2. Company name (if mentioned, otherwise "Target Company")
3. Core technical stack and skills
4. 2-3 specific search queries to find actual real-world interview questions and interview rubrics for this specific role and company on trusted engineering sites like Glassdoor, LeetCode, GitHub.

Job Description:
\"\"\"
{jd_text}
\"\"\"

Return strictly JSON matching this structure:
{{
  "role": "Role Title",
  "company": "Company Name",
  "tech_stack": ["tech1", "tech2"],
  "search_queries": ["query 1", "query 2"]
}}
"""

# Prompt template used by rubric_generator.py to synthesize comprehensive Interview Rubrics
RUBRIC_GENERATOR_PROMPT_TEMPLATE = """
You are an elite Tech Lead and Hiring Bar Raiser creating an interview assessment rubric.

Job Description:
\"\"\"
{jd_text}
\"\"\"

Extracted Details:
Role: {role}
Company: {company}
Tech Stack: {tech_stack}

Live Market Intelligence & Interview Context:
\"\"\"
{context_str}
\"\"\"

Generate a comprehensive, highly accurate Interview Rubric.
Return strictly valid JSON matching this exact structure:
{{
  "roleOverview": "Summary of role expectations and target candidate profile",
  "keyTechnicalPillars": ["Pillar 1", "Pillar 2", "Pillar 3"],
  "expectedInterviewTopics": [
    {{
      "category": "System Design / Data Structures / Core Tech",
      "difficulty": "Junior" | "Mid" | "Senior",
      "example_questions": [
        "Question 1",
        "Question 2",
        "Question 3"
      ]
    }}
  ]
}}
"""
