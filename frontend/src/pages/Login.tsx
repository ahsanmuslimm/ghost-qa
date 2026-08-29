import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Ghost } from 'lucide-react';
import toast from 'react-hot-toast';
import { authApi } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Spinner } from '../components/ui/feedback';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((s) => s.login);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [isLoading, setIsLoading] = useState(false);

  function validate(): boolean {
    const next: typeof errors = {};
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) next.email = 'Invalid email address';
    if (password.length < 8) next.password = 'Password must be at least 8 characters';
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate() || isLoading) return;

    setIsLoading(true);
    try {
      const { data } = await authApi.login(email, password);
      login(data.token);
      toast.success('Login successful');
      const from = (location.state as { from?: string } | null)?.from || '/';
      navigate(from, { replace: true });
    } catch {
      toast.error('Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-8 rounded-lg border border-border bg-card p-8 shadow-lg">
        <div className="space-y-2 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/15">
            <Ghost className="h-6 w-6 text-primary" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-bold">Ghost QA</h1>
          <p className="text-muted-foreground">AI-Powered QA Engineer</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-5" noValidate>
          <div className="space-y-1.5">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="admin@ghost.qa"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={!!errors.email}
            />
            {errors.email && (
              <p role="alert" className="text-xs text-red-400">
                {errors.email}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={!!errors.password}
            />
            {errors.password && (
              <p role="alert" className="text-xs text-red-400">
                {errors.password}
              </p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? (
              <>
                <Spinner className="h-4 w-4" /> Logging in...
              </>
            ) : (
              'Login'
            )}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Don&apos;t have an account? Contact your administrator.
        </p>
      </div>
    </div>
  );
}
