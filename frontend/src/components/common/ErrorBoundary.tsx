import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '../ui/button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string | null;
}

// Global error boundary: catches render crashes and offers a clean recovery
// path instead of a blank screen.
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled UI error:', error, info.componentStack);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div className="flex min-h-screen items-center justify-center bg-surface p-6">
        <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-raised">
          <div className="flex items-start gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-warning-border bg-warning-subtle">
              <AlertTriangle className="h-4 w-4 text-warning" aria-hidden="true" />
            </span>
            <div className="min-w-0 space-y-1">
              <h1 className="text-sm font-semibold text-foreground">Unexpected interface error</h1>
              <p className="text-xs leading-relaxed text-muted-foreground">
                The console failed to render this view. Reloading usually resolves it; the error has
                been logged to the browser console.
              </p>
            </div>
          </div>

          {this.state.message && (
            <pre className="mt-4 max-h-40 overflow-auto rounded-md border border-border bg-surface p-3 font-mono text-2xs leading-relaxed text-muted-foreground">
              {this.state.message}
            </pre>
          )}

          <div className="mt-5 flex justify-end">
            <Button size="sm" onClick={() => window.location.reload()}>
              <RefreshCw className="h-3.5 w-3.5" />
              Reload interface
            </Button>
          </div>
        </div>
      </div>
    );
  }
}
