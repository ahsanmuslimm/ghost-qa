import * as React from 'react';
import { cn } from '../../lib/utils';
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react';

export type AlertVariant = 'default' | 'info' | 'success' | 'warning' | 'destructive';

const ALERT_STYLES: Record<AlertVariant, string> = {
  default: 'border-border bg-card text-foreground',
  info: 'border-info-border bg-info-subtle text-info',
  success: 'border-success-border bg-success-subtle text-success',
  warning: 'border-warning-border bg-warning-subtle text-warning',
  destructive: 'border-danger-border bg-danger-subtle text-danger',
};

const ALERT_ICONS: Record<AlertVariant, React.ComponentType<{ className?: string }>> = {
  default: Info,
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  destructive: AlertCircle,
};

export function Alert({
  variant = 'default',
  title,
  children,
  className,
}: {
  variant?: AlertVariant;
  title?: string;
  children?: React.ReactNode;
  className?: string;
}) {
  const Icon = ALERT_ICONS[variant];
  const neutral = variant === 'default';
  return (
    <div
      role={variant === 'destructive' || variant === 'warning' ? 'alert' : 'status'}
      className={cn(
        'relative w-full rounded-md border px-3 py-2.5 shadow-panel',
        ALERT_STYLES[variant],
        className
      )}
    >
      <div className="flex gap-2.5">
        <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <div className="min-w-0 space-y-1">
          {title && (
            <h5 className={cn('text-xs font-semibold leading-none', neutral && 'text-foreground')}>
              {title}
            </h5>
          )}
          {children && (
            <div className={cn('text-xs leading-relaxed', neutral ? 'text-muted-foreground' : 'opacity-90')}>
              {children}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/** Neutral placeholder shown when a collection has no rows yet. */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-2 px-6 py-14 text-center',
        className
      )}
    >
      {Icon && (
        <span className="mb-1 flex h-9 w-9 items-center justify-center rounded-md border border-border bg-surface">
          <Icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
        </span>
      )}
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description && (
        <p className="max-w-sm text-xs leading-relaxed text-muted-foreground">{description}</p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-muted', className)}
      aria-hidden="true"
    />
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cn(
        'inline-block h-4 w-4 animate-spin rounded-full border-2 border-border-strong border-t-primary',
        className
      )}
    />
  );
}

/** Thin determinate bar used for pipeline progress. */
export function Progress({
  value,
  className,
  indicatorClassName,
}: {
  value: number;
  className?: string;
  indicatorClassName?: string;
}) {
  const pct = Math.min(100, Math.max(0, value));
  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(pct)}
      aria-valuemin={0}
      aria-valuemax={100}
      className={cn('h-1.5 w-full overflow-hidden rounded-full bg-muted', className)}
    >
      <div
        className={cn('h-full rounded-full bg-primary transition-all duration-500', indicatorClassName)}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
