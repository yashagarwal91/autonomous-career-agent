"""
Resume Parser — Autonomous Career Intelligence Agent
Extracts raw text and skills from uploaded PDF resume
Uses PyMuPDF for PDF reading + Groq LLM for skill extraction
"""

import os
import fitz  # PyMuPDF
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()


llm = ChatGroq(
    model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
    temperature=0,
    max_tokens=2048,
    api_key=os.getenv("GROQ_API_KEY")
)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract raw text from PDF resume using PyMuPDF.
    Handles multi-page resumes gracefully.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume not found at: {pdf_path}")

    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            text += f"\n--- Page {page_num + 1} ---\n{page_text}"
        doc.close()
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF: {str(e)}")

    if not text.strip():
        raise ValueError("PDF appears to be empty or scanned image — cannot extract text")

    return text.strip()


def extract_skills_from_text(resume_text: str) -> list[str]:
    """
    Use Groq LLM to intelligently extract technical skills from resume text.
    Returns a clean deduplicated list of skills.
    """
    system_prompt = """You are a technical resume parser.
Your job is to extract ONLY technical skills from resume text.

Rules:
- Include: programming languages, frameworks, tools, platforms, methodologies
- Exclude: soft skills, company names, job titles, education degrees
- Normalize: "lang chain" → "LangChain", "open ai" → "OpenAI"
- Deduplicate: list each skill only once
- Return ONLY a comma-separated list, nothing else

Example output:
Python, FastAPI, LangChain, LangGraph, Docker, PostgreSQL, AWS, RAG, LLMs"""

    user_prompt = f"""Extract all technical skills from this resume:

{resume_text[:4000]}

Return only a comma-separated list of skills."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        raw    = response.content.strip()
        skills = [s.strip() for s in raw.split(",") if s.strip()]
        skills = list(dict.fromkeys(skills))  # dedupe while keeping order

        return skills

    except Exception as e:
        raise RuntimeError(f"Skill extraction failed: {str(e)}")


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes directly.
    Used when Streamlit uploads a file (no disk path needed).
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page_num, page in enumerate(doc):
            text += f"\n--- Page {page_num + 1} ---\n{page.get_text('text')}"
        doc.close()
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF bytes: {str(e)}")


def parse_resume(pdf_input) -> dict:
    """
    Main entry point — accepts file path (str) or bytes (Streamlit upload).

    Returns:
        {
            "resume_text": str,
            "extracted_skills": list[str]
        }
    """
    if isinstance(pdf_input, bytes):
        resume_text = extract_text_from_bytes(pdf_input)
    else:
        resume_text = extract_text_from_pdf(pdf_input)

    extracted_skills = extract_skills_from_text(resume_text)

    return {
        "resume_text"     : resume_text,
        "extracted_skills": extracted_skills
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python resume_parser.py <resume.pdf>")
        sys.exit(1)

    result = parse_resume(sys.argv[1])
    print(f"\nextracted {len(result['extracted_skills'])} skills:")
    for skill in result["extracted_skills"]:
        print(f"  {skill}")