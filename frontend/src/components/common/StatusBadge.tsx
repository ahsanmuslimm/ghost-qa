import { Badge } from '../ui/badge';
import {
  humanize,
  humanizePriority,
  isActiveStatus,
  outcomeVariant,
  priorityVariant,
  riskVariant,
  statusVariant,
} from '../../lib/variants';

/**
 * One badge component per backend enum so tone, dot and label casing stay
 * consistent across every table and detail view.
 */
export function StatusBadge({
  status,
  className,
}: {
  status: string | null | undefined;
  className?: string;
}) {
  return (
    <Badge
      variant={statusVariant(status)}
      dot
      pulse={isActiveStatus(status)}
      className={className}
    >
      {humanize(status, 'Unknown')}
    </Badge>
  );
}

export function RiskBadge({
  level,
  className,
}: {
  level: string | null | undefined;
  className?: string;
}) {
  if (!level) {
    return <Badge variant="outline" className={className}>Unassessed</Badge>;
  }
  return (
    <Badge variant={riskVariant(level)} dot className={className}>
      {humanize(level)}
    </Badge>
  );
}

export function OutcomeBadge({
  outcome,
  className,
}: {
  outcome: string | null | undefined;
  className?: string;
}) {
  return (
    <Badge variant={outcomeVariant(outcome)} dot className={className}>
      {humanize(outcome, 'Pending')}
    </Badge>
  );
}

export function PriorityBadge({
  priority,
  className,
}: {
  priority: string | null | undefined;
  className?: string;
}) {
  return (
    <Badge variant={priorityVariant(priority)} className={className}>
      {humanizePriority(priority)}
    </Badge>
  );
}
