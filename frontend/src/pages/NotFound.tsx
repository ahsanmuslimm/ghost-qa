import { Link } from 'react-router-dom';
import { Ghost } from 'lucide-react';
import { buttonVariants } from '../components/ui/button';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-4 text-center">
      <Ghost className="h-12 w-12 text-primary" aria-hidden="true" />
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-muted-foreground">This page seems to have vanished... like a ghost.</p>
      <Link to="/" className={buttonVariants()}>
        Back to Dashboard
      </Link>
    </div>
  );
}
