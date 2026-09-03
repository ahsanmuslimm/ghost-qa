import { cn } from '../../lib/utils';

/**
 * Product mark: the same geometric ghost used in favicon.svg, drawn inline so
 * it inherits the current text colour and stays crisp at any size.
 */
export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground',
        className
      )}
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none">
        <path
          d="M6 16.5V10.5a6 6 0 1 1 12 0v6l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4Z"
          fill="currentColor"
        />
        <circle cx="9.9" cy="10.2" r="1.05" className="fill-primary" />
        <circle cx="14.1" cy="10.2" r="1.05" className="fill-primary" />
      </svg>
    </span>
  );
}

/** Mark + wordmark, used in the sidebar and on the auth screen. */
export function Brand({
  subtitle,
  className,
  markClassName,
}: {
  subtitle?: string;
  className?: string;
  markClassName?: string;
}) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <BrandMark className={markClassName} />
      <div className="min-w-0 leading-tight">
        <p className="truncate text-sm font-semibold tracking-tight text-foreground">Ghost QA</p>
        {subtitle && (
          <p className="truncate text-2xs text-muted-foreground">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
