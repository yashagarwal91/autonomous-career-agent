"""
Agent Tools — Autonomous Career Intelligence Agent
5 tools used by the LangGraph ReAct agent
"""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.tools import tool
from tavily import TavilyClient
from db.database import SessionLocal, JobPosting
from dotenv import load_dotenv

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def search_job_postings(query: str) -> str:
    """
    Search the web for latest job postings and required skills.
    Use this to find current market demand for a specific role.

    Args:
        query: Job role to search (e.g. 'Senior AI Engineer India 2025 skills required')

    Returns:
        Summary of job postings with required skills
    """
    try:
        results = tavily.search(
            query=query,
            search_depth="basic",
            max_results=5
        )

        if not results.get("results"):
            return "No job postings found for this query."

        output = []
        for r in results["results"]:
            output.append(f"Source: {r.get('url', 'N/A')}")
            output.append(f"Title: {r.get('title', 'N/A')}")
            output.append(f"Summary: {r.get('content', 'N/A')[:300]}")
            output.append("---")

        return "\n".join(output)

    except Exception as e:
        return f"Web search failed: {str(e)}. Try a different query."


@tool
def query_job_database(role: str) -> str:
    """
    Query the local job database for stored job postings matching a role.
    Returns required skills, salary ranges, and experience levels.

    Args:
        role: Job role to search in DB (e.g. 'AI Engineer', 'ML Engineer')

    Returns:
        Matching jobs with required skills and salary info
    """
    db = SessionLocal()
    try:
        jobs = db.query(JobPosting).filter(
            JobPosting.title.ilike(f"%{role}%")
        ).all()

        if not jobs:
            # fallback to all jobs if no match found
            jobs = db.query(JobPosting).limit(5).all()
            if not jobs:
                return "No jobs found in database."

        output = []
        for job in jobs[:5]:
            output.append(f"Role         : {job.title}")
            output.append(f"Company      : {job.company}")
            output.append(f"Level        : {job.experience_level}")
            output.append(f"Required     : {job.required_skills}")
            output.append(f"Nice to Have : {job.nice_to_have_skills}")
            output.append(f"Salary (LPA) : {job.salary_min} - {job.salary_max}")
            output.append("---")

        return "\n".join(output)

    except Exception as e:
        return f"Database query failed: {str(e)}"

    finally:
        db.close()


@tool
def analyze_skill_gaps(user_skills: str, required_skills: str) -> str:
    """
    Compare user's current skills against job required skills.
    Identifies missing skills and proficiency gaps.

    Args:
        user_skills    : Comma-separated list of user's skills
        required_skills: Comma-separated list of skills required for the role

    Returns:
        Structured gap analysis with missing and matching skills
    """
    try:
        user_set     = {s.strip().lower() for s in user_skills.split(",") if s.strip()}
        required_set = {s.strip().lower() for s in required_skills.split(",") if s.strip()}

        matching = []
        gaps     = []

        for skill in required_set:
            # partial match handles cases like "langchain" vs "langchain-community"
            matched = any(skill in u or u in skill for u in user_set)
            if matched:
                matching.append(skill.title())
            else:
                gaps.append(skill.title())

        match_pct = round((len(matching) / len(required_set)) * 100) if required_set else 0

        result = {
            "match_percentage": f"{match_pct}%",
            "matching_skills" : matching,
            "skill_gaps"      : gaps,
            "total_required"  : len(required_set),
            "total_matching"  : len(matching),
            "total_gaps"      : len(gaps)
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return f"Gap analysis failed: {str(e)}"


@tool
def search_learning_resources(skill: str) -> str:
    """
    Search the web for the best learning resources for a specific skill.
    Finds courses, tutorials, documentation, and projects.

    Args:
        skill: Specific skill to find resources for (e.g. 'LangGraph tutorial 2025')

    Returns:
        Top learning resources with links and descriptions
    """
    try:
        results = tavily.search(
            query=f"best way to learn {skill} tutorial course 2025",
            search_depth="basic",
            max_results=3
        )

        if not results.get("results"):
            return f"No resources found for {skill}."

        output = [f"Learning Resources for: {skill}", ""]
        for r in results["results"]:
            output.append(f"📚 {r.get('title', 'N/A')}")
            output.append(f"   {r.get('url', 'N/A')}")
            output.append(f"   {r.get('content', '')[:200]}")
            output.append("")

        return "\n".join(output)

    except Exception as e:
        return f"Resource search failed: {str(e)}. Returning generic advice."


@tool
def analyze_market_trends(role: str) -> str:
    """
    Analyze current job market trends for a specific role.
    Finds salary benchmarks, in-demand skills, and hiring outlook.

    Args:
        role: Job role to analyze (e.g. 'AI Engineer India 2025')

    Returns:
        Market trends including salary, demand, and top skills
    """
    try:
        results = tavily.search(
            query=f"{role} salary trends hiring demand India 2025",
            search_depth="basic",
            max_results=4
        )

        if not results.get("results"):
            return f"No market trend data found for {role}."

        output = [f"Market Trends: {role}", ""]
        for r in results["results"]:
            output.append(f"→ {r.get('title', 'N/A')}")
            output.append(f"  {r.get('content', '')[:250]}")
            output.append("")

        return "\n".join(output)

    except Exception as e:
        return f"Market trend search failed: {str(e)}"


tools = [
    search_job_postings,
    query_job_database,
    analyze_skill_gaps,
    search_learning_resources,
    analyze_market_trends
]