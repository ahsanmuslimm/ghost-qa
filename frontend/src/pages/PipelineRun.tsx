import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { ArrowLeft, CheckCircle2 } from 'lucide-react';
import { pipelineApi } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import type { PipelineRun, RiskReport, TestCase, TestResult } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Skeleton, Alert, Spinner } from '../components/ui/feedback';
import {
  formatDateTime,
  formatDuration,
  outcomeVariant,
  priorityVariant,
  riskVariant,
  statusVariant,
} from '../lib/variants';

export function PipelineRunPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  const { data: run, isLoading, error } = useQuery({
    queryKey: ['pipeline-run', id],
    queryFn: () => pipelineApi.get(id || '').then((res) => res.data),
    enabled: !!id,
  });

  const { data: tests } = useQuery({
    queryKey: ['pipeline-tests', id],
    queryFn: () => pipelineApi.getTests(id || '').then((res) => res.data),
    enabled: !!id,
  });

  const { data: results } = useQuery({
    queryKey: ['pipeline-results', id],
    queryFn: () => pipelineApi.getResults(id || '').then((res) => res.data),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="space-y-4" aria-busy="true">
        <Skeleton className="h-9 w-72" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" title="Failed to load pipeline run">
        The run may not exist or the backend is unreachable.
      </Alert>
    );
  }

  if (!run) return null;

  const passed = results?.filter((r) => r.outcome === 'passed').length ?? 0;
  const failed = results?.filter((r) => r.outcome === 'failed').length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <button
            onClick={() => navigate('/runs')}
            className="mb-1 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> Back to runs
          </button>
          <h1 className="text-2xl font-bold">Pipeline Run {run.id.slice(0, 8)}</h1>
          <p className="text-muted-foreground">
            PR #{run.pr_number ?? '—'} · {run.repository}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={riskVariant(run.risk_level)}>{run.risk_level || 'pending'}</Badge>
          <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <MiniStat title="Total Tests" value={tests?.length ?? '…'} />
        <MiniStat title="Passed" value={passed} tone="text-emerald-400" />
        <MiniStat title="Failed" value={failed} tone="text-red-400" />
        <MiniStat title="Duration" value={formatDuration(run.started_at, run.completed_at)} />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="tests">Tests</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="report">Report</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab run={run} />
        </TabsContent>
        <TabsContent value="tests">
          <TestsTab tests={tests ?? []} />
        </TabsContent>
        <TabsContent value="results">
          <ResultsTab results={results ?? []} />
        </TabsContent>
        <TabsContent value="report">
          <ReportTab runId={id || ''} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function MiniStat({ title, value, tone }: { title: string; value: string | number; tone?: string }) {
  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-xs font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-xl font-bold ${tone ?? ''}`}>{value}</div>
      </CardContent>
    </Card>
  );
}

function OverviewTab({ run }: { run: PipelineRun }) {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const queryClient = useQueryClient();

  const approve = useMutation({
    mutationFn: () => pipelineApi.approve(run.id),
    onSuccess: () => {
      toast.success('All pending tests approved');
      queryClient.invalidateQueries({ queryKey: ['pipeline-run', run.id] });
      queryClient.invalidateQueries({ queryKey: ['pipeline-tests', run.id] });
    },
    onError: () => toast.error('Approval failed — check test states / permissions'),
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>Pipeline Overview</CardTitle>
        {hasPermission('test:approve') && run.status === 'awaiting_approval' && (
          <Button size="sm" onClick={() => approve.mutate()} disabled={approve.isPending}>
            {approve.isPending ? <Spinner className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
            Approve All Tests
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="space-y-2 text-sm">
            <h3 className="font-medium">Basic Information</h3>
            <p className="text-muted-foreground">Repository: <span className="text-foreground">{run.repository}</span></p>
            <p className="text-muted-foreground">PR: <span className="text-foreground">#{run.pr_number ?? '—'}</span></p>
            <p className="text-muted-foreground">
              Commit: <span className="font-mono text-foreground">{run.commit_sha?.slice(0, 8) ?? '—'}</span>
            </p>
          </div>
          <div className="space-y-2 text-sm">
            <h3 className="font-medium">Timing</h3>
            <p className="text-muted-foreground">Created: <span className="text-foreground">{formatDateTime(run.created_at)}</span></p>
            <p className="text-muted-foreground">Started: <span className="text-foreground">{formatDateTime(run.started_at)}</span></p>
            <p className="text-muted-foreground">Completed: <span className="text-foreground">{formatDateTime(run.completed_at)}</span></p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function TestsTab({ tests }: { tests: TestCase[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Test Cases ({tests.length})</CardTitle>
      </CardHeader>
      <CardContent>
        {tests.length === 0 ? (
          <p className="text-sm text-muted-foreground">No test cases generated yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Test</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Outcome</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tests.map((test) => (
                <TableRow key={test.id}>
                  <TableCell>
                    <Link to={`/tests/${test.id}`} className="font-medium text-primary hover:underline">
                      {test.title || test.id.slice(0, 8)}
                    </Link>
                  </TableCell>
                  <TableCell>{test.test_type || '—'}</TableCell>
                  <TableCell>
                    <Badge variant={priorityVariant(test.priority)}>{test.priority || '—'}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={riskVariant(test.risk_level)}>{test.risk_level || '—'}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={outcomeVariant(test.outcome ?? test.status)}>
                      {test.outcome ?? test.status ?? 'pending'}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function ResultsTab({ results }: { results: TestResult[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Test Results ({results.length})</CardTitle>
      </CardHeader>
      <CardContent>
        {results.length === 0 ? (
          <p className="text-sm text-muted-foreground">No execution results yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Test</TableHead>
                <TableHead>Outcome</TableHead>
                <TableHead>Failure Type</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Robot</TableHead>
                <TableHead>Executed</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {results.map((result) => (
                <TableRow key={result.id}>
                  <TableCell>
                    <Link to={`/tests/${result.test_case_id}`} className="font-mono text-primary hover:underline">
                      {result.test_case_id.slice(0, 8)}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant={outcomeVariant(result.outcome)}>{result.outcome}</Badge>
                  </TableCell>
                  <TableCell>{result.failure_type || '—'}</TableCell>
                  <TableCell>{result.duration_ms != null ? `${result.duration_ms}ms` : '—'}</TableCell>
                  <TableCell>{result.robot_id || '—'}</TableCell>
                  <TableCell className="text-muted-foreground">{formatDateTime(result.executed_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function ReportTab({ runId }: { runId: string }) {
  const { data: report, isLoading, error } = useQuery({
    queryKey: ['pipeline-report', runId],
    queryFn: () => pipelineApi.getReport(runId).then((res) => res.data),
    enabled: !!runId,
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6" aria-busy="true">
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" title="Risk report unavailable">
        The report can only be generated once the run has execution results.
      </Alert>
    );
  }

  return <RiskReportView report={report as RiskReport} />;
}

function RiskReportView({ report }: { report: RiskReport }) {
  const overall = report.risk_level ?? 'unknown';
  const entries = Object.entries(report).filter(([key]) => key !== 'risk_level');

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>Risk Report</CardTitle>
        <Badge variant={riskVariant(overall)}>{overall}</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-start justify-between gap-4 border-b border-border pb-2 text-sm last:border-0">
            <span className="font-mono text-muted-foreground">{key}</span>
            <span className="max-w-[60%] break-words text-right">
              {typeof value === 'object' ? (
                <pre className="overflow-x-auto text-xs text-muted-foreground">
                  {JSON.stringify(value, null, 2)}
                </pre>
              ) : (
                String(value)
              )}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
