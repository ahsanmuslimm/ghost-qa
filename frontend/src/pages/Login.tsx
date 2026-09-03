import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Lock } from 'lucide-react';
import toast from 'react-hot-toast';
import { authApi, systemApi } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import { Button } from '../components/ui/button';
import { FieldError, Input, Label } from '../components/ui/input';
import { Alert, Spinner } from '../components/ui/feedback';
import { BrandMark } from '../components/common/Brand';

/** Backend reachability + run mode, shown on the auth screen as a status line. */
function useBackendStatus() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['system-health'],
    queryFn: async () => (await systemApi.health()).data,
    staleTime: 60_000,
    retry: 1,
  });

  if (isLoading) return { label: 'Checking API…', ok: true, pulse: true };
  if (isError || !data) return { label: 'API unreachable', ok: false, pulse: false };
  if (data.demo_mode) return { label: 'API online · Demo mode', ok: true, pulse: false };
  if (data.execution_backend === 'uipath') {
    return { label: 'API online · Live mode (UiPath)', ok: true, pulse: false };
  }
  return { label: 'API online · Live mode', ok: true, pulse: false };
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((s) => s.login);
  const status = useBackendStatus();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  function validate(): boolean {
    const next: typeof errors = {};
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) next.email = 'Enter a valid email address.';
    if (password.length < 8) next.password = 'Password must be at least 8 characters.';
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    if (!validate() || isLoading) return;

    setIsLoading(true);
    try {
      const { data } = await authApi.login(email, password);
      login(data.token);
      toast.success('Signed in');
      const from = (location.state as { from?: string } | null)?.from || '/';
      navigate(from, { replace: true });
    } catch {
      setFormError('Invalid email or password. Check your credentials and try again.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-surface px-4 py-10">
      <div className="bg-grid pointer-events-none absolute inset-0 opacity-60" aria-hidden="true" />
      <div className="bg-radial-fade pointer-events-none absolute inset-0" aria-hidden="true" />

      <div className="relative w-full max-w-[368px]">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <BrandMark className="h-10 w-10 rounded-lg [&_svg]:h-5 [&_svg]:w-5" />
          <div className="space-y-1">
            <h1 className="text-lg font-semibold tracking-tight text-foreground">Ghost QA</h1>
            <p className="text-xs text-muted-foreground">
              Autonomous test generation, approval and execution
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-5 shadow-raised">
          <div className="mb-4 flex items-center gap-2">
            <Lock className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
            <h2 className="text-xs font-semibold uppercase tracking-caps text-muted-foreground">
              Sign in
            </h2>
          </div>

          {formError && (
            <Alert variant="destructive" className="mb-4">
              {formError}
            </Alert>
          )}

          <form onSubmit={onSubmit} className="space-y-3.5" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                autoFocus
                placeholder="you@company.com"
                className="h-9"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? 'email-error' : undefined}
              />
              {errors.email && <FieldError id="email-error">{errors.email}</FieldError>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                className="h-9"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                aria-invalid={!!errors.password}
                aria-describedby={errors.password ? 'password-error' : undefined}
              />
              {errors.password && <FieldError id="password-error">{errors.password}</FieldError>}
            </div>

            <Button type="submit" className="h-9 w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Spinner className="h-3.5 w-3.5" />
                  Verifying credentials…
                </>
              ) : (
                <>
                  Continue
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </Button>
          </form>
        </div>

        <div className="mt-4 flex items-center justify-between gap-3 px-1">
          <p className="text-2xs text-muted-foreground">
            Accounts are provisioned by your administrator.
          </p>
          <span className="flex shrink-0 items-center gap-1.5 text-2xs text-muted-foreground">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                status.ok ? 'bg-success' : 'bg-danger'
              } ${status.pulse ? 'animate-pulse-soft' : ''}`}
              aria-hidden="true"
            />
            {status.label}
          </span>
        </div>
      </div>
    </div>
  );
}
