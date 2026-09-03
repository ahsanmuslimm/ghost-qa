// Presentation mappings for backend enum values: badge tone, human labels and
// date/number formatting. Every colour here resolves through the semantic
// design tokens so contrast is correct in both light and dark themes.

export type BadgeVariant =
  | 'default'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'destructive'
  | 'info'
  | 'outline';

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
  approved: 'info',
  rejected: 'destructive',
  running: 'info',
  completed: 'success',
  failed: 'destructive',
  skipped: 'secondary',
  cancelled: 'secondary',
};

const OUTCOME_VARIANTS: Record<string, BadgeVariant> = {
  passed: 'success',
  failed: 'destructive',
  error: 'destructive',
  skipped: 'secondary',
  timed_out: 'warning',
  pending: 'secondary',
};

const PRIORITY_VARIANTS: Record<string, BadgeVariant> = {
  p0_critical: 'destructive',
  p1_high: 'warning',
  p2_medium: 'info',
  p3_low: 'secondary',
};

const HEAL_VARIANTS: Record<string, BadgeVariant> = {
  proposed: 'warning',
  pending: 'warning',
  accepted: 'info',
  applied: 'info',
  rejected: 'destructive',
  verified: 'success',
};

/** Statuses that are still moving — render their badge with a pulsing dot. */
const ACTIVE_STATUSES = new Set(['queued', 'extracting', 'generating', 'running']);

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

export function isActiveStatus(status: string | null | undefined): boolean {
  return !!status && ACTIVE_STATUSES.has(status);
}

/** `awaiting_approval` → `Awaiting approval`; unknown values pass through. */
export function humanize(value: string | null | undefined, fallback = '—'): string {
  if (!value) return fallback;
  const spaced = value.replace(/[_-]+/g, ' ').trim();
  if (!spaced) return fallback;
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

/** `p0_critical` → `P0 · Critical` for priority columns. */
export function humanizePriority(priority: string | null | undefined): string {
  if (!priority) return '—';
  const match = /^(p\d)[_-](.+)$/i.exec(priority);
  if (!match) return humanize(priority);
  return `${match[1].toUpperCase()} · ${humanize(match[2])}`;
}

const dateFmt = new Intl.DateTimeFormat(undefined, {
  year: 'numeric',
  month: 'short',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

const timeFmt = new Intl.DateTimeFormat(undefined, {
  month: 'short',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

function toDate(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDateTime(iso: string | null | undefined): string {
  const date = toDate(iso);
  return date ? dateFmt.format(date) : '—';
}

/** Compact timestamp for dense table rows (omits the year). */
export function formatShortDateTime(iso: string | null | undefined): string {
  const date = toDate(iso);
  return date ? timeFmt.format(date) : '—';
}

/** `3m ago` / `2h ago` / `Yesterday` / `Mar 4` — the console-standard form. */
export function formatRelative(iso: string | null | undefined): string {
  const date = toDate(iso);
  if (!date) return '—';
  const diff = Date.now() - date.getTime();
  if (diff < 0) return 'just now';
  const sec = Math.floor(diff / 1000);
  if (sec < 45) return 'just now';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  if (day === 1) return 'yesterday';
  if (day < 7) return `${day}d ago`;
  return timeFmt.format(date);
}

export function formatDuration(
  start: string | null | undefined,
  end: string | null | undefined
): string {
  const from = toDate(start);
  const to = toDate(end);
  if (!from || !to) return '—';
  const ms = to.getTime() - from.getTime();
  if (Number.isNaN(ms) || ms < 0) return '—';
  const sec = Math.round(ms / 1000);
  if (sec < 60) return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`;
  return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`;
}

/** Groups thousands: `12345` → `12,345`. */
export function formatNumber(value: number | null | undefined, fallback = '—'): string {
  if (value === null || value === undefined || Number.isNaN(value)) return fallback;
  return new Intl.NumberFormat(undefined).format(value);
}

/** `0.842` → `84.2%`. */
export function formatPercent(ratio: number | null | undefined, fallback = '—'): string {
  if (ratio === null || ratio === undefined || Number.isNaN(ratio)) return fallback;
  return `${(ratio * 100).toFixed(ratio * 100 < 10 ? 1 : 0)}%`;
}
