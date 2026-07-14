"""
Agent Graph — Autonomous Career Intelligence Agent
LangGraph StateGraph with ReAct pattern + 4 HITL interrupt points
"""

import os
import sys
import json
import uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.tools import (
    tools,
    search_job_postings,
    query_job_database,
    analyze_skill_gaps,
    search_learning_resources,
    analyze_market_trends
)
from utils.resume_parser import parse_resume
from db.database import SessionLocal, UserSession
from dotenv import load_dotenv

load_dotenv()


llm = ChatGroq(
    model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
    temperature=0,
    max_tokens=int(os.getenv("MAX_TOKENS", 4096)),
    api_key=os.getenv("GROQ_API_KEY")
)
llm_with_tools = llm.bind_tools(tools)

TOOL_MAP = {t.name: t for t in tools}


def execute_tool_call(tool_call: dict) -> str:
    name    = tool_call["name"]
    args    = tool_call["args"]
    tool_fn = TOOL_MAP.get(name)

    if not tool_fn:
        return f"tool '{name}' not found."

    try:
        result = tool_fn.invoke(args)
        return str(result)
    except Exception as e:
        return f"tool '{name}' failed: {str(e)}"


def run_react_loop(system_prompt: str, user_prompt: str, trace: list) -> tuple[str, list]:
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            trace.append(f"✅ Agent completed reasoning in {iteration} step(s)")
            return response.content, trace

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            trace.append(f"🔧 Calling tool: {tool_name}")

            result = execute_tool_call(tool_call)
            trace.append(f"📥 Tool result received from: {tool_name}")

            messages.append(ToolMessage(
                content=result,
                tool_call_id=tool_call["id"]
            ))

    return "Max iterations reached. Partial results returned.", trace


def parse_resume_node(state: AgentState) -> dict:
    trace = state.get("reasoning_trace", [])
    trace.append("📄 Parsing uploaded resume...")

    try:
        result = parse_resume(state["resume_text"])
        skills = result["extracted_skills"]
        trace.append(f"✅ Extracted {len(skills)} skills from resume")

        return {
            "extracted_skills": skills,
            "reasoning_trace" : trace,
            "current_node"    : "parse_resume"
        }
    except Exception as e:
        return {
            "error"          : f"Resume parsing failed: {str(e)}",
            "reasoning_trace": trace,
            "current_node"   : "parse_resume"
        }


def skill_review_node(state: AgentState) -> dict:
    trace = state.get("reasoning_trace", [])
    trace.append("⏸️  Waiting for user to confirm extracted skills...")

    # graph pauses here until user responds
    human_response = interrupt({
        "type"            : "skill_review",
        "message"         : "I extracted these skills from your resume. Please review and confirm.",
        "extracted_skills": state.get("extracted_skills", [])
    })

    confirmed = human_response.get("confirmed_skills", state["extracted_skills"])
    trace.append(f"✅ User confirmed {len(confirmed)} skills")

    return {
        "confirmed_skills": confirmed,
        "skills_confirmed": True,
        "reasoning_trace" : trace,
        "current_node"    : "skill_review"
    }


def search_jobs_node(state: AgentState) -> dict:
    trace = state.get("reasoning_trace", [])
    trace.append("🔍 Searching job market — web + database...")

    skills_str = ", ".join(state.get("confirmed_skills", []))

    system_prompt = """You are a job market analyst.
Use the available tools to:
1. Search live job postings for AI/ML roles in India
2. Query the local job database for stored roles
3. Analyze current market trends

After gathering data, return a JSON with:
{
  "available_roles": ["list of 4-5 distinct job titles found"],
  "market_summary": "2-3 sentence market overview"
}
Return ONLY valid JSON, no extra text."""

    user_prompt = f"""Find relevant job roles for someone with these skills: {skills_str}
Search for AI/ML/Data Science roles in India 2025.
Return the JSON response."""

    response_text, trace = run_react_loop(system_prompt, user_prompt, trace)

    try:
        clean = response_text.strip().replace("```json", "").replace("```", "")
        data  = json.loads(clean)
        roles = data.get("available_roles", [])
    except Exception:
        # llm occasionally returns malformed json — fallback to sensible defaults
        roles = ["AI Engineer", "ML Engineer", "Senior AI Engineer", "NLP Engineer", "Data Scientist"]
        trace.append("⚠️  Used fallback roles — JSON parse failed")

    return {
        "available_roles": roles,
        "reasoning_trace": trace,
        "current_node"   : "search_jobs"
    }


def role_selection_node(state: AgentState) -> dict:
    trace = state.get("reasoning_trace", [])
    trace.append("⏸️  Waiting for user to select target role...")

    human_response = interrupt({
        "type"          : "role_selection",
        "message"       : "Which role do you want to target?",
        "available_roles": state.get("available_roles", [])
    })

    role = human_response.get("target_role", "AI Engineer")
    trace.append(f"✅ User selected role: {role}")

    return {
        "target_role"    : role,
        "reasoning_trace": trace,
        "current_node"   : "role_selection"
    }


def gap_analysis_node(state: AgentState) -> dict:
    trace = state.get("reasoning_trace", [])
    trace.append(f"📊 Analyzing skill gaps for: {state.get('target_role')}...")

    db_result = query_job_database.invoke({"role": state.get("target_role", "")})

    required_skills_str = ""
    for line in db_result.split("\n"):
        if line.startswith("Required"):
            required_skills_str = line.split(":", 1)[-1].strip()
            break

    if not required_skills_str:
        required_skills_str = "Python,LangChain,LangGraph,FastAPI,Docker,SQL,LLMs,Vector Databases"

    gap_result = analyze_skill_gaps.invoke({
        "user_skills"    : ", ".join(state.get("confirmed_skills", [])),
        "required_skills": required_skills_str
    })

    try:
        gap_data  = json.loads(gap_result)
        gaps      = gap_data.get("skill_gaps", [])
        match_pct = gap_data.get("match_percentage", "0%")
    except Exception:
        gaps      = []
        match_pct = "N/A"

    required_list = [s.strip() for s in required_skills_str.split(",")]
    trace.append(f"✅ Gap analysis done — {match_pct} match, {len(gaps)} gaps found")

    return {
        "required_skills": required_list,
        "skill_gaps"     : gaps,
        "reasoning_trace": trace,
        "current_node"   : "gap_analysis"
    }


def gap_prioritization_node(state: AgentState) -> dict:
    trace = state.get("reasoning_trace", [])
    gaps  = state.get("skill_gaps", [])
    trace.append("⏸️  Waiting for user to prioritize skill gaps...")

    human_response = interrupt({
        "type"      : "gap_prioritization",
        "message"   : f"I found {len(gaps)} skill gaps. Select up to 3 to focus on first.",
        "skill_gaps": gaps
    })

    prioritized = human_response.get("prioritized_gaps", gaps[:3])
    trace.append(f"✅ User prioritized {len(prioritized)} gaps: {', '.join(prioritized)}")

    return {
        "prioritized_gaps": prioritized,
        "reasoning_trace" : trace,
        "current_node"    : "gap_prioritization"
    }


def generate_plan_node(state: AgentState) -> dict:
    trace = state.get("reasoning_trace", [])
    gaps  = state.get("prioritized_gaps", [])
    role  = state.get("target_role", "AI Engineer")
    trace.append(f"📚 Generating learning plan for {len(gaps)} priority skills...")

    system_prompt = """You are a career development coach.
Search for the best learning resources for each skill.
Then return a structured learning plan as JSON:
{
  "target_role": "role name",
  "total_duration": "X months",
  "skills": [
    {
      "skill": "skill name",
      "duration": "X weeks",
      "resources": [{"title": "", "url": "", "type": "course/doc/project"}],
      "milestone": "what you'll be able to do after"
    }
  ],
  "final_project": "capstone project idea"
}
Return ONLY valid JSON."""

    user_prompt = f"""Create a learning plan for these skills: {', '.join(gaps)}
Target role: {role}
Use the search tool to find specific resources for each skill."""

    response_text, trace = run_react_loop(system_prompt, user_prompt, trace)

    try:
        clean = response_text.strip().replace("```json", "").replace("```", "")
        plan  = json.loads(clean)
    except Exception:
        # fallback if llm returns bad json
        plan = {
            "target_role"   : role,
            "total_duration": "3 months",
            "skills"        : [{"skill": g, "duration": "4 weeks", "resources": [], "milestone": f"Build a project using {g}"} for g in gaps],
            "final_project" : f"Build a complete {role} portfolio project"
        }
        trace.append("⚠️  Used fallback plan structure")

    return {
        "learning_plan"  : plan,
        "reasoning_trace": trace,
        "current_node"   : "generate_plan"
    }


def plan_approval_node(state: AgentState) -> dict:
    trace = state.get("reasoning_trace", [])
    trace.append("⏸️  Waiting for user to approve learning plan...")

    human_response = interrupt({
        "type"         : "plan_approval",
        "message"      : "Here is your personalized learning plan. Do you approve?",
        "learning_plan": state.get("learning_plan", {})
    })

    approved = human_response.get("approved", True)
    trace.append(f"✅ User {'approved' if approved else 'rejected'} the plan")

    return {
        "plan_approved"  : approved,
        "reasoning_trace": trace,
        "current_node"   : "plan_approval"
    }


def finalize_node(state: AgentState) -> dict:
    trace = state.get("reasoning_trace", [])
    trace.append("💾 Saving results and evaluating plan quality...")

    plan  = state.get("learning_plan", {})
    gaps  = state.get("prioritized_gaps", [])
    score = 0.0

    if plan.get("skills"):         score += 0.4
    if plan.get("final_project"):  score += 0.2
    if len(gaps) > 0:              score += 0.2
    if plan.get("total_duration"): score += 0.2

    score = round(score, 2)
    feedback = (
        "Excellent plan with clear structure and resources."
        if score >= 0.8 else
        "Good plan. Consider adding more specific resources."
        if score >= 0.5 else
        "Basic plan generated. Manual refinement recommended."
    )

    db = SessionLocal()
    try:
        session = UserSession(
            session_id    = state.get("session_id", str(uuid.uuid4())),
            resume_skills = ", ".join(state.get("confirmed_skills", [])),
            target_role   = state.get("target_role", ""),
            skill_gaps    = ", ".join(state.get("skill_gaps", [])),
            learning_plan = json.dumps(plan),
            eval_score    = score
        )
        db.add(session)
        db.commit()
        trace.append(f"✅ Session saved — eval score: {score}")
    except Exception as e:
        trace.append(f"⚠️  DB save failed: {str(e)}")
    finally:
        db.close()

    return {
        "eval_score"     : score,
        "eval_feedback"  : feedback,
        "reasoning_trace": trace,
        "current_node"   : "finalize"
    }


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("parse_resume",       parse_resume_node)
    builder.add_node("skill_review",       skill_review_node)
    builder.add_node("search_jobs",        search_jobs_node)
    builder.add_node("role_selection",     role_selection_node)
    builder.add_node("gap_analysis",       gap_analysis_node)
    builder.add_node("gap_prioritization", gap_prioritization_node)
    builder.add_node("generate_plan",      generate_plan_node)
    builder.add_node("plan_approval",      plan_approval_node)
    builder.add_node("finalize",           finalize_node)

    builder.add_edge(START,                "parse_resume")
    builder.add_edge("parse_resume",       "skill_review")
    builder.add_edge("skill_review",       "search_jobs")
    builder.add_edge("search_jobs",        "role_selection")
    builder.add_edge("role_selection",     "gap_analysis")
    builder.add_edge("gap_analysis",       "gap_prioritization")
    builder.add_edge("gap_prioritization", "generate_plan")
    builder.add_edge("generate_plan",      "plan_approval")
    builder.add_edge("plan_approval",      "finalize")
    builder.add_edge("finalize",           END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


graph = build_graph()