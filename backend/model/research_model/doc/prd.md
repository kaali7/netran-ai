# Product Requirements Document (PRD)

## Project Name: Netran AI (SAMWINI) - Subsystem: JD Research & Market Intelligence Engine

**Document Type:** Technical & Functional Specifications for Web-Augmented Interview Generation
**Academic Year:** 2026-27

**Authors:** Samta Sakha & Ashwini Prajapati

---

## 1. Project Overview & Objective

The JD Research & Market Intelligence Engine is a critical backend subsystem of Netran AI designed to eliminate generic, predictable AI interview questions. By actively querying the live internet for recent interview rubrics, technical expectations, and real-world questions from trusted engineering sources, this module synthesizes raw Job Descriptions (JDs) with current market intelligence. The objective is to force the AI interviewer to generate highly accurate, company-specific, and domain-relevant questions that mirror actual industry standards.

### 1.1 Problem Statement

Standard AI-generated mock interviews often suffer from:

* **Generic Output:** Relying solely on a base LLM's pre-trained knowledge results in basic, textbook-style questions rather than real-world technical deep dives.
* **Lack of Company Context:** A raw JD rarely explains the *actual* difficulty of an interview at specific tech companies.
* **Format Instability:** Unstructured LLM outputs often break the frontend UI when parsing dynamic question categories or difficulty tiers.

---

## 2. Scope & Target Audience

### 2.1 Primary Users

* **Students & Job Seekers:** Benefits from practicing against the exact types of questions recently asked at their target companies (e.g., LeetCode patterns, system design expectations).
* **Netran AI System Architecture:** This module serves as the primary data-structuring layer, guaranteeing that the downstream Voice-to-Voice LLM receives perfectly formatted, JSON-structured interview rubrics to execute the voice loop.

---

## 3. Core Features & Functional Requirements

### 3.1 Targeted LLM Query Generation

* **JD Parsing & Extraction:** The system must evaluate the user's uploaded JD to extract the target role, company name, and core technology stack.
* **Dynamic Search Formulation:** An initial LLM prompt generates highly specific search queries (e.g., "Senior Frontend Engineer interview rubric and technical questions glassdoor").

### 3.2 Trusted Domain Web Search

* **Tavily API Integration:** The system will execute web searches strictly filtered to high-trust engineering domains (e.g., `leetcode.com`, `glassdoor.com`, `github.com`). Tavily's AI-optimized search is used for clean, structured web content extraction without scraping barriers.
* **Fallback Resilience:** If the search engine fails to retrieve clean data or returns a silent failure (e.g., API rate limit or empty result set), the system must automatically pivot to a fallback instruction, relying on the LLM's internal baseline knowledge rather than failing the application loop.

### 3.3 Strict Structured Output (JSON) Generation

* **Schema Enforcement:** The system will pass the retrieved web context and raw JD into Gemini. It will utilize the API's native structured output configuration to guarantee the model's response is in a predictable JSON format.
* **Prompt Optimization:** To maintain optimal output quality and prevent performance degradation, the expected JSON structure will only be defined within the schema object and will not be duplicated inside the text prompt.
* **String Enums:** Categorical data, such as question difficulty (e.g., "Junior", "Senior"), must be enforced exclusively using string-based enums within the schema.

---

## 4. Technical Specifications & Architecture

### 4.1 Backend Pipeline Stack

* **Language & Framework:** Python with **FastAPI** to handle high-performance, asynchronous REST API routing and orchestrate the external API calls efficiently.
* **Data Validation:** **Pydantic** models will be utilized to define, enforce, and validate the strict JSON schema structures expected from the LLM, seamlessly integrating with FastAPI's native architecture.
* **Search Infrastructure:** `tavily-python` (Tavily Search API Python SDK) for real-time web data extraction and domain whitelisting. API key stored as `TAVILY_API_KEY` in `.env`.
* **Reasoning Engine:** `google-genai` SDK (`from google import genai`, model: `gemini-3.6-flash`) for synthesizing the web context into a structured rubric. API key stored as `GEMINI_API_KEY` in `.env`.

### 4.2 Data Layer & Schema Constraints

* **Output Specification:** The resulting JSON must strictly contain `roleOverview`, `keyTechnicalPillars`, and `expectedInterviewTopics` (an array containing specific categories, string-based difficulty levels, and example questions).
* **Data Caching (PostgreSQL):** To reduce API costs and latency, generated interview rubrics will be hashed against the input JD and stored in the database. Repeat JD submissions will retrieve the cached structured JSON instead of re-triggering the web search.

---

## 5. Development Timeline (Mapped to Main 8-Week Sprint)

This subsystem will be built during the core AI integration phase of the overarching project:

* **Week 3 (Early):** Setup FastAPI endpoints, Exa API Python connections, and test domain whitelisting logic against sample JDs.
* **Week 3 (Late):** Implement the Gemini `response_schema` generation using Pydantic models and test JSON extraction reliability.
* **Week 4 (Early):** Build the fallback error-handling logic for when web searches return sparse or blocked data.
* **Week 4 (Late):** Wire the generated JSON rubric output directly into the prompt context for the Voice-to-Voice streaming module.
* **Week 7:** End-to-end integration testing (verifying that a PDF upload successfully triggers the FastAPI route, searches the web, structures the JSON, and begins the voice interview).

---

## 6. Future Scope

* **Dynamic Domain Swapping:** Automatically adjust the trusted search domains based on the JD (e.g., swapping to Kaggle or Arxiv for Data Science roles).
* **URL Source Citations:** Passing the specific Exa search URLs from the FastAPI backend to the frontend so the user can click through to read the original Glassdoor or LeetCode posts after their mock interview concludes.