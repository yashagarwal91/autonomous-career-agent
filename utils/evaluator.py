"""
Evaluator — Autonomous Career Intelligence Agent
Simple scoring of the generated learning plan quality.
"""

def evaluate_plan(learning_plan: dict, prioritized_gaps: list[str]) -> dict:
    """
    Score the learning plan across 3 simple checks.
    Returns score (0.0 - 1.0), grade, and feedback.
    """
    score = 0.0

    # are all prioritized gaps covered? (40%)
    skills_in_plan = [s.get("skill", "").lower() for s in learning_plan.get("skills", [])]
    covered = sum(
        1 for gap in prioritized_gaps
        if any(gap.lower() in s or s in gap.lower() for s in skills_in_plan)
    )
    if prioritized_gaps:
        score += (covered / len(prioritized_gaps)) * 0.4

    # does plan have all key sections? (40%)
    if learning_plan.get("skills"):         score += 0.2
    if learning_plan.get("final_project"):  score += 0.1
    if learning_plan.get("total_duration"): score += 0.1

    # do skills have resources? (20%)
    skills = learning_plan.get("skills", [])
    if skills:
        with_resources = sum(1 for s in skills if s.get("resources"))
        score += (with_resources / len(skills)) * 0.2

    score = round(score, 2)

    grade = (
        "A" if score >= 0.85 else
        "B" if score >= 0.70 else
        "C" if score >= 0.50 else
        "D"
    )

    feedback = (
        "Great plan — covers all gaps with clear resources."  if grade == "A" else
        "Good plan — minor improvements possible."            if grade == "B" else
        "Decent plan — consider adding more resources."       if grade == "C" else
        "Plan needs improvement — missing key sections."
    )

    return {
        "overall_score": score,
        "grade"        : grade,
        "feedback"     : feedback
    }


if __name__ == "__main__":
    sample_plan = {
        "target_role"   : "AI Engineer",
        "total_duration": "3 months",
        "skills": [
            {
                "skill"    : "LangGraph",
                "duration" : "3 weeks",
                "resources": [{"title": "LangGraph Docs", "url": "https://langchain-ai.github.io/langgraph/"}],
                "milestone": "Build a multi-node agent"
            }
        ],
        "final_project": "Deploy an autonomous agent"
    }

    result = evaluate_plan(sample_plan, ["LangGraph", "Docker"])
    print(f"Score    : {result['overall_score']} ({result['grade']})")
    print(f"Feedback : {result['feedback']}")