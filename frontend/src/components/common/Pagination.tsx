import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '../ui/button';

export interface PaginationInfo {
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

/** Table footer pager: range label + prev/next. Matches the backend page shape. */
export function Pagination({
  pagination,
  page,
  onPageChange,
  unit = 'records',
}: {
  pagination: PaginationInfo;
  page: number;
  onPageChange: (page: number) => void;
  unit?: string;
}) {
  const { total, page_size } = pagination;
  if (total === 0) return null;

  const from = (page - 1) * page_size + 1;
  const to = Math.min(page * page_size, total);

  return (
    <div className="flex items-center justify-between gap-3 border-t border-border px-4 py-2.5">
      <p className="numeric text-2xs text-muted-foreground">
        {from}–{to} of {total} {unit}
      </p>
      <div className="flex items-center gap-1.5">
        <Button
          variant="outline"
          size="icon-sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
        </Button>
        <span className="numeric min-w-[52px] text-center text-2xs text-muted-foreground">
          {page} / {Math.max(1, Math.ceil(total / page_size))}
        </span>
        <Button
          variant="outline"
          size="icon-sm"
          disabled={!pagination.has_next}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        >
          <ChevronRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
