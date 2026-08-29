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

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 15_000,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
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
            style: {
              background: 'hsl(var(--card))',
              color: 'hsl(var(--foreground))',
              border: '1px solid hsl(var(--border))',
            },
          }}
        />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
