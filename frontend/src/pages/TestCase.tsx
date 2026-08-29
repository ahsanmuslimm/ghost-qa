import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { ArrowLeft, Play, ShieldCheck, XCircle } from 'lucide-react';
import { healApi, testApi } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import type { HealAttempt } from '../types';
import { useAllTests } from './TestsList';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Skeleton, Alert, Spinner } from '../components/ui/feedback';
import {
  formatDateTime,
  healVariant,
  outcomeVariant,
  priorityVariant,
  riskVariant,
} from '../lib/variants';

export function TestCasePage() {
  const { id } = useParams<{ id: string }>();
  const { data: tests, isLoading } = useAllTests();
  const test = tests?.find((t) => t.id === id);

  if (isLoading) {
    return (
      <div className="space-y-4" aria-busy="true">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-72" />
      </div>
    );
  }

  if (!test) {
    return (
      <Alert variant="destructive" title="Test case not found">
        This test may belong to an older run not on the first page.
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/tests"
          className="mb-1 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> Back to tests
        </Link>
        <h1 className="text-2xl font-bold">{test.title || test.id.slice(0, 8)}</h1>
        <p className="text-muted-foreground">
          Run{' '}
          <Link to={`/runs/${test.run_id}`} className="text-primary hover:underline">
            PR #{test.pr_number ?? test.run_id.slice(0, 8)}
          </Link>{' '}
          · {test.repository}
        </p>
      </div>

      <TestDetailCard testId={test.id} />
      <HealsSection testId={test.id} />
    </div>
  );
}

function TestDetailCard({ testId }: { testId: string }) {
  const { data: tests } = useAllTests();
  const test = tests?.find((t) => t.id === testId);
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const queryClient = useQueryClient();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['all-tests'] });

  const approve = useMutation({
    mutationFn: () => testApi.approve(testId),
    onSuccess: () => {
      toast.success('Test approved');
      invalidate();
    },
    onError: () => toast.error('Approval failed'),
  });

  const reject = useMutation({
    mutationFn: () => testApi.reject(testId),
    onSuccess: () => {
      toast.success('Test rejected');
      invalidate();
    },
    onError: () => toast.error('Rejection failed'),
  });

  if (!test) return null;

  const canReview = test.approval_status === 'pending' || test.approval_status === null;
  const busy = approve.isPending || reject.isPending;

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 space-y-0">
        <CardTitle>Test Details</CardTitle>
        <div className="flex gap-2">
          {hasPermission('test:approve') && canReview && (
            <Button size="sm" onClick={() => approve.mutate()} disabled={busy}>
              {approve.isPending ? <Spinner className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
              Approve
            </Button>
          )}
          {hasPermission('test:reject') && canReview && (
            <Button size="sm" variant="destructive" onClick={() => reject.mutate()} disabled={busy}>
              {reject.isPending ? <Spinner className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
              Reject
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Badge variant={priorityVariant(test.priority)}>{test.priority || 'no priority'}</Badge>
          <Badge variant={riskVariant(test.risk_level)}>{test.risk_level || 'no risk'}</Badge>
          <Badge variant="outline">approval: {test.approval_status || 'pending'}</Badge>
          <Badge variant={outcomeVariant(test.outcome ?? test.status)}>
            {test.outcome ?? test.status ?? 'pending'}
          </Badge>
        </div>

        <dl className="grid grid-cols-1 gap-x-8 gap-y-3 text-sm md:grid-cols-2">
          <Field label="Test Type" value={test.test_type} />
          <Field label="Executed" value={formatDateTime(test.executed_at)} />
          <Field label="Approved By" value={test.approved_by} />
          <Field label="Duration" value={test.duration_ms != null ? `${test.duration_ms}ms` : null} />
          <Field label="Expected Result" value={test.expected_result} wide />
          <Field label="Risk Rationale" value={test.risk_rationale} wide />
          {test.failure_message && <Field label="Failure" value={test.failure_message} wide mono />}
        </dl>
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  value,
  wide,
  mono,
}: {
  label: string;
  value: string | null | undefined;
  wide?: boolean;
  mono?: boolean;
}) {
  return (
    <div className={wide ? 'md:col-span-2' : undefined}>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={`mt-0.5 break-words ${mono ? 'font-mono text-xs' : ''}`}>{value || '—'}</dd>
    </div>
  );
}

function HealsSection({ testId }: { testId: string }) {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const queryClient = useQueryClient();

  const { data: heals, isLoading } = useQuery({
    queryKey: ['test-heals', testId],
    queryFn: () => testApi.getHeals(testId).then((res) => res.data),
    enabled: !!testId,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['test-heals', testId] });

  const approveHeal = useMutation({
    mutationFn: (id: string) => healApi.approve(id),
    onSuccess: () => {
      toast.success('Heal approved');
      invalidate();
    },
    onError: () => toast.error('Heal approval failed'),
  });

  const rejectHeal = useMutation({
    mutationFn: (id: string) => healApi.reject(id),
    onSuccess: () => {
      toast.success('Heal rejected');
      invalidate();
    },
    onError: () => toast.error('Heal rejection failed'),
  });

  const executeHeal = useMutation({
    mutationFn: (id: string) => healApi.execute(id),
    onSuccess: () => {
      toast.success('Heal executed — healed test clone created');
      invalidate();
      queryClient.invalidateQueries({ queryKey: ['all-tests'] });
    },
    onError: () => toast.error('Heal execution failed'),
  });

  const busyFor = (healId: string) =>
    (approveHeal.isPending || rejectHeal.isPending || executeHeal.isPending) &&
    [approveHeal.variables, rejectHeal.variables, executeHeal.variables].includes(healId);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Heal Attempts ({heals?.length ?? 0})</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading && (
          <div className="flex justify-center py-6" aria-busy="true">
            <Spinner />
          </div>
        )}
        {!isLoading && (!heals || heals.length === 0) && (
          <p className="text-sm text-muted-foreground">No heal attempts for this test yet.</p>
        )}
        {heals?.map((heal) => (
          <HealCard
            key={heal.id}
            heal={heal}
            busy={busyFor(heal.id)}
            canApprove={hasPermission('heal:approve')}
            canExecute={hasPermission('heal:execute')}
            onApprove={() => approveHeal.mutate(heal.id)}
            onReject={() => rejectHeal.mutate(heal.id)}
            onExecute={() => executeHeal.mutate(heal.id)}
          />
        ))}
      </CardContent>
    </Card>
  );
}

function HealCard({
  heal,
  busy,
  canApprove,
  canExecute,
  onApprove,
  onReject,
  onExecute,
}: {
  heal: HealAttempt;
  busy: boolean;
  canApprove: boolean;
  canExecute: boolean;
  onApprove: () => void;
  onReject: () => void;
  onExecute: () => void;
}) {
  const rationale = (heal.rationale as string | undefined) ?? null;
  const failureType = (heal.failure_type as string | undefined) ?? null;

  return (
    <div className="rounded-lg border border-border p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-muted-foreground">{heal.id.slice(0, 8)}</span>
          <Badge variant={healVariant(heal.status)}>{heal.status}</Badge>
          {failureType && <Badge variant="outline">{failureType}</Badge>}
        </div>
        <div className="flex gap-2">
          {canApprove && heal.status === 'proposed' && (
            <>
              <Button size="sm" onClick={onApprove} disabled={busy}>
                Approve
              </Button>
              <Button size="sm" variant="destructive" onClick={onReject} disabled={busy}>
                Reject
              </Button>
            </>
          )}
          {canExecute && heal.status === 'accepted' && (
            <Button size="sm" onClick={onExecute} disabled={busy}>
              {busy ? <Spinner className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              Execute
            </Button>
          )}
        </div>
      </div>
      {rationale && (
        <p className="mb-3 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">AI rationale: </span>
          {rationale}
        </p>
      )}
      <p className="text-xs text-muted-foreground">Proposed {formatDateTime(heal.proposed_at as string | null)}</p>
    </div>
  );
}
