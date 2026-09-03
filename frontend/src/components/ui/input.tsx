import * as React from 'react';
import { cn } from '../../lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        'flex h-8 w-full rounded-md border border-input bg-card px-2.5 py-1 text-sm',
        'text-foreground shadow-panel transition-colors placeholder:text-muted-foreground/70',
        'file:border-0 file:bg-transparent file:text-sm file:font-medium',
        'focus-visible:border-ring focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/25',
        'disabled:cursor-not-allowed disabled:opacity-60',
        'aria-[invalid=true]:border-danger aria-[invalid=true]:ring-danger/20',
        className
      )}
      {...props}
    />
  )
);
Input.displayName = 'Input';

const Label = React.forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn(
        'text-xs font-medium text-foreground peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
        className
      )}
      {...props}
    />
  )
);
Label.displayName = 'Label';

/** Native select styled to match Input — used for table filters. */
export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        'h-8 w-full appearance-none rounded-md border border-input bg-card py-1 pl-2.5 pr-7 text-xs',
        'font-medium text-foreground shadow-panel transition-colors',
        'focus-visible:border-ring focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/25',
        'disabled:cursor-not-allowed disabled:opacity-60',
        className
      )}
      style={{
        backgroundImage:
          "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E\")",
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'right 8px center',
      }}
      {...props}
    >
      {children}
    </select>
  )
);
Select.displayName = 'Select';

/** Inline validation message — semantic, not a hardcoded shade. */
function FieldError({
  children,
  className,
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <p id={id} role="alert" className={cn('text-xs text-danger', className)}>
      {children}
    </p>
  );
}

export { Input, Label, FieldError, Select };
