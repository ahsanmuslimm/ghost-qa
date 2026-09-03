import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

/**
 * Status labels for the console.
 *
 * Subtle tinted surface + matching hairline border + strong text colour, driven
 * entirely by semantic theme tokens so contrast holds in light AND dark mode.
 * `dot` renders the leading indicator used across CI/CD tooling.
 */
const badgeVariants = cva(
  'inline-flex items-center gap-1.5 whitespace-nowrap rounded-md border px-1.5 py-0.5 text-2xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'border-info-border bg-info-subtle text-info',
        secondary: 'border-neutral-border bg-neutral-subtle text-muted-foreground',
        success: 'border-success-border bg-success-subtle text-success',
        warning: 'border-warning-border bg-warning-subtle text-warning',
        destructive: 'border-danger-border bg-danger-subtle text-danger',
        info: 'border-info-border bg-info-subtle text-info',
        outline: 'border-border bg-transparent text-muted-foreground',
        solid: 'border-transparent bg-primary text-primary-foreground',
      },
      dot: {
        true: '',
        false: '',
      },
    },
    defaultVariants: { variant: 'default', dot: false },
  }
);

/** Dot colour per variant; neutral variants stay quiet. */
const DOT_CLASS: Record<string, string> = {
  default: 'bg-info',
  secondary: 'bg-muted-foreground/60',
  success: 'bg-success',
  warning: 'bg-warning',
  destructive: 'bg-danger',
  info: 'bg-info',
  outline: 'bg-muted-foreground/60',
  solid: 'bg-primary-foreground',
};

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  /** Render the leading status indicator. */
  dot?: boolean;
  /** Animate the dot for in-progress states (running, generating…). */
  pulse?: boolean;
}

export function Badge({ className, variant, dot, pulse, children, ...props }: BadgeProps) {
  const resolved = variant ?? 'default';
  return (
    <span className={cn(badgeVariants({ variant: resolved, dot }), className)} {...props}>
      {dot && (
        <span
          aria-hidden="true"
          className={cn(
            'h-1.5 w-1.5 shrink-0 rounded-full',
            DOT_CLASS[resolved] ?? 'bg-muted-foreground',
            pulse && 'animate-pulse-soft'
          )}
        />
      )}
      {children}
    </span>
  );
}

export { badgeVariants };
