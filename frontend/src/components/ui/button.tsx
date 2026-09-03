import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-md',
    'text-sm font-medium transition-[color,background-color,border-color,box-shadow]',
    'duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
    'focus-visible:ring-offset-1 focus-visible:ring-offset-background',
    'disabled:pointer-events-none disabled:opacity-50',
    'active:translate-y-px [&_svg]:pointer-events-none [&_svg]:shrink-0',
  ].join(' '),
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground shadow-panel hover:bg-primary/90',
        secondary:
          'border border-border bg-card text-foreground shadow-panel hover:bg-muted hover:text-foreground',
        outline:
          'border border-border bg-transparent text-foreground hover:border-border-strong hover:bg-muted',
        ghost: 'bg-transparent text-muted-foreground hover:bg-muted hover:text-foreground',
        destructive:
          'bg-danger text-danger-foreground shadow-panel hover:bg-danger/90',
        link: 'bg-transparent text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-8 px-3 py-1.5',
        sm: 'h-7 px-2.5 text-xs',
        lg: 'h-10 px-5 text-base',
        icon: 'h-8 w-8',
        'icon-sm': 'h-7 w-7',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  )
);
Button.displayName = 'Button';

export { Button, buttonVariants };
