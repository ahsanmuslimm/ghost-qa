import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { pipelineApi } from '../lib/api';
import type { TestCase } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Skeleton, Alert } from '../components/ui/feedback';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { formatDateTime, outcomeVariant, priorityVariant, riskVariant } from '../lib/variants';

export interface FlatTest extends TestCase {
  run_id: string;
  repository: string;
  pr_number: number | null;
}

// The backend has no global test listing, so flatten tests across the most
// recent runs (first page, newest first).
export function useAllTests() {
  return useQuery({
    queryKey: ['all-tests'],
    queryFn: async () => {
      const { data: page } = await pipelineApi.list(1, 50);
      const withTests = await Promise.all(
        page.runs.map(async (run) => {
          const { data: tests } = await pipelineApi.getTests(run.id);
          return tests.map(
            (test): FlatTest => ({
              ...test,
              run_id: run.id,
              repository: run.repository,
              pr_number: run.pr_number,
            })
          );
        })
      );
      return withTests.flat();
    },
  });
}

export function TestsListPage() {
  const { data: tests, isLoading, error } = useAllTests();

  if (isLoading) {
    return (
      <div className="space-y-4" aria-busy="true">
        <Skeleton className="h-9 w-48" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" title="Failed to load test cases">
        Could not reach the Ghost QA backend.
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Test Cases</h1>
        <span className="text-sm text-muted-foreground">{tests?.length ?? 0} generated</span>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>AI-Generated Tests</CardTitle>
        </CardHeader>
        <CardContent>
          {!tests || tests.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No test cases yet. Trigger a pipeline run to generate tests.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Run</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Risk</TableHead>
                  <TableHead>Outcome</TableHead>
                  <TableHead>Executed</TableHead>
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
                    <TableCell className="text-muted-foreground">
                      <Link to={`/runs/${test.run_id}`} className="hover:underline">
                        PR #{test.pr_number ?? test.run_id.slice(0, 8)}
                      </Link>
                    </TableCell>
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
                    <TableCell className="text-muted-foreground">{formatDateTime(test.executed_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
