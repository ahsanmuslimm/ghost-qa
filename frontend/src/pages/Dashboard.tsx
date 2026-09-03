import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Clock,
  GitPullRequest,
  RefreshCw,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { dashboardApi } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button, buttonVariants } from '../components/ui/button';
import { Alert, EmptyState, Skeleton } from '../components/ui/feedback';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { PageHeader } from '../components/common/PageHeader';
import { StatCard } from '../components/common/StatCard';
import { RiskBadge, StatusBadge } from '../components/common/StatusBadge';
import { formatRelative, humanize } from '../lib/variants';
import { axisTick, riskColor, statusColor, tooltipStyle, useChartTheme } from '../lib/chartTheme';
import { cn } from '../lib/utils';

const RISK_ORDER = ['low', 'medium', 'high', 'critical'];

export function DashboardPage() {
  const queryClient = useQueryClient();
  const palette = useChartTheme();

  const { data: overview, isLoading, error, isFetching } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: () => dashboardApi.overview().then((res) => res.data),
    refetchInterval: 30_000,
  });

  const metrics = useMemo(() => {
    const status = overview?.status_breakdown ?? {};
    const risk = overview?.risk_breakdown ?? {};

    const completed = status.completed ?? 0;
    const failed = status.failed ?? 0;
    const concluded = completed + failed;
    const inFlight =
      (status.queued ?? 0) + (status.extracting ?? 0) + (status.generating ?? 0) + (status.running ?? 0);

    return {
      totalRuns: overview?.total_pipeline_runs ?? 0,
      repositories: overview?.total_repositories ?? 0,
      concluded,
      successRate: concluded > 0 ? completed / concluded : null,
      awaitingApproval: status.awaiting_approval ?? 0,
      inFlight,
      elevatedRisk: (risk.high ?? 0) + (risk.critical ?? 0),
      assessed: Object.values(risk).reduce((sum, value) => sum + value, 0),
    };
  }, [overview]);

  const statusData = useMemo(
    () =>
      Object.entries(overview?.status_breakdown ?? {})
        .map(([status, count]) => ({ status, label: humanize(status), count }))
        .sort((a, b) => b.count - a.count),
    [overview]
  );

  const riskData = useMemo(
    () =>
      RISK_ORDER.filter((level) => (overview?.risk_breakdown[level] ?? 0) > 0).map((level) => ({
        name: level,
        label: humanize(level),
        value: overview?.risk_breakdown[level] ?? 0,
      })),
    [overview]
  );

  if (isLoading) {
    return (
      <div className="space-y-5" aria-busy="true">
        <Skeleton className="h-12 w-72" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((index) => (
            <Skeleton key={index} className="h-[104px]" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-5">
          <Skeleton className="h-[300px] lg:col-span-3" />
          <Skeleton className="h-[300px] lg:col-span-2" />
        </div>
        <Skeleton className="h-[320px]" />
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="space-y-5">
        <PageHeader title="Pipeline Overview" />
        <Alert variant="destructive" title="Unable to load dashboard">
          The Ghost QA API did not respond. Confirm the backend is running and reachable from this
          browser, then retry.
        </Alert>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] })}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Pipeline Overview"
        description="Webhook-triggered test generation, approval gates, execution and risk scoring across connected repositories."
        actions={
          <Button
            variant="secondary"
            size="sm"
            disabled={isFetching}
            onClick={() => queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] })}
          >
            <RefreshCw className={isFetching ? 'h-3.5 w-3.5 animate-spin' : 'h-3.5 w-3.5'} />
            Refresh
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Pipeline runs"
          value={metrics.totalRuns}
          icon={Activity}
          caption={`${metrics.repositories} connected ${metrics.repositories === 1 ? 'repository' : 'repositories'}`}
          href="/runs"
        />
        <StatCard
          label="Success rate"
          value={
            metrics.successRate === null ? '—' : `${Math.round(metrics.successRate * 100)}%`
          }
          icon={CheckCircle2}
          tone={
            metrics.successRate === null
              ? 'neutral'
              : metrics.successRate >= 0.9
                ? 'success'
                : metrics.successRate >= 0.7
                  ? 'warning'
                  : 'danger'
          }
          caption={
            metrics.concluded > 0
              ? `${metrics.concluded} concluded in the last 10 runs`
              : 'No concluded runs yet'
          }
        />
        <StatCard
          label="Awaiting approval"
          value={metrics.awaitingApproval}
          icon={Clock}
          tone={metrics.awaitingApproval > 0 ? 'warning' : 'neutral'}
          caption={
            metrics.inFlight > 0 ? `${metrics.inFlight} currently in progress` : 'Queue is idle'
          }
          href="/runs"
        />
        <StatCard
          label="Elevated risk"
          value={metrics.elevatedRisk}
          icon={AlertTriangle}
          tone={metrics.elevatedRisk > 0 ? 'danger' : 'success'}
          caption={
            metrics.assessed > 0
              ? `${metrics.assessed} assessed as high or critical`
              : 'No risk assessments yet'
          }
        />
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Run status distribution</CardTitle>
            <p className="text-2xs text-muted-foreground">Last 10 pipeline runs by terminal state</p>
          </CardHeader>
          <CardContent>
            {statusData.length === 0 ? (
              <EmptyState icon={Activity} title="No runs recorded" description="Trigger a webhook to start the first pipeline." />
            ) : (
              <ResponsiveContainer width="100%" height={232}>
                <BarChart
                  data={statusData}
                  layout="vertical"
                  margin={{ top: 4, right: 16, bottom: 0, left: 8 }}
                  barCategoryGap={8}
                >
                  <XAxis
                    type="number"
                    allowDecimals={false}
                    axisLine={false}
                    tickLine={false}
                    tick={axisTick(palette)}
                    stroke={palette.grid}
                  />
                  <YAxis
                    type="category"
                    dataKey="label"
                    width={112}
                    axisLine={false}
                    tickLine={false}
                    tick={axisTick(palette)}
                    stroke={palette.grid}
                  />
                  <Tooltip {...tooltipStyle(palette)} cursor={{ fill: palette.grid, opacity: 0.3 }} />
                  <Bar dataKey="count" radius={[0, 3, 3, 0]} maxBarSize={22}>
                    {statusData.map((entry) => (
                      <Cell key={entry.status} fill={statusColor(entry.status, palette)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Risk exposure</CardTitle>
            <p className="text-2xs text-muted-foreground">Highest assessed risk per run</p>
          </CardHeader>
          <CardContent>
            {riskData.length === 0 ? (
              <EmptyState icon={AlertTriangle} title="No risk data" description="Risk scoring runs after tests are generated." />
            ) : (
              <div className="flex items-center gap-4">
                <div className="relative h-[168px] w-[168px] shrink-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={riskData}
                        dataKey="value"
                        nameKey="label"
                        innerRadius={54}
                        outerRadius={78}
                        paddingAngle={2}
                        stroke={palette.tooltipBg}
                        strokeWidth={2}
                      >
                        {riskData.map((entry) => (
                          <Cell key={entry.name} fill={riskColor(entry.name, palette)} />
                        ))}
                      </Pie>
                      <Tooltip {...tooltipStyle(palette)} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                    <span className="numeric text-xl font-semibold leading-none text-foreground">
                      {metrics.assessed}
                    </span>
                    <span className="label-caps mt-1">Assessed</span>
                  </div>
                </div>

                <ul className="min-w-0 flex-1 space-y-2">
                  {riskData.map((entry) => (
                    <li key={entry.name} className="flex items-center justify-between gap-2 text-xs">
                      <span className="flex min-w-0 items-center gap-2">
                        <span
                          className="h-2 w-2 shrink-0 rounded-sm"
                          style={{ backgroundColor: riskColor(entry.name, palette) }}
                          aria-hidden="true"
                        />
                        <span className="truncate text-muted-foreground">{entry.label}</span>
                      </span>
                      <span className="numeric font-medium text-foreground">{entry.value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
          <div className="space-y-1">
            <CardTitle>Recent pipeline runs</CardTitle>
            <p className="text-2xs text-muted-foreground">Newest first · auto-refreshes every 30s</p>
          </div>
          <Link
            to="/runs"
            className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), 'shrink-0')}
          >
            View all
            <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </CardHeader>

        {overview.recent_runs.length === 0 ? (
          <EmptyState
            icon={GitPullRequest}
            title="No pipeline runs yet"
            description="Open a pull request on a connected repository, or post a sample webhook, to generate the first run."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run</TableHead>
                <TableHead>Repository</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead className="text-right">Triggered</TableHead>
                <TableHead className="w-8" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {overview.recent_runs.map((run) => (
                <TableRow key={run.id} className="group">
                  <TableCell>
                    <Link
                      to={`/runs/${run.id}`}
                      className="font-mono text-xs font-medium text-foreground hover:text-primary hover:underline"
                    >
                      {run.pr_number ? `PR #${run.pr_number}` : run.id.slice(0, 8)}
                    </Link>
                  </TableCell>
                  <TableCell className="max-w-[220px] truncate text-muted-foreground">
                    {run.repository}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={run.status} />
                  </TableCell>
                  <TableCell>
                    <RiskBadge level={run.risk_level} />
                  </TableCell>
                  <TableCell className="numeric text-right text-muted-foreground">
                    <time dateTime={run.created_at ?? undefined} title={run.created_at ?? undefined}>
                      {formatRelative(run.created_at)}
                    </time>
                  </TableCell>
                  <TableCell className="pr-3 text-right">
                    <ChevronRight
                      className="ml-auto h-3.5 w-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100"
                      aria-hidden="true"
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
