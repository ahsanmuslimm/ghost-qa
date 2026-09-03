import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ChevronRight, GitPullRequest, Search } from 'lucide-react';
import { pipelineApi } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input, Select } from '../components/ui/input';
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
import { Pagination } from '../components/common/Pagination';
import { RiskBadge, StatusBadge } from '../components/common/StatusBadge';
import { formatRelative, humanize } from '../lib/variants';

const STATUS_FILTERS = [
  'queued',
  'extracting',
  'generating',
  'awaiting_approval',
  'running',
  'completed',
  'failed',
];

export function RunsListPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('all');
  const [search, setSearch] = useState('');

  const { data, isLoading, error, isFetching, refetch } = useQuery({
    queryKey: ['runs', page],
    queryFn: () => pipelineApi.list(page).then((res) => res.data),
    refetchInterval: 30_000,
  });

  // Filtering is applied to the fetched page; the pager still reflects the
  // full server-side result set so totals stay honest.
  const rows = useMemo(() => {
    const all = data?.runs ?? [];
    const term = search.trim().toLowerCase();
    return all.filter((run) => {
      if (status !== 'all' && run.status !== status) return false;
      if (!term) return true;
      return (
        run.repository.toLowerCase().includes(term) ||
        String(run.pr_number ?? '').includes(term) ||
        run.id.toLowerCase().includes(term) ||
        (run.commit_sha ?? '').toLowerCase().includes(term)
      );
    });
  }, [data, search, status]);

  if (isLoading) {
    return (
      <div className="space-y-5" aria-busy="true">
        <Skeleton className="h-12 w-72" />
        <Skeleton className="h-8 w-full max-w-md" />
        <Skeleton className="h-[440px]" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-5">
        <PageHeader title="Pipeline Runs" />
        <Alert variant="destructive" title="Unable to load pipeline runs">
          The Ghost QA API did not respond. Confirm the backend is running, then retry.
        </Alert>
        <Button variant="secondary" size="sm" onClick={() => refetch()}>
          Retry
        </Button>
      </div>
    );
  }

  const filtered = status !== 'all' || search.trim().length > 0;

  return (
    <div className="space-y-5">
      <PageHeader
        title="Pipeline Runs"
        description="Every webhook-triggered run, from diff extraction through generation, approval, execution and reporting."
        actions={
          <Button
            variant="secondary"
            size="sm"
            disabled={isFetching}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
        }
      />

      <Card>
        <div className="flex flex-wrap items-center gap-2 border-b border-border px-4 py-3">
          <div className="relative min-w-[200px] flex-1">
            <Search
              className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search repository, PR, commit or run id…"
              aria-label="Search pipeline runs"
              className="pl-8"
            />
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="status-filter" className="label-caps whitespace-nowrap">
              Status
            </label>
            <Select
              id="status-filter"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="w-[168px]"
            >
              <option value="all">All statuses</option>
              {STATUS_FILTERS.map((value) => (
                <option key={value} value={value}>
                  {humanize(value)}
                </option>
              ))}
            </Select>
          </div>

          {filtered && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setStatus('all');
                setSearch('');
              }}
            >
              Clear
            </Button>
          )}
        </div>

        {rows.length === 0 ? (
          <EmptyState
            icon={GitPullRequest}
            title={filtered ? 'No runs match these filters' : 'No pipeline runs yet'}
            description={
              filtered
                ? 'Adjust the search term or status filter to widen the results.'
                : 'Open a pull request on a connected repository, or post a sample webhook, to generate the first run.'
            }
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run</TableHead>
                <TableHead>Repository</TableHead>
                <TableHead>Commit</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead className="text-right">Triggered</TableHead>
                <TableHead className="w-8" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((run) => (
                <TableRow key={run.id} className="group">
                  <TableCell>
                    <Link
                      to={`/runs/${run.id}`}
                      className="font-mono text-xs font-medium text-foreground hover:text-primary hover:underline"
                    >
                      {run.pr_number ? `PR #${run.pr_number}` : run.id.slice(0, 8)}
                    </Link>
                  </TableCell>
                  <TableCell className="max-w-[240px] truncate text-muted-foreground">
                    {run.repository}
                  </TableCell>
                  <TableCell>
                    {run.commit_sha ? (
                      <code className="font-mono text-2xs text-muted-foreground">
                        {run.commit_sha.slice(0, 7)}
                      </code>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
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

        <Pagination
          pagination={data.pagination}
          page={page}
          onPageChange={setPage}
          unit="runs"
        />
      </Card>
    </div>
  );
}
