import { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useUIStore } from '../../stores/uiStore';
import { Button } from '../ui/button';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

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
  const { isSidebarCollapsed, toggleSidebarCollapsed } = useUIStore();
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Navigating always dismisses the mobile drawer.
  useEffect(() => setMobileOpen(false), [location.pathname]);

  // The drawer must not scroll the page behind it.
  useEffect(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = mobileOpen ? 'hidden' : previous;
    return () => {
      document.body.style.overflow = previous;
    };
  }, [mobileOpen]);

  return (
    <div className="flex min-h-screen bg-surface">
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-foreground/40 backdrop-blur-[1px] md:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <Sidebar
        collapsed={isSidebarCollapsed}
        onToggleCollapse={toggleSidebarCollapsed}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          leading={
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setMobileOpen((open) => !open)}
              aria-label="Open navigation"
              aria-expanded={mobileOpen}
              className="md:hidden"
            >
              <Menu className="h-4 w-4" />
            </Button>
          }
        />
        <main className="flex-1 px-4 py-5 md:px-6 md:py-6">
          <div className="mx-auto w-full max-w-[1400px] space-y-5">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
