# Implementation Plan: Frontend UI Professional Polish

## Overview

This implementation plan focuses on polishing the Ghost QA frontend to achieve a professional DevOps tool aesthetic. The tasks build upon the existing solid foundation with semantic design tokens and React components. Implementation follows a systematic approach: design tokens first, then core interactive components, then layout components, then pages, and finally verification.

## Tasks

- [ ] 1. Update design system tokens in index.css
  - [ ] 1.1 Refine spacing scale with 4px baseline grid alignment
    - Add explicit spacing custom properties: --space-1 through --space-12
    - Ensure all existing components use consistent spacing values
    - _Requirements: 1.1, 1.2, 1.4, 1.5_
  
  - [ ] 1.2 Enhance shadow system
    - Add refined shadow values (shadow-sm, shadow-md, shadow-lg)
    - Ensure proper elevation hierarchy
    - _Requirements: 4.1, 4.3_
  
  - [ ] 1.3 Enhance dark mode colors
    - Adjust elevated surface colors for dark mode (--card, --popover, --modal)
    - Reduce text contrast (85% instead of 93% for foreground)
    - Add dimmed border colors for dark mode
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ] 1.4 Add animation utilities
    - Add fade-in, slide-in-right, pulse-soft keyframes
    - Add duration utilities (duration-150, duration-180, duration-200)
    - _Requirements: 7.1, 7.2, 7.3_

- [ ] 2. Enhance Button component with interaction states
  - [ ] 2.1 Add hover state refinements
    - Darken background by 10% with 150ms transition
    - _Requirements: 4.1_
  
  - [ ] 2.2 Add focus ring refinements
    - Show 2px ring with ring color and 2px offset
    - Add ring-offset for proper contrast
    - _Requirements: 4.2, 4.6_
  
  - [ ] 2.3 Add active/pressed state
    - Implement translate-y-px on active
    - _Requirements: 4.3_
  
  - [ ] 2.4 Refine button variants
    - Ensure all variants (default, secondary, outline, ghost, destructive, link) have consistent styling
    - _Requirements: 24.1, 24.2_

- [ ] 3. Enhance Input component
  - [ ] 3.1 Refine focus ring
    - Add ring-2 with proper ring-offset-1
    - _Requirements: 4.5, 4.6_
  
  - [ ] 3.2 Add error states
    - Add danger border color when error=true
    - Add ring-1 ring-danger for error state
    - _Requirements: 10.4_
  
  - [ ] 3.3 Refine placeholder styling
    - Ensure placeholder uses muted-foreground color
    - _Requirements: 21.2_
  
  - [ ] 3.4 Add disabled state
    - Ensure opacity-50 and pointer-events-none on disabled
    - _Requirements: 4.4, 21.5_

- [ ] 4. Enhance Card component
  - [ ] 4.1 Improve visual hierarchy
    - Refine CardTitle with semibold font and tight tracking
    - Add CardDescription with muted-foreground color
    - _Requirements: 15.3, 15.4_
  
  - [ ] 4.2 Refine shadows and borders
    - Ensure consistent border, shadow, rounded corners
    - Add proper elevation shadows
    - _Requirements: 15.2_
  
  - [ ] 4.3 Refine padding and layout
    - Ensure CardContent uses p-4 (16px)
    - Add top border separator to CardFooter
    - _Requirements: 15.5, 15.6_

- [ ] 5. Enhance Table component
  - [ ] 5.1 Add row hover states
    - Implement hover:bg-muted/60 on TableRow
    - _Requirements: 14.3_
  
  - [ ] 5.2 Refine header styling
    - Add uppercase text with tracking-caps
    - Use muted-foreground color
    - _Requirements: 14.2_
  
  - [ ] 5.3 Refine cell typography and spacing
    - Use consistent padding (px-3 py-2.5)
    - Add tabular-nums for numeric data
    - _Requirements: 14.4, 14.7_
  
  - [ ] 5.4 Add optional features
    - Add sticky header support
    - Add alternating row backgrounds variant
    - _Requirements: 14.5, 14.6_

- [ ] 6. Enhance Badge and StatusBadge components
  - [ ] 6.1 Add status indicator dots
    - Add dot indicator for status visualization
    - _Requirements: 16.2_
  
  - [ ] 6.2 Add pulse animation
    - Implement pulse animation for in-progress states
    - _Requirements: 16.3_
  
  - [ ] 6.3 Refine styling
    - Ensure semantic color variants work correctly
    - Use text-2xs size (11px)
    - _Requirements: 16.1, 16.4, 16.5_

- [ ] 7. Enhance StatCard component
  - [ ] 7.1 Add accent bar
    - Add 2px tone-specific color bar on left edge
    - _Requirements: 17.4_
  
  - [ ] 7.2 Refine layout
    - Add label-caps for label styling
    - Add tabular-nums for value display
    - Add text-2xl for large numeric value
    - _Requirements: 17.1, 17.2, 17.6_
  
  - [ ] 7.3 Add optional features
    - Add optional caption and icon support
    - Add optional href for clickable cards
    - _Requirements: 17.3, 17.5_

- [ ] 8. Enhance Alert component
  - [ ] 8.1 Add variant support
    - Implement variants: default, info, success, warning, destructive
    - _Requirements: 25.1_
  
  - [ ] 8.2 Add icons
    - Add appropriate icons per variant (AlertCircle, CheckCircle, Info, etc.)
    - _Requirements: 25.2_
  
  - [ ] 8.3 Refine styling
    - Use semantic color scheme per variant
    - Add proper ARIA roles (alert for errors/warnings)
    - _Requirements: 25.3, 25.4, 25.5_

- [ ] 9. Enhance Skeleton component
  - [ ] 9.1 Refine animations
    - Ensure pulse animation is smooth
    - Use muted background colors
    - _Requirements: 28.1, 28.2_
  
  - [ ] 9.2 Add variant support
    - Support variants: text, circular, rectangular
    - Accept custom dimensions via className
    - _Requirements: 28.3, 28.4_

- [ ] 10. Enhance Sidebar component
  - [ ] 10.1 Add collapse animation
    - Implement smooth width transition (200ms ease-in-out)
    - Add collapse/expand toggle functionality
    - _Requirements: 7.5, 11.7_
  
  - [ ] 10.2 Add active state
    - Highlight currently active page with left accent bar
    - _Requirements: 11.4_
  
  - [ ] 10.3 Refine styling
    - Ensure fixed width: 236px expanded, 60px collapsed
    - Add brand mark at top
    - Add section titles with label-caps
    - _Requirements: 11.1, 11.5, 11.6_
  
  - [ ] 10.4 Add mobile drawer behavior
    - Implement off-canvas drawer with overlay on mobile (<768px)
    - _Requirements: 6.2, 11.2_

- [ ] 11. Enhance Header component
  - [ ] 11.1 Add sticky behavior
    - Make header sticky at top with backdrop-blur
    - _Requirements: 12.1_
  
  - [ ] 11.2 Refine user menu
    - Add user avatar (initials circle) and email display
    - Add dropdown menu with sign-out option
    - _Requirements: 12.3, 12.4_
  
  - [ ] 11.3 Add time display
    - Show current time in 24-hour format
    - _Requirements: 12.5_
  
  - [ ] 11.4 Add mobile menu
    - Add hamburger menu for mobile
    - _Requirements: 12.6, 6.3_

- [ ] 12. Enhance Login page
  - [ ] 12.1 Refine form styling
    - Polish Input and Button component integration
    - Ensure consistent spacing and alignment
    - _Requirements: 21.1, 21.2, 21.3, 21.4_
  
  - [ ] 12.2 Add visual polish
    - Center form with proper card styling
    - Add branding elements
    - Ensure responsive behavior
    - _Requirements: 6.1, 20.1_

- [ ] 13. Enhance Dashboard page
  - [ ] 13.1 Polish StatCards
    - Apply all StatCard enhancements
    - Ensure proper grid layout
    - _Requirements: 17.1, 17.2, 17.3, 17.4_
  
  - [ ] 13.2 Refine page layout
    - Apply proper PageHeader styling
    - Ensure consistent spacing and typography
    - _Requirements: 19.1, 19.2, 19.3, 19.6_
  
  - [ ] 13.3 Add responsive behavior
    - Ensure cards stack on mobile
    - Add proper padding at all breakpoints
    - _Requirements: 6.5_

- [ ] 14. Enhance RunsList page
  - [ ] 14.1 Polish table styling
    - Apply all Table component enhancements
    - Ensure proper header and row styling
    - _Requirements: 14.1, 14.2, 14.3, 14.4_
  
  - [ ] 14.2 Refine filters
    - Style filter inputs consistently
    - Add proper spacing between filter elements
    - _Requirements: 21.1, 21.2_
  
  - [ ] 14.3 Add mobile responsiveness
    - Enable horizontal scroll with sticky first column
    - Ensure pagination adapts to mobile
    - _Requirements: 6.4, 6.6_

- [ ] 15. Checkpoint - Verify build and fix errors
  - [ ] 15.1 Run vite build
    - Execute: `cd frontend && npm run build`
    - Verify no build errors
    - _Requirements: All_
  
  - [ ] 15.2 Fix TypeScript errors
    - Review and fix any type errors
    - Ensure proper prop types
    - _Requirements: All_
  
  - [ ] 15.3 Fix CSS issues
    - Review and fix any styling conflicts
    - Ensure design tokens apply correctly
    - _Requirements: All_

## Notes

- Tasks follow a logical implementation order: tokens → components → layout → pages → verification
- Each task builds on previous implementations
- Checkpoint at task 15 ensures build succeeds before completion
- Design tokens in index.css must be updated first as other components depend on them
- Mobile responsiveness is tested throughout (not just at end)
- All interaction states should be verified manually after implementation