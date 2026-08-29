// Badge variant mappings for backend enum values.

export type BadgeVariant = 'default' | 'secondary' | 'success' | 'warning' | 'destructive' | 'outline';

const RISK_VARIANTS: Record<string, BadgeVariant> = {
  low: 'success',
  medium: 'warning',
  high: 'destructive',
  critical: 'destructive',
};

const STATUS_VARIANTS: Record<string, BadgeVariant> = {
  queued: 'secondary',
  extracting: 'secondary',
  generating: 'secondary',
  awaiting_approval: 'warning',
  running: 'default',
  completed: 'success',
  failed: 'destructive',
};

const OUTCOME_VARIANTS: Record<string, BadgeVariant> = {
  passed: 'success',
  failed: 'destructive',
  skipped: 'warning',
  timed_out: 'destructive',
};

const PRIORITY_VARIANTS: Record<string, BadgeVariant> = {
  p0_critical: 'destructive',
  p1_high: 'warning',
  p2_medium: 'default',
  p3_low: 'secondary',
};

const HEAL_VARIANTS: Record<string, BadgeVariant> = {
  proposed: 'warning',
  accepted: 'default',
  rejected: 'destructive',
  verified: 'success',
};

export function riskVariant(level: string | null | undefined): BadgeVariant {
  return (level && RISK_VARIANTS[level]) || 'secondary';
}

export function statusVariant(status: string | null | undefined): BadgeVariant {
  return (status && STATUS_VARIANTS[status]) || 'secondary';
}

export function outcomeVariant(outcome: string | null | undefined): BadgeVariant {
  return (outcome && OUTCOME_VARIANTS[outcome]) || 'secondary';
}

export function priorityVariant(priority: string | null | undefined): BadgeVariant {
  return (priority && PRIORITY_VARIANTS[priority]) || 'secondary';
}

export function healVariant(status: string | null | undefined): BadgeVariant {
  return (status && HEAL_VARIANTS[status]) || 'secondary';
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString();
}

export function formatDuration(start: string | null | undefined, end: string | null | undefined): string {
  if (!start || !end) return '—';
  const ms = new Date(end).getTime() - new Date(start).getTime();
  if (Number.isNaN(ms) || ms < 0) return '—';
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`;
  return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`;
}
