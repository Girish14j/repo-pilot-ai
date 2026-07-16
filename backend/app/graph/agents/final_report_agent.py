from app.graph.state import RepoState

def final_report_agent(state: RepoState) -> dict:
    """
    Node 9: Final Report Agent

    Responsibility: Assemble all agent outputs into one clean report.
    This agent does NOT call an LLM — it just organizes existing state.

    This is an important pattern: not every node needs an LLM.
    Sometimes a node is just pure Python logic.

    Inputs from state:  everything
    Outputs to state:   final_report
    """
    print("Final Report Agent: Assembling Final report...")

    repo_data = state.get("repo_data") or {}
    architecture = state.get("architecture_analysis") or {}
    documentation = state.get("documentation_analysis") or {}
    security = state.get("security_analysis") or {}
    performance = state.get("performance_analysis") or {}

    #calculates overall score from all agent scores
    scores = {
        "architecture": architecture.get("score", 0),
        "documentation": documentation.get("score", 0),
        "security": security.get("score", 0),
        "performance": performance.get("score", 0),
    }

    # Only average scores that were actually computed
    valid_scores = [s for s in scores.values() if s > 0]
    overall_score = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0

    final_report = {
        "repository": {
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "stars": repo_data.get("stars"),
            "forks": repo_data.get("forks"),
            "language": repo_data.get("language"),
            "topics": repo_data.get("topics", []),
        },
        "scores": {
            **scores,
            "overall": overall_score,
        },
        "analysis": {
            "architecture": architecture,
            "documentation": documentation,
            "security": security,
            "performance": performance,
            "refactoring": state.get("refactoring_suggestions"),
        },
        "career": {
            "interview": state.get("interview_content"),
            "resume": state.get("resume_content"),
        },
        "meta": {
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []),
            "total_agents_run": len(state.get("completed_agents", [])),
        }
    }

    print(f" Final Report Agent: Report assembled. Overall score: {overall_score}/10")
    print(f" Agents completed: {', '.join(state.get('completed_agents', []))}")

    return {
        "final_report": final_report,
        "completed_agents": state.get("completed_agents", []) + ["final_report_agent"],
        "errors": state.get("errors", []),
    }
