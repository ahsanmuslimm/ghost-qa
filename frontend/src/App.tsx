import { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ProtectedRoute } from './components/layout/RootLayout';
import { LoginPage } from './pages/Login';
import { DashboardPage } from './pages/Dashboard';
import { RunsListPage } from './pages/RunsList';
import { PipelineRunPage } from './pages/PipelineRun';
import { TestsListPage } from './pages/TestsList';
import { TestCasePage } from './pages/TestCase';
import { AdminPage } from './pages/Admin';
import { NotFoundPage } from './pages/NotFound';
import { useThemeStore, watchSystemTheme } from './stores/themeStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 15_000,
      refetchOnWindowFocus: false,
    },
  },
});

function ThemeManager() {
  const theme = useThemeStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.classList.toggle(
      'dark',
      theme === 'dark' ||
        (theme === 'system' &&
          window.matchMedia('(prefers-color-scheme: dark)').matches)
    );
  }, [theme]);

  useEffect(() => watchSystemTheme(), []);
  return null;
}

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeManager />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            {/* All authenticated pages live under the protected layout */}
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/runs" element={<RunsListPage />} />
              <Route path="/runs/:id" element={<PipelineRunPage />} />
              <Route path="/tests" element={<TestsListPage />} />
              <Route path="/tests/:id" element={<TestCasePage />} />
              <Route path="/admin" element={<AdminPage />} />
            </Route>

            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            className: 'text-sm',
            style: {
              background: 'hsl(var(--popover))',
              color: 'hsl(var(--popover-foreground))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '6px',
              boxShadow: 'var(--shadow-md)',
              font: 'inherit',
            },
            success: { iconTheme: { primary: 'hsl(var(--success))', secondary: '#fff' } },
            error: { iconTheme: { primary: 'hsl(var(--danger))', secondary: '#fff' } },
          }}
        />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
