import { useEffect, useState } from 'react';
import { useThemeStore } from '../stores/themeStore';

/**
 * Recharts needs literal colour strings, not Tailwind classes, so the palette
 * is read from the design tokens at runtime. This keeps charts in sync with
 * the active theme instead of hardcoding neon hex values.
 */
export interface ChartTheme {
  series: string[];
  grid: string;
  axis: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipText: string;
  success: string;
  warning: string;
  danger: string;
  info: string;
  muted: string;
}

function token(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return raw ? `hsl(${raw})` : fallback;
}

export function readChartTheme(): ChartTheme {
  return {
    series: [
      token('--chart-1', 'hsl(221 83% 45%)'),
      token('--chart-2', 'hsl(190 70% 38%)'),
      token('--chart-3', 'hsl(262 60% 55%)'),
      token('--chart-4', 'hsl(32 95% 44%)'),
      token('--chart-5', 'hsl(152 62% 32%)'),
    ],
    grid: token('--border', 'hsl(240 6% 90%)'),
    axis: token('--muted-foreground', 'hsl(240 4% 46%)'),
    tooltipBg: token('--popover', 'hsl(0 0% 100%)'),
    tooltipBorder: token('--border', 'hsl(240 6% 90%)'),
    tooltipText: token('--popover-foreground', 'hsl(240 10% 10%)'),
    success: token('--success', 'hsl(152 62% 32%)'),
    warning: token('--warning', 'hsl(32 95% 38%)'),
    danger: token('--danger', 'hsl(356 72% 44%)'),
    info: token('--info', 'hsl(221 83% 45%)'),
    muted: token('--muted-foreground', 'hsl(240 4% 46%)'),
  };
}

/** Re-reads the palette whenever the theme or the OS preference changes. */
export function useChartTheme(): ChartTheme {
  const theme = useThemeStore((s) => s.theme);
  const [palette, setPalette] = useState<ChartTheme>(() => readChartTheme());

  useEffect(() => {
    // Tokens are applied to <html> before this effect runs.
    setPalette(readChartTheme());
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => theme === 'system' && setPalette(readChartTheme());
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, [theme]);

  return palette;
}

/** Risk level → semantic token colour, for stacked bars and legend swatches. */
export function riskColor(level: string | null | undefined, palette: ChartTheme): string {
  switch (level) {
    case 'low':
      return palette.success;
    case 'medium':
      return palette.warning;
    case 'high':
      return palette.danger;
    case 'critical':
      return palette.danger;
    default:
      return palette.muted;
  }
}

/** Outcome → semantic token colour. */
export function outcomeColor(outcome: string | null | undefined, palette: ChartTheme): string {
  switch (outcome) {
    case 'passed':
      return palette.success;
    case 'failed':
    case 'error':
      return palette.danger;
    case 'skipped':
    case 'timed_out':
      return palette.warning;
    default:
      return palette.muted;
  }
}

/** Pipeline status → semantic token colour. */
export function statusColor(status: string | null | undefined, palette: ChartTheme): string {
  switch (status) {
    case 'completed':
      return palette.success;
    case 'failed':
      return palette.danger;
    case 'awaiting_approval':
      return palette.warning;
    case 'running':
    case 'approved':
      return palette.info;
    default:
      return palette.muted;
  }
}

/** Shared axis/tooltip props so every chart reads identically. */
export const axisTick = (palette: ChartTheme) => ({
  fill: palette.axis,
  fontSize: 11,
  fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
});

export const tooltipStyle = (palette: ChartTheme) => ({
  contentStyle: {
    backgroundColor: palette.tooltipBg,
    border: `1px solid ${palette.tooltipBorder}`,
    borderRadius: 6,
    boxShadow: '0 1px 3px 0 rgb(16 24 40 / 0.08)',
    fontSize: 12,
    padding: '6px 10px',
    color: palette.tooltipText,
  },
  labelStyle: {
    color: palette.tooltipText,
    fontSize: 11,
    fontWeight: 600,
    marginBottom: 2,
  },
  itemStyle: { color: palette.tooltipText, fontSize: 11, padding: 0 },
  cursor: { fill: palette.grid, opacity: 0.35 },
});
