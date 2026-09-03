import * as React from 'react';
import { cn } from '../../lib/utils';

interface TabsContextValue {
  value: string;
  onValueChange: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | null>(null);

function useTabs() {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error('Tabs components must be used within <Tabs>');
  return ctx;
}

export function Tabs({
  value,
  onValueChange,
  className,
  children,
}: {
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

/** Underline tab list — the standard control for section navigation in consoles. */
export function TabsList({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div
      role="tablist"
      className={cn('flex items-center gap-1 border-b border-border', className)}
    >
      {children}
    </div>
  );
}

export function TabsTrigger({
  value,
  className,
  children,
}: {
  value: string;
  className?: string;
  children: React.ReactNode;
}) {
  const { value: active, onValueChange } = useTabs();
  const isActive = active === value;
  return (
    <button
      role="tab"
      type="button"
      aria-selected={isActive}
      onClick={() => onValueChange(value)}
      className={cn(
        '-mb-px inline-flex items-center gap-1.5 whitespace-nowrap border-b-2 px-3 py-2 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
        isActive
          ? 'border-primary text-foreground'
          : 'border-transparent text-muted-foreground hover:border-border-strong hover:text-foreground',
        className
      )}
    >
      {children}
    </button>
  );
}

export function TabsContent({
  value,
  className,
  children,
}: {
  value: string;
  className?: string;
  children: React.ReactNode;
}) {
  const { value: active } = useTabs();
  if (active !== value) return null;
  return (
    <div role="tabpanel" className={cn('mt-4 animate-fade-in', className)}>
      {children}
    </div>
  );
}
