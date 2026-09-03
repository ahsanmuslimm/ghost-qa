import * as React from 'react';
import { cn } from '../../lib/utils';

interface MenuContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const MenuContext = React.createContext<MenuContextValue | null>(null);

function useMenu() {
  const ctx = React.useContext(MenuContext);
  if (!ctx) throw new Error('Menu components must be used within <Menu>');
  return ctx;
}

/**
 * Minimal accessible dropdown: closes on outside click, Escape and item
 * activation. No portal — the console never nests menus inside clipped panels.
 */
export function Menu({
  align = 'end',
  className,
  children,
}: {
  align?: 'start' | 'end';
  className?: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  const childrenArray = React.Children.toArray(children);
  const isTrigger = (child: React.ReactNode) =>
    React.isValidElement(child) && child.type === MenuTrigger;
  const trigger = childrenArray.find(isTrigger);
  const content = childrenArray.filter((child) => !isTrigger(child));

  return (
    <MenuContext.Provider value={{ open, setOpen }}>
      <div ref={ref} className={cn('relative', className)}>
        {trigger}
        {open && (
          <div
            role="menu"
            className={cn(
              'absolute top-[calc(100%+6px)] z-50 min-w-[190px] animate-fade-in rounded-md border border-border bg-popover p-1 shadow-raised',
              align === 'end' ? 'right-0' : 'left-0'
            )}
          >
            {content}
          </div>
        )}
      </div>
    </MenuContext.Provider>
  );
}

export function MenuTrigger({
  className,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { open, setOpen } = useMenu();
  return (
    <button
      type="button"
      aria-haspopup="menu"
      aria-expanded={open}
      onClick={() => setOpen(!open)}
      className={className}
      {...props}
    >
      {children}
    </button>
  );
}

export function MenuLabel({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <p className={cn('label-caps px-2 py-1.5', className)}>{children}</p>
  );
}

export function MenuItem({
  icon: Icon,
  onSelect,
  tone = 'default',
  className,
  children,
}: {
  icon?: React.ComponentType<{ className?: string }>;
  onSelect?: () => void;
  tone?: 'default' | 'danger';
  className?: string;
  children: React.ReactNode;
}) {
  const { setOpen } = useMenu();
  return (
    <button
      type="button"
      role="menuitem"
      onClick={() => {
        setOpen(false);
        onSelect?.();
      }}
      className={cn(
        'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-xs font-medium transition-colors',
        tone === 'danger'
          ? 'text-danger hover:bg-danger-subtle'
          : 'text-foreground hover:bg-muted',
        className
      )}
    >
      {Icon && <Icon className="h-3.5 w-3.5 shrink-0 opacity-70" aria-hidden="true" />}
      {children}
    </button>
  );
}

export function MenuSeparator({ className }: { className?: string }) {
  return <div role="separator" className={cn('my-1 h-px bg-border', className)} />;
}
