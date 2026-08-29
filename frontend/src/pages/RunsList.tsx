import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { pipelineApi } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Skeleton, Alert } from '../components/ui/feedback';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { formatDateTime, riskVariant, statusVariant } from '../lib/variants';

export function RunsListPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ['runs', page],
    queryFn: () => pipelineApi.list(page).then((res) => res.data),
  });

  if (isLoading) {
    return (
      <div className="space-y-4" aria-busy="true">
        <Skeleton className="h-9 w-56" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" title="Failed to load pipeline runs">
        Could not reach the Ghost QA backend.
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Pipeline Runs</h1>
        {data && <span className="text-sm text-muted-foreground">{data.pagination.total} total</span>}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Runs</CardTitle>
        </CardHeader>
        <CardContent>
          {data && data.runs.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No pipeline runs yet. Push a PR to a connected repository to trigger one.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run</TableHead>
                  <TableHead>Repository</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Risk</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.runs.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell>
                      <Link to={`/runs/${run.id}`} className="font-mono text-primary hover:underline">
                        #{run.pr_number ?? run.id.slice(0, 8)}
                      </Link>
                    </TableCell>
                    <TableCell>{run.repository}</TableCell>
                    <TableCell>
                      <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={riskVariant(run.risk_level)}>{run.risk_level || 'pending'}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDateTime(run.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {data && data.pagination.total > data.pagination.page_size && (
            <div className="mt-4 flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                aria-label="Previous page"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground">Page {data.pagination.page}</span>
              <Button
                variant="outline"
                size="sm"
                disabled={!data.pagination.has_next}
                onClick={() => setPage((p) => p + 1)}
                aria-label="Next page"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
