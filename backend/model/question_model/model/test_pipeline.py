"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: test_pipeline.py
Description: Standalone CLI test harness for verifying Stage 2 question tree and prompt generation.
"""

import os
import sys
import logging
from datetime import datetime

# Adjust Python path to allow imports if run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from model.question_model.model.question_generator import generate_stage2_output

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_dummy_resume(path: str):
    content = """
    John Doe
    Software Engineer

    Experience:
    - Backend Developer at TechCorp (2020 - Present)
      Built scalable microservices using Python, FastAPI, and PostgreSQL.
      Deployed infrastructure using Docker and Kubernetes.
      Implemented OAuth2 authentication and Redis caching, improving API latency by 40%.
    
    - Junior Web Developer at WebSolutions (2018 - 2020)
      Developed interactive frontend components using React and Redux.
      Styled applications using Tailwind CSS.
      Maintained legacy PHP/Laravel applications.
    
    Education:
    - B.S. in Computer Science, University of Technology (2014 - 2018)

    Skills:
    Python, JavaScript, React, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, AWS.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    logger.info(f"Created dummy resume at {path}")

def run_test():
    # Setup test paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_resume_path = os.path.join(current_dir, "dummy_resume.txt")
    
    # Create dummy artifacts
    create_dummy_resume(test_resume_path)
    
    dummy_jd = """
    Role: Senior Backend Engineer
    Company: InnovateAI
    
    Key Technical Pillars:
    - Python (FastAPI/Django)
    - System Design & Microservices architecture
    - Relational Databases (PostgreSQL) and NoSQL
    - Cloud Infrastructure (AWS) and Containerization (Docker, K8s)
    - High-concurrency systems, asynchronous programming
    
    Role Overview: We are looking for a senior backend engineer who can scale our AI infrastructure, ensure high availability, and build robust APIs.
    """
    
    session_id = f"sess_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = os.path.abspath(os.path.join(current_dir, "test_output", session_id))
    
    logger.info(f"Starting Stage 2 Pipeline Test for session: {session_id}")
    
    try:
        output = generate_stage2_output(
            session_id=session_id,
            jd_text=dummy_jd,
            resume_path=test_resume_path,
            target_seniority="Senior",
            output_dir=output_dir
        )
        
        logger.info("✅ Pipeline Test Successful!")
        logger.info(f"Session ID: {output.session_id}")
        logger.info(f"Generated {len(output.question_tree)} questions.")
        logger.info(f"System Prompt Length: {len(output.interviewer_system_prompt)} characters.")
        
        print("\n--- SAMPLE GENERATED PROMPT ---")
        print(output.interviewer_system_prompt[:500] + "...\n")
        
        print("--- FIRST QUESTION ---")
        print(output.question_tree[0].model_dump_json(indent=2))
        
        print(f"\nCheck the output directory for artifacts: {output_dir}")
        
    except Exception as e:
        logger.error(f"❌ Pipeline Test Failed: {e}")
        
if __name__ == "__main__":
    run_test()
