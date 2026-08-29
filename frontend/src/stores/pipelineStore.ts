import { create } from 'zustand';
import type { PipelineRunSummary } from '../types';

interface PipelineState {
  runs: PipelineRunSummary[];
  currentRun: PipelineRunSummary | null;
  isLoading: boolean;
  error: string | null;
  setRuns: (runs: PipelineRunSummary[]) => void;
  setCurrentRun: (run: PipelineRunSummary | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  addRun: (run: PipelineRunSummary) => void;
  updateRun: (id: string, updates: Partial<PipelineRunSummary>) => void;
}

export const usePipelineStore = create<PipelineState>((set) => ({
  runs: [],
  currentRun: null,
  isLoading: false,
  error: null,
  setRuns: (runs) => set({ runs, isLoading: false }),
  setCurrentRun: (run) => set({ currentRun: run }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  addRun: (run) => set((state) => ({ runs: [run, ...state.runs] })),
  updateRun: (id, updates) =>
    set((state) => ({
      runs: state.runs.map((run) => (run.id === id ? { ...run, ...updates } : run)),
    })),
}));
