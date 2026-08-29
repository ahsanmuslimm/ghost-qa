import { LogOut } from 'lucide-react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

export function Header({ leading }: { leading?: ReactNode }) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <header className="sticky top-0 z-10 h-16 border-b border-border bg-background/95 backdrop-blur">
      <div className="flex h-full items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-3">{leading}</div>
        {user && (
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 sm:flex">
              <span className="text-sm text-muted-foreground">{user.email}</span>
              <Badge variant="outline">{user.role}</Badge>
            </div>
            <Button variant="ghost" size="sm" onClick={handleLogout} aria-label="Logout">
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}
