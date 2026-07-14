"""
Agent State — Autonomous Career Intelligence Agent
Defines the shared state passed between all LangGraph nodes
"""

from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class AgentState(TypedDict):

    # conversation history
    messages: Annotated[list, add_messages]

    # resume
    resume_text: Optional[str]
    extracted_skills: Optional[list[str]]

    # HITL #1 — user confirms/edits skills
    skills_confirmed: Optional[bool]
    confirmed_skills: Optional[list[str]]

    # job search
    search_query: Optional[str]
    job_results: Optional[list[dict]]
    available_roles: Optional[list[str]]

    # HITL #2 — user picks target role
    target_role: Optional[str]

    # gap analysis
    required_skills: Optional[list[str]]
    skill_gaps: Optional[list[str]]

    # HITL #3 — user picks top 3 gaps
    prioritized_gaps: Optional[list[str]]

    # learning plan
    learning_plan: Optional[dict]

    # HITL #4 — user approves plan
    plan_approved: Optional[bool]

    # eval
    eval_score: Optional[float]
    eval_feedback: Optional[str]

    # internals
    current_node: Optional[str]
    reasoning_trace: Optional[list[str]]    # shown in UI trace panel
    error: Optional[str]
    session_id: Optional[str]