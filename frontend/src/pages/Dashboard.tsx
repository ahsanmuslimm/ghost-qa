import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  GitBranch,
  type LucideIcon,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { dashboardApi } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Skeleton, Alert } from '../components/ui/feedback';
import { formatDateTime, riskVariant, statusVariant } from '../lib/variants';

const RISK_COLORS: Record<string, string> = {
  low: '#10b981',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#b91c1c',
};

function StatCard({ title, value, icon: Icon }: { title: string; value: string | number; icon: LucideIcon }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  const { data: overview, isLoading, error } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: () => dashboardApi.overview().then((res) => res.data),
  });

  if (isLoading) {
    return (
      <div className="space-y-6" aria-busy="true">
        <Skeleton className="h-9 w-64" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    );
  }

  if (error || !overview) {
    return (
      <Alert variant="destructive" title="Failed to load dashboard">
        Could not reach the Ghost QA backend. Verify the API server is running.
      </Alert>
    );
  }

  const statusData = Object.entries(overview.status_breakdown).map(([status, count]) => ({
    status,
    count,
  }));
  const riskData = Object.entries(overview.risk_breakdown).map(([level, count]) => ({
    name: level,
    value: count,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold md:text-3xl">Welcome back, {user?.email}</h1>
        <p className="text-muted-foreground">Here&apos;s what&apos;s happening with Ghost QA</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard title="Pipeline Runs" value={overview.total_pipeline_runs} icon={Activity} />
        <StatCard title="Repositories" value={overview.total_repositories} icon={GitBranch} />
        <StatCard
          title="Pass Rate (recent)"
          value={passRate(overview.status_breakdown)}
          icon={CheckCircle2}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Run Statuses</CardTitle>
          </CardHeader>
          <CardContent>
            {statusData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={statusData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="status" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      background: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: 8,
                    }}
                  />
                  <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
              Risk Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            {riskData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={riskData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={90} paddingAngle={3}>
                    {riskData.map((entry) => (
                      <Cell key={entry.name} fill={RISK_COLORS[entry.name] || '#888'} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: 8,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Pipeline Runs</CardTitle>
          <Link to="/runs" className="text-sm text-primary hover:underline">
            View all
          </Link>
        </CardHeader>
        <CardContent className="space-y-3">
          {overview.recent_runs.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No pipeline runs yet. Push a PR to a connected repository to trigger one.
            </p>
          )}
          {overview.recent_runs.map((run) => (
            <Link
              key={run.id}
              to={`/runs/${run.id}`}
              className="flex flex-col gap-3 rounded-lg border border-border p-4 transition-colors hover:bg-muted/50 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                  {run.pr_number ?? '–'}
                </div>
                <div>
                  <p className="font-medium">
                    PR #{run.pr_number ?? '—'} · {run.repository}
                  </p>
                  <p className="text-sm text-muted-foreground">{formatDateTime(run.created_at)}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={riskVariant(run.risk_level)}>{run.risk_level || 'pending'}</Badge>
                <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
              </div>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function EmptyChart() {
  return (
    <div className="flex h-[260px] items-center justify-center text-sm text-muted-foreground">
      No data yet
    </div>
  );
}

function passRate(statusBreakdown: Record<string, number>): string {
  const completed = statusBreakdown.completed || 0;
  const failed = statusBreakdown.failed || 0;
  const total = completed + failed;
  if (total === 0) return '—';
  return `${Math.round((completed / total) * 100)}%`;
}
