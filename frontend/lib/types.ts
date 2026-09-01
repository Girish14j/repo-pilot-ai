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
    code_quality: CodeQualityAnalysis | null;      // ← NEW
    optimization: OptimizationAnalysis | null;     // ← NEW
  };
  career: {
    interview: InterviewContent | null;
    resume: ResumeContent | null;
  };
  meta: {
    completed_agents: string[];
    errors: string[];
    total_agents_run: number;
    files_analyzed: number;          // ← NEW
    critical_issues_found: number;   // ← NEW
  };
}

export interface CodeIssue {
  file: string;
  issue: string;
  severity: "critical" | "warning" | "suggestion";
  line_hint: string | null;
  fix: string;
}

export interface CodeQualityAnalysis {
  score: number;
  issues: CodeIssue[];
  good_patterns: string[];
  overall_assessment: string;
  top_3_fixes: string[];
}

export interface OptimizationSuggestion {
  file: string;
  current_pattern: string;
  optimized_pattern: string;
  impact: string;
  effort: string;
  explanation: string;
}

export interface OptimizationAnalysis {
  suggestions: OptimizationSuggestion[];
  quick_wins: string[];
  performance_score: number;
  readability_score: number;
  summary: string;
} 