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

// Global error boundary (Task 5.13): catches render crashes and offers a
// clean recovery path instead of a blank screen.
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
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <div className="w-full max-w-md space-y-4 rounded-lg border border-border bg-card p-8 text-center">
          <AlertTriangle className="mx-auto h-10 w-10 text-amber-400" aria-hidden="true" />
          <h1 className="text-xl font-bold">Something went wrong</h1>
          {this.state.message && (
            <p className="break-words font-mono text-xs text-muted-foreground">{this.state.message}</p>
          )}
          <Button onClick={() => window.location.reload()}>
            <RefreshCw className="h-4 w-4" /> Reload
          </Button>
        </div>
      </div>
    );
  }
}
