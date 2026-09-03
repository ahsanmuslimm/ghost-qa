import type { ComponentType, ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '../../lib/utils';

export type StatTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info';

const TONE_TEXT: Record<StatTone, string> = {
  neutral: 'text-foreground',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
  info: 'text-info',
};

const TONE_ACCENT: Record<StatTone, string> = {
  neutral: 'bg-border-strong',
  success: 'bg-success',
  warning: 'bg-warning',
  danger: 'bg-danger',
  info: 'bg-info',
};

/**
 * KPI tile: uppercase label, one large tabular figure, an optional caption.
 * A 2px tone accent keeps status legible without colouring the whole tile.
 */
export function StatCard({
  label,
  value,
  caption,
  icon: Icon,
  tone = 'neutral',
  href,
  className,
}: {
  label: string;
  value: ReactNode;
  caption?: ReactNode;
  icon?: ComponentType<{ className?: string }>;
  tone?: StatTone;
  href?: string;
  className?: string;
}) {
  const body = (
    <>
      <span
        aria-hidden="true"
        className={cn('absolute inset-y-0 left-0 w-[2px]', TONE_ACCENT[tone])}
      />
      <div className="flex items-start justify-between gap-2">
        <p className="label-caps">{label}</p>
        {Icon && (
          <Icon className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
        )}
      </div>
      <p
        className={cn(
          'numeric mt-2 text-2xl font-semibold leading-none tracking-tight',
          TONE_TEXT[tone]
        )}
      >
        {value}
      </p>
      {caption && (
        <p className="mt-2 truncate text-2xs text-muted-foreground">{caption}</p>
      )}
    </>
  );

  const shellClass = cn(
    'relative block overflow-hidden rounded-md border border-border bg-card p-4 pl-[18px] shadow-panel',
    href && 'transition-colors hover:border-border-strong hover:bg-muted/40',
    className
  );

  return href ? (
    <Link to={href} className={shellClass}>
      {body}
    </Link>
  ) : (
    <div className={shellClass}>{body}</div>
  );
}
