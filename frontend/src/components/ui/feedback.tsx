import * as React from 'react';
import { cn } from '../../lib/utils';
import { AlertCircle, Info } from 'lucide-react';

export function Alert({
  variant = 'default',
  title,
  children,
  className,
}: {
  variant?: 'default' | 'destructive';
  title?: string;
  children?: React.ReactNode;
  className?: string;
}) {
  const destructive = variant === 'destructive';
  const Icon = destructive ? AlertCircle : Info;
  return (
    <div
      role="alert"
      className={cn(
        'relative w-full rounded-lg border p-4',
        destructive
          ? 'border-red-600/40 bg-red-600/10 text-red-400'
          : 'border-border bg-card text-foreground',
        className
      )}
    >
      <div className="flex gap-3">
        <Icon className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
        <div className="space-y-1">
          {title && <h5 className="font-medium leading-none tracking-tight">{title}</h5>}
          {children && <div className="text-sm opacity-90">{children}</div>}
        </div>
      </div>
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-pulse rounded-md bg-muted', className)} aria-hidden="true" />;
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cn(
        'inline-block h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-primary',
        className
      )}
    />
  );
}
