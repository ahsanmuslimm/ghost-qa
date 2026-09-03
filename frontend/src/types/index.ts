// Types mirroring the FastAPI backend responses (snake_case, as returned).

export type PipelineStatus =
  | 'queued'
  | 'extracting'
  | 'generating'
  | 'awaiting_approval'
  | 'running'
  | 'completed'
  | 'failed';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface PipelineRunSummary {
  id: string;
  repository: string;
  pr_number: number | null;
  commit_sha: string | null;
  status: PipelineStatus;
  risk_level: RiskLevel | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface PipelineRun extends PipelineRunSummary {
  started_at: string | null;
}

export interface RunsPage {
  runs: PipelineRunSummary[];
  pagination: {
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  };
}

export interface TestCase {
  id: string;
  title: string;
  test_type: string | null;
  priority: string | null;
  expected_result: string | null;
  risk_level: RiskLevel | null;
  risk_rationale: string | null;
  approval_status: string | null;
  status: string | null;
  approved_by: string | null;
  outcome: string | null;
  failure_step: number | null;
  failure_message: string | null;
  failure_type: string | null;
  duration_ms: number | null;
  executed_at: string | null;
}

export interface TestResult {
  id: string;
  test_case_id: string;
  outcome: 'passed' | 'failed' | 'skipped' | 'timed_out';
  failure_step: number | null;
  failure_message: string | null;
  failure_type: string | null;
  duration_ms: number | null;
  robot_id: string | null;
  executed_at: string | null;
}

export interface HealAttempt {
  id: string;
  status: 'proposed' | 'accepted' | 'rejected' | 'verified';
  [key: string]: unknown;
}

export interface RiskReport {
  pipeline_run_id?: string;
  risk_level?: RiskLevel;
  total_tests?: number;
  passed?: number;
  failed?: number;
  [key: string]: unknown;
}

export interface DashboardOverview {
  total_repositories: number;
  total_pipeline_runs: number;
  recent_runs: {
    id: string;
    repository: string;
    pr_number: number | null;
    status: PipelineStatus;
    risk_level: RiskLevel | null;
    created_at: string | null;
  }[];
  status_breakdown: Record<string, number>;
  risk_breakdown: Record<string, number>;
}

export interface UserPayload {
  id: string;
  email: string;
  full_name?: string | null;
  is_active?: boolean;
  is_admin?: boolean;
  roles?: string[];
  permissions?: string[];
}

export interface LoginResponse {
  token: string;
  expires_in: number;
}

export interface ActionResult {
  success: boolean;
  message?: string;
  error?: string;
  [key: string]: unknown;
}

// Response of GET / — reports which run mode the backend is serving.
export interface SystemHealth {
  status: string;
  demo_mode: boolean;
  execution_backend?: 'demo' | 'uipath' | 'mock' | string;
  execution?: string;
  app_env?: string;
}

// JWT payload issued by the backend (app/services/auth.py).
export interface JwtPayload {
  sub: string;
  role: string;
  exp: number;
  iat: number;
}
