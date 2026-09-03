import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  /** When true the desktop sidebar renders as a 60px icon rail. */
  isSidebarCollapsed: boolean;
  toggleSidebarCollapsed: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      isSidebarCollapsed: false,
      toggleSidebarCollapsed: () =>
        set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ isSidebarCollapsed: collapsed }),
    }),
    {
      name: 'ghost-qa-ui',
      partialize: (state) => ({ isSidebarCollapsed: state.isSidebarCollapsed }),
    }
  )
);
