"""
Streamlit UI — Autonomous Career Intelligence Agent
"""

import streamlit as st
import requests

API = "http://localhost:8000"

st.set_page_config(page_title="Career Intelligence Agent", page_icon="🤖", layout="centered")
st.title("🤖 Autonomous Career Intelligence Agent")
st.caption("Upload your resume → Agent analyzes job market → Builds your learning plan")
st.divider()


for key in ["session_id", "status", "interrupt", "final_result"]:
    if key not in st.session_state:
        st.session_state[key] = None


def resume_agent(human_response: dict):
    res  = requests.post(
        f"{API}/resume/{st.session_state.session_id}",
        json={"human_response": human_response}
    )
    data = res.json()
    st.session_state.status    = data.get("status")
    st.session_state.interrupt = data.get("interrupt", {})
    if data.get("status") == "completed":
        st.session_state.final_result = data
    st.rerun()


def show_trace():
    res   = requests.get(f"{API}/status/{st.session_state.session_id}")
    trace = res.json().get("reasoning_trace", [])
    if trace:
        with st.expander("🔍 Agent Reasoning Trace", expanded=False):
            for step in trace:
                st.text(step)


# upload screen
if not st.session_state.session_id:
    uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

    if uploaded and st.button("🚀 Start Analysis", use_container_width=True):
        with st.spinner("Parsing resume and starting agent..."):
            res  = requests.post(
                f"{API}/start",
                files={"file": (uploaded.name, uploaded.read(), "application/pdf")}
            )
            data = res.json()

        st.session_state.session_id = data["session_id"]
        st.session_state.status     = data["status"]
        st.session_state.interrupt  = data.get("interrupt", {})
        st.rerun()


# HITL screens
elif st.session_state.status == "waiting_for_human":
    interrupt = st.session_state.interrupt
    itype     = interrupt.get("type")
    show_trace()
    st.divider()

    if itype == "skill_review":
        st.subheader("✅ Step 1 — Confirm Your Skills")
        st.caption("Remove any incorrect skills or add missing ones.")

        skills   = interrupt.get("extracted_skills", [])
        selected = st.multiselect("Your Skills", options=skills, default=skills)
        extra    = st.text_input("Add a missing skill (optional)")

        if st.button("Confirm Skills →", use_container_width=True):
            final = selected + ([extra.strip()] if extra.strip() else [])
            resume_agent({"confirmed_skills": final})

    elif itype == "role_selection":
        st.subheader("🎯 Step 2 — Choose Your Target Role")
        st.caption("Based on current job market data.")

        roles = interrupt.get("available_roles", [])
        role  = st.radio("Select a role", options=roles)

        if st.button("Select Role →", use_container_width=True):
            resume_agent({"target_role": role})

    elif itype == "gap_prioritization":
        st.subheader("📊 Step 3 — Prioritize Skill Gaps")
        gaps = interrupt.get("skill_gaps", [])
        st.caption(f"Found {len(gaps)} gaps. Pick up to 3 to focus on first.")

        selected_gaps = st.multiselect("Select skills to learn", options=gaps, max_selections=3)

        if st.button("Set Priorities →", use_container_width=True, disabled=len(selected_gaps) == 0):
            resume_agent({"prioritized_gaps": selected_gaps})

    elif itype == "plan_approval":
        st.subheader("📋 Step 4 — Review Your Learning Plan")
        plan = interrupt.get("learning_plan", {})

        st.write(f"**Target Role:** {plan.get('target_role')}")
        st.write(f"**Duration:** {plan.get('total_duration')}")

        for skill in plan.get("skills", []):
            with st.expander(f"📘 {skill.get('skill')} — {skill.get('duration')}"):
                st.write(f"**Milestone:** {skill.get('milestone')}")
                for r in skill.get("resources", []):
                    st.markdown(f"- [{r.get('title')}]({r.get('url')})")

        st.write(f"**Final Project:** {plan.get('final_project')}")
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve Plan", use_container_width=True):
                resume_agent({"approved": True})
        with col2:
            if st.button("🔄 Regenerate", use_container_width=True):
                resume_agent({"approved": False})


# final result screen
elif st.session_state.status == "completed":
    result = st.session_state.final_result
    plan   = result.get("learning_plan", {})
    score  = result.get("eval_score", 0)

    st.success("✅ Your learning plan is ready!")
    show_trace()
    st.divider()

    col1, col2 = st.columns(2)
    col1.metric("Plan Quality Score", f"{int(score * 100)}%")
    col2.metric("Target Role", plan.get("target_role", "N/A"))

    st.subheader("📋 Your Learning Plan")
    st.write(f"**Total Duration:** {plan.get('total_duration')}")

    for skill in plan.get("skills", []):
        with st.expander(f"📘 {skill.get('skill')} — {skill.get('duration')}"):
            st.write(f"**Milestone:** {skill.get('milestone')}")
            for r in skill.get("resources", []):
                st.markdown(f"- [{r.get('title')}]({r.get('url')})")

    st.info(f"🚀 **Final Project:** {plan.get('final_project')}")

    if st.button("🔁 Start Over", use_container_width=True):
        for key in ["session_id", "status", "interrupt", "final_result"]:
            st.session_state[key] = None
        st.rerun()