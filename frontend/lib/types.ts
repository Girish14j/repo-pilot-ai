export interface ArchitectureAnalysis {
  score: number;
  patterns_detected: string[];
  violations: string[];
  strengths: string[];
  recommendations: string[];
  summary: string;
}

export interface DocumentationAnalysis {
  score: number;
  has_readme: boolean;
  missing_sections: string[];
  strengths: string[];
  improvements: string[];
  summary: string;
}

export interface SecurityAnalysis {
  score: number;
  vulnerabilities: string[];
  owasp_concerns: string[];
  good_practices: string[];
  critical_fixes: string[];
  summary: string;
}

export interface PerformanceAnalysis {
  score: number;
  potential_bottlenecks: string[];
  good_practices: string[];
  recommendations: string[];
  summary: string;
}

export interface RefactoringAnalysis {
  priority_refactors: string[];
  quick_wins: string[];
  long_term_improvements: string[];
  estimated_impact: string;
  summary: string;
}

export interface InterviewContent {
  technical_questions: string[];
  behavioral_questions: string[];
  system_design_questions: string[];
  suggested_answers_hints: string[];
  topics_to_study: string[];
}

export interface ResumeContent {
  resume_bullets: string[];
  ats_description: string;
  linkedin_post: string;
  key_achievements: string[];
  skills_demonstrated: string[];
}

export interface Scores {
  architecture: number;
  documentation: number;
  security: number;
  performance: number;
  overall: number;
}

export interface FullReport {
  repository: {
    full_name: string;
    description: string | null;
    stars: number;
    forks: number;
    language: string | null;
    topics: string[];
  };
  scores: Scores;
  analysis: {
    architecture: ArchitectureAnalysis | null;
    documentation: DocumentationAnalysis | null;
    security: SecurityAnalysis | null;
    performance: PerformanceAnalysis | null;
    refactoring: RefactoringAnalysis | null;
  };
  career: {
    interview: InterviewContent | null;
    resume: ResumeContent | null;
  };
  meta: {
    completed_agents: string[];
    errors: string[];
    total_agents_run: number;
  };
}