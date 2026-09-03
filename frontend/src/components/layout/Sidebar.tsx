import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  FlaskConical,
  LayoutDashboard,
  PanelLeftClose,
  PanelLeftOpen,
  Shield,
} from 'lucide-react';
import { systemApi } from '../../lib/api';
import { cn } from '../../lib/utils';
import { useAuthStore } from '../../stores/authStore';
import { Badge } from '../ui/badge';
import { Brand, BrandMark } from '../common/Brand';

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

function useNavSections(): NavSection[] {
  const { user, hasPermission } = useAuthStore();
  const canAdmin = !!user && (user.role === 'admin' || hasPermission('user:view'));

  const sections: NavSection[] = [
    {
      title: 'Monitor',
      items: [
        { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
        { to: '/runs', label: 'Pipeline Runs', icon: Activity },
      ],
    },
    {
      title: 'Quality',
      items: [{ to: '/tests', label: 'Test Cases', icon: FlaskConical }],
    },
  ];

  if (canAdmin) {
    sections.push({
      title: 'Administration',
      items: [{ to: '/admin', label: 'Users & Roles', icon: Shield }],
    });
  }

  return sections;
}

/** Which run mode the backend is serving — Demo, Live or Live (built-in). */
function useRunMode() {
  const { data } = useQuery({
    queryKey: ['system-health'],
    queryFn: async () => (await systemApi.health()).data,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  if (!data) return { label: 'Connecting', tone: 'secondary' as const, pulse: true };
  if (data.demo_mode) return { label: 'Demo mode', tone: 'secondary' as const, pulse: false };
  if (data.execution_backend === 'uipath') {
    return { label: 'Live · UiPath', tone: 'success' as const, pulse: false };
  }
  return { label: 'Live · built-in', tone: 'success' as const, pulse: false };
}

export function Sidebar({
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile,
}: {
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}) {
  const sections = useNavSections();
  const mode = useRunMode();

  // Escape closes the mobile drawer.
  useEffect(() => {
    if (!mobileOpen) return;
    const onKeyDown = (event: KeyboardEvent) => event.key === 'Escape' && onCloseMobile();
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [mobileOpen, onCloseMobile]);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      'group relative flex items-center gap-2.5 rounded-md py-1.5 text-xs font-medium transition-colors',
      collapsed ? 'justify-center px-2' : 'px-2.5',
      isActive
        ? 'bg-muted text-foreground'
        : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
    );

  return (
    <aside
      aria-label="Main navigation"
      className={cn(
        'z-40 flex shrink-0 flex-col border-r border-border bg-card',
        collapsed ? 'md:w-[60px]' : 'md:w-[236px]',
        'w-[236px]',
        mobileOpen ? 'fixed inset-y-0 left-0 flex' : 'hidden',
        'md:sticky md:top-0 md:h-screen md:flex'
      )}
    >
      {/* Brand / collapse */}
      <div
        className={cn(
          'flex h-14 shrink-0 items-center border-b border-border',
          collapsed ? 'md:justify-center px-2' : 'justify-between px-3.5'
        )}
      >
        {collapsed ? (
          <span className="hidden md:block">
            <BrandMark />
          </span>
        ) : (
          <Brand subtitle="Autonomous test pipeline" />
        )}
        {!collapsed && (
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label="Collapse navigation"
            className="hidden rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:block"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        )}
      </div>

      {collapsed && (
        <button
          type="button"
          onClick={onToggleCollapse}
          aria-label="Expand navigation"
          className="hidden h-9 shrink-0 items-center justify-center border-b border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:flex"
        >
          <PanelLeftOpen className="h-4 w-4" />
        </button>
      )}

      {/* Sections */}
      <nav className="flex-1 space-y-5 overflow-y-auto px-2.5 py-4">
        {sections.map((section) => (
          <div key={section.title} className="space-y-1">
            {!collapsed && <p className="label-caps px-2.5 pb-1">{section.title}</p>}
            {collapsed && <div className="mx-2.5 h-px bg-border" aria-hidden="true" />}
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                title={collapsed ? item.label : undefined}
                onClick={onCloseMobile}
                className={navLinkClass}
              >
                {({ isActive }) => (
                  <>
                    <span
                      aria-hidden="true"
                      className={cn(
                        'absolute left-0 top-1/2 h-4 w-[2px] -translate-y-1/2 rounded-full bg-primary transition-opacity',
                        isActive ? 'opacity-100' : 'opacity-0'
                      )}
                    />
                    <item.icon
                      className={cn(
                        'h-4 w-4 shrink-0',
                        isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'
                      )}
                      aria-hidden="true"
                    />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer: run mode + build identity */}
      <div className={cn('shrink-0 border-t border-border', collapsed ? 'p-2' : 'p-3')}>
        {collapsed ? (
          <span
            className={cn(
              'mx-auto block h-1.5 w-1.5 rounded-full',
              mode.tone === 'success' ? 'bg-success' : 'bg-muted-foreground'
            )}
            title={mode.label}
          />
        ) : (
          <div className="flex items-center justify-between gap-2 rounded-md border border-border bg-surface px-2.5 py-2">
            <div className="min-w-0">
              <p className="label-caps">Run mode</p>
              <p className="truncate text-2xs text-muted-foreground">
                Backend-reported configuration
              </p>
            </div>
            <Badge variant={mode.tone} dot pulse={mode.pulse} className="shrink-0">
              {mode.label}
            </Badge>
          </div>
        )}
      </div>
    </aside>
  );
}
