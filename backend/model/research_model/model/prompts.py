"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: prompts.py
Description: Centralized system prompts and instruction templates for Stage 1.
             Upgraded to support 3-vector market intelligence search queries and
             a comprehensive rubric schema (Salary, HR signals, Soft Skills).
"""

# Prompt template used by jd_parser.py to extract role details, tech stack, and 3-vector search queries
JD_PARSER_PROMPT_TEMPLATE = """
Analyze the following Job Description (JD) text as an expert Technical Recruiter and Engineering Director.

Extract:
1. Role title
2. Company name (if mentioned, otherwise "Target Company")
3. Target Seniority level (e.g., Junior, Mid, Senior, Lead, Staff)
4. Core technical stack, frameworks, databases, and infrastructure tools
5. Exactly 3 multi-vector search queries to gather real-world intelligence:
   - Query 1 (Technical Interview Questions): Target real-world coding and system design interview questions on trusted engineering sites (LeetCode, Glassdoor, GitHub, Reddit, GeeksforGeeks).
   - Query 2 (Market & Compensation): Target salary benchmarks, compensation bands (USD & INR), and market demand trends.
   - Query 3 (HR & Recruiter Lens): Target recruiter screening signals, hiring bar standards, green flags, and red flags for this stack.

Job Description:
\"\"\"
{jd_text}
\"\"\"

Return strictly valid JSON matching this exact structure:
{{
  "role": "Extracted Role Title",
  "company": "Company Name or Target Company",
  "target_seniority": "Junior | Mid | Senior | Lead | Staff",
  "tech_stack": ["tech1", "tech2", "tech3"],
  "search_queries": [
    "Query 1: Technical interview questions and system design topics",
    "Query 2: Salary bands compensation trends market demand 2026",
    "Query 3: Recruiter evaluation green flags red flags resume signals"
  ]
}}
"""

# Prompt template used by rubric_generator.py to synthesize Market & Technical Rubrics
RUBRIC_GENERATOR_PROMPT_TEMPLATE = """
You are an elite Tech Lead, Talent Strategist, and Executive Hiring Bar Raiser creating a multi-dimensional assessment rubric for an AI interview platform.

Job Description:
\"\"\"
{jd_text}
\"\"\"

Parsed Role Metadata:
- Role: {role}
- Company: {company}
- Target Seniority: {target_seniority}
- Tech Stack: {tech_stack}

Live Web Context & Market Intelligence:
\"\"\"
{context_str}
\"\"\"

Synthesize all available data into a comprehensive Market & Technical Interview Rubric.
Ensure salary estimations reflect realistic market standards (both USD base/year and INR LPA CTC ranges).
Define concrete, actionable green and red flags for HR/Interviewers, along with critical soft skills and evaluation methods.

Return strictly valid JSON matching this exact structure:
{{
  "roleOverview": "Detailed summary of role expectations, technical bar, and target candidate profile",
  "marketIntelligence": {{
    "salary_benchmark": {{
      "usd_range": "e.g., $140,000 - $190,000 Base / Year + Equity",
      "inr_range": "e.g., ₹28.0 LPA - ₹55.0 LPA CTC",
      "compensation_notes": "Key drivers for premium compensation (e.g., specific stack mastery, high concurrency experience)"
    }},
    "market_demand_level": "High | Very High | Niche",
    "hiring_landscape": "Overview of current industry demand, competition, and stack trends",
    "top_hiring_company_types": [
      "Company Type 1 (e.g., AI Infrastructure SaaS)",
      "Company Type 2 (e.g., High-Volume Fintech Platforms)"
    ]
  }},
  "hrRecruiterLens": {{
    "what_hr_looks_for": [
      "Key resume signal or quantified achievement 1",
      "Key resume signal or quantified achievement 2"
    ],
    "green_flags": [
      "Positive indicator 1 during initial candidate screening",
      "Positive indicator 2 during technical deep dives"
    ],
    "red_flags": [
      "Warning sign 1 (e.g., over-reliance on ORMs without raw SQL understanding)",
      "Warning sign 2 (e.g., inability to articulate system architectural trade-offs)"
    ]
  }},
  "skillRequirements": {{
    "must_have_hard_skills": ["Skill 1", "Skill 2", "Skill 3"],
    "nice_to_have_hard_skills": ["Skill 1", "Skill 2"],
    "critical_soft_skills": [
      {{
        "skill": "Soft Skill Name (e.g., Architectural Articulation)",
        "why_it_matters": "Why this soft skill is essential for this role level",
        "evaluation_method": "How an interviewer should test/observe this during the call"
      }}
    ]
  }},
  "keyTechnicalPillars": [
    "Pillar 1: Core Technical Focus Area",
    "Pillar 2: System Design / Data Engineering Focus Area",
    "Pillar 3: Infrastructure / Reliability Focus Area"
  ],
  "expectedInterviewTopics": [
    {{
      "category": "Category Name (e.g., Async Python Systems)",
      "difficulty": "Junior" | "Mid" | "Senior" | "Lead",
      "example_questions": [
        "Scenario-based interview question 1",
        "Scenario-based interview question 2",
        "Scenario-based interview question 3"
      ]
    }}
  ]
}}
"""