import { useState } from 'react';
import { NavLink, Navigate, Outlet, useLocation } from 'react-router-dom';
import {
  Activity,
  FlaskConical,
  Ghost,
  LayoutDashboard,
  Menu,
  Shield,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useUIStore } from '../../stores/uiStore';
import { Button } from '../ui/button';
import { Header } from './Header';
import { cn } from '../../lib/utils';

// Guards every authenticated route; bounces anonymous users to /login and
// remembers where they were heading.
export function ProtectedRoute() {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <RootLayout />;
}

function RootLayout() {
  const { isSidebarOpen, toggleSidebar } = useUIStore();
  const { user, hasPermission } = useAuthStore();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
    { to: '/runs', label: 'Pipeline Runs', icon: Activity, end: false },
    { to: '/tests', label: 'Test Cases', icon: FlaskConical, end: false },
  ];
  if (user && (user.role === 'admin' || hasPermission('user:view'))) {
    navItems.push({ to: '/admin', label: 'Admin', icon: Shield, end: false });
  }

  function handleMenuClick() {
    if (window.innerWidth < 768) {
      setMobileOpen((open) => !open);
    } else {
      toggleSidebar();
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        {/* Mobile drawer backdrop */}
        {mobileOpen && (
          <div
            className="fixed inset-0 z-30 bg-black/60 md:hidden"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
        )}

        <aside
          aria-label="Main navigation"
          className={cn(
            'w-64 shrink-0 flex-col border-r border-border bg-card',
            // Mobile: hidden unless the drawer is toggled open
            mobileOpen ? 'fixed inset-y-0 left-0 z-40 flex' : 'hidden',
            // Desktop: static column, visibility follows the persisted toggle
            'md:sticky md:top-0 md:z-auto',
            isSidebarOpen ? 'md:flex' : 'md:hidden'
          )}
        >
          <div className="flex items-center gap-2 border-b border-border p-4">
            <Ghost className="h-6 w-6 text-primary" aria-hidden="true" />
            <span className="text-lg font-bold">Ghost QA</span>
          </div>
          <nav className="flex-1 space-y-1 p-3">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                    isActive
                      ? 'bg-accent/15 text-primary'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )
                }
              >
                <item.icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="border-t border-border p-4 text-xs text-muted-foreground">
            AI-Powered QA Automation
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <Header
            leading={
              <Button
                variant="ghost"
                size="icon"
                onClick={handleMenuClick}
                aria-label="Toggle navigation"
                aria-expanded={mobileOpen || isSidebarOpen}
              >
                <Menu className="h-4 w-4" />
              </Button>
            }
          />
          <main className="flex-1 p-4 md:p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
