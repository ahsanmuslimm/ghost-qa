import * as React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface Crumb {
  label: string;
  to?: string;
}

/**
 * Standard page header used by every route: optional breadcrumb, a compact
 * title, supporting description, a meta strip and right-aligned actions.
 * Keeps vertical rhythm identical across the console.
 */
export function PageHeader({
  title,
  description,
  breadcrumbs,
  meta,
  actions,
  className,
}: {
  title: string;
  description?: React.ReactNode;
  breadcrumbs?: Crumb[];
  meta?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <header className={cn('space-y-3', className)}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav aria-label="Breadcrumb">
          <ol className="flex flex-wrap items-center gap-1 text-2xs text-muted-foreground">
            {breadcrumbs.map((crumb, index) => {
              const last = index === breadcrumbs.length - 1;
              return (
                <li key={`${crumb.label}-${index}`} className="flex items-center gap-1">
                  {crumb.to && !last ? (
                    <Link
                      to={crumb.to}
                      className="transition-colors hover:text-foreground hover:underline"
                    >
                      {crumb.label}
                    </Link>
                  ) : (
                    <span className={cn(last && 'text-foreground')}>{crumb.label}</span>
                  )}
                  {!last && <ChevronRight className="h-3 w-3 opacity-50" aria-hidden="true" />}
                </li>
              );
            })}
          </ol>
        </nav>
      )}

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <h1 className="text-xl font-semibold leading-tight tracking-tight text-foreground">
            {title}
          </h1>
          {description && (
            <p className="max-w-2xl text-xs leading-relaxed text-muted-foreground">{description}</p>
          )}
          {meta && <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 pt-1">{meta}</div>}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
      </div>
    </header>
  );
}

/** Small label/value pair used in a PageHeader meta strip or card footer. */
export function MetaItem({
  label,
  value,
  className,
}: {
  label: string;
  value: React.ReactNode;
  className?: string;
}) {
  return (
    <span className={cn('flex items-center gap-1.5 text-2xs', className)}>
      <span className="text-muted-foreground">{label}</span>
      <span className="numeric font-medium text-foreground">{value}</span>
    </span>
  );
}
