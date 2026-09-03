import { useEffect, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, LogOut, Monitor, Moon, Sun } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useThemeStore, watchSystemTheme, type Theme } from '../../stores/themeStore';
import { cn } from '../../lib/utils';
import { Button } from '../ui/button';
import { Menu, MenuItem, MenuLabel, MenuSeparator, MenuTrigger } from '../ui/menu';

const THEME_OPTIONS: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
];

function ThemeMenu() {
  const { theme, setTheme } = useThemeStore();
  const Active = THEME_OPTIONS.find((option) => option.value === theme)?.icon ?? Monitor;

  return (
    <Menu>
      <MenuTrigger
        aria-label="Change theme"
        className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        <Active className="h-4 w-4" />
      </MenuTrigger>
      <MenuLabel>Appearance</MenuLabel>
      {THEME_OPTIONS.map((option) => (
        <MenuItem
          key={option.value}
          icon={option.icon}
          onSelect={() => setTheme(option.value)}
          className="justify-between"
        >
          <span className="flex items-center gap-2">
            <option.icon className="h-3.5 w-3.5 opacity-70" aria-hidden="true" />
            {option.label}
          </span>
          {theme === option.value && <Check className="h-3.5 w-3.5 text-primary" />}
        </MenuItem>
      ))}
    </Menu>
  );
}

function initials(email: string): string {
  const local = email.split('@')[0] ?? email;
  const parts = local.split(/[._-]+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return local.slice(0, 2).toUpperCase();
}

export function Header({ leading }: { leading?: ReactNode }) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [now, setNow] = useState(() => new Date());

  // Follow the OS preference while theme === 'system'.
  useEffect(() => watchSystemTheme(), []);

  // Keeps the clock in the header honest without a heavy interval.
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(id);
  }, []);

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const timeLabel = now.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between gap-3 border-b border-border bg-background/90 px-3 backdrop-blur supports-[backdrop-filter]:bg-background/75 md:px-5">
      <div className="flex min-w-0 items-center gap-2">
        {leading}
        {leading && (
          <span className="h-4 w-px bg-border md:hidden" aria-hidden="true" />
        )}
        <span className="numeric hidden text-2xs text-muted-foreground lg:inline">{timeLabel}</span>
      </div>

      {user && (
        <div className="flex items-center gap-1.5">
          <ThemeMenu />

          <span className="mx-0.5 hidden h-5 w-px bg-border sm:block" aria-hidden="true" />

          <Menu>
            <MenuTrigger
              aria-label="Account menu"
              className="flex items-center gap-2 rounded-md py-1 pl-1 pr-1.5 transition-colors hover:bg-muted sm:pr-2"
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md border border-border bg-surface text-2xs font-semibold text-muted-foreground">
                {initials(user.email)}
              </span>
              <span className="hidden min-w-0 flex-col items-start leading-tight sm:flex">
                <span className="max-w-[160px] truncate text-xs font-medium text-foreground">
                  {user.email}
                </span>
                <span className="text-2xs capitalize text-muted-foreground">{user.role}</span>
              </span>
            </MenuTrigger>

            <MenuLabel>Signed in as</MenuLabel>
            <p className="truncate px-2 pb-1.5 text-xs text-foreground">{user.email}</p>
            <MenuSeparator />
            <MenuItem
              icon={LogOut}
              tone="danger"
              onSelect={handleLogout}
              className={cn('justify-start')}
            >
              Sign out
            </MenuItem>
          </Menu>

          <span className="sm:hidden">
            <Button variant="ghost" size="icon-sm" onClick={handleLogout} aria-label="Sign out">
              <LogOut className="h-4 w-4" />
            </Button>
          </span>
        </div>
      )}
    </header>
  );
}
