from pydantic import BaseModel

class DeveloperAssistant(BaseModel):
    """
    Career-focused content generated from a repository.
    Every field maps to a section in the Developer Assistant UI.
    """
    resume_bullets: list[str]       # 4-6 ATS-friendly resume bullet points
    ats_description: str            # one paragraph ATS-friendly project description
    interview_questions: list[str]  # 5 likely technical interview questions
    readme_improvements: list[str]  # specific suggestions to improve the README
    feature_suggestions: list[str]  # 3-5 features that would improve the project
    linkedin_post: str              # ready-to-post LinkedIn draft