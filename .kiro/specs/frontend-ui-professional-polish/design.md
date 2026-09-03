# Design Document

## Frontend UI Professional Polish

## Overview

This design document specifies the implementation approach for professional UI polish of the Ghost QA frontend. The existing codebase provides a solid foundation with semantic design tokens (HSL-based CSS custom properties), dark mode support, and core component structures. This improvement focuses on visual hierarchy refinements, interaction states, animations, mobile responsiveness, and data presentation enhancements to achieve a professional DevOps tool aesthetic comparable to GitHub, GitLab, and Datadog.

The design builds upon the existing Tailwind CSS infrastructure and React component architecture, extending design tokens where necessary while maintaining backward compatibility with existing implementations.

## Architecture

### Design System Architecture

The Ghost QA design system follows a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Page Layouts                              │
│  (RootLayout, Sidebar, Header, PageHeader)                  │
├─────────────────────────────────────────────────────────────┤
│                 Component Layer                              │
│  (Card, Table, Badge, Button, Input, StatCard, Pagination)  │
├─────────────────────────────────────────────────────────────┤
│              Primitive Components                            │
│  (Alert, Toast, Spinner, Skeleton, Progress)                │
├─────────────────────────────────────────────────────────────┤
│                  Design Tokens                               │
│  (CSS Custom Properties in index.css)                       │
├─────────────────────────────────────────────────────────────┤
│               Tailwind CSS Engine                            │
│  (Utility classes, custom utilities, components)            │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Styling**: Tailwind CSS v3 with custom design tokens
- **Components**: React with class-variance-authority for variant management
- **Icons**: Lucide React
- **Animations**: CSS keyframes with Tailwind animation utilities
- **Theme**: CSS custom properties with `.dark` class toggle

## Components and Interfaces

### 1. Visual Hierarchy System

#### Spacing Scale

The system extends Tailwind's default spacing with explicit 4px baseline grid alignment:

```css
/* Extended spacing scale - all values align to 4px baseline */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
```

**Usage by context:**

- **Component internal padding**: `p-3` (12px) for tight elements, `p-4` (16px) for standard
- **Flex/grid gaps**: `gap-2` (8px) for related items, `gap-4` (16px) for sections
- **Section margins**: 16px (mobile), 24px (tablet), 32px (desktop)
- **Component heights**: All align to 4px: 32px (h-8), 36px (h-9), 40px (h-10)

#### Typography Scale

The existing font stack is preserved with enhanced line-height and tracking:

```css
/* Font families - existing */
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Font sizes - existing */
--text-2xs: 0.6875rem;  /* 11px */
--text-xs: 0.75rem;     /* 12px */
--text-sm: 0.8125rem;   /* 13px */
--text-base: 0.875rem;  /* 14px */

/* Line heights */
--leading-tight: 1.25;    /* Headings */
--leading-normal: 1.5;    /* Body text */
--leading-relaxed: 1.625; /* Dense data */

/* Tracking */
--tracking-tight: -0.01em;
--tracking-normal: 0;
--tracking-wide: 0.025em;
--tracking-caps: 0.08em;  /* Small-caps labels */
```

**Typography Usage:**

| Element | Size | Weight | Line Height | Tracking |
|---------|------|--------|-------------|----------|
| Page title | text-2xl | semibold | 1.25 | -0.025em |
| Section heading | text-lg | semibold | 1.25 | -0.025em |
| Body | text-base | normal | 1.5 | normal |
| Small text | text-sm | normal | 1.5 | normal |
| Labels | text-xs | medium | normal | normal |
| Section labels | text-2xs | medium | normal | 0.08em |
| Code/ID | text-sm | normal | normal | normal |

### 2. Color System

#### Semantic Token Structure

The existing HSL-based tokens are preserved with enhanced dark mode variants:

```css
/* Light mode - existing values preserved */
:root {
  /* Surfaces */
  --background: 0 0% 100%;
  --surface: 240 20% 99%;
  --foreground: 240 10% 10%;
  
  /* Primary accent - professional blue */
  --primary: 221 83% 45%;
  --primary-foreground: 0 0% 100%;
  --primary-subtle: 221 83% 96%;
  
  /* Semantic status */
  --success: 152 62% 32%;
  --warning: 32 95% 38%;
  --danger: 356 72% 44%;
  --info: 221 83% 45%;
}

/* Dark mode - enhanced values */
.dark {
  /* Elevated surfaces for dark mode */
  --background: 240 8% 7%;
  --surface: 240 8% 9%;
  --card: 240 8% 10%;  /* Slightly lighter than background */
  --foreground: 240 5% 93%;
  
  /* Reduced contrast for eye comfort */
  --foreground: 240 5% 85%;  /* 85% instead of 93% */
  
  /* Dimmed borders */
  --border: 240 6% 17%;
  --border-strong: 240 5% 22%;  /* Subtle, not prominent */
}
```

#### Color Contrast Requirements

- **Normal text**: Minimum 4.5:1 contrast ratio
- **Large text** (14px+ bold or 18px+ normal): Minimum 3:1
- **Interactive elements**: 3:1 against adjacent background
- **Status indicators**: Semantic colors maintain visibility in both themes

### 3. Interaction States

#### Button States (Requirements 4.1-4.4)

```typescript
// button.tsx variants - existing with refinements
const buttonVariants = cva(
  [
    // Base styles
    'inline-flex items-center justify-center gap-1.5 rounded-md',
    'text-sm font-medium transition-all duration-150',
    
    // Focus - enhanced ring
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
    'focus-visible:ring-offset-2 focus-visible:ring-offset-background',
    
    // Disabled
    'disabled:pointer-events-none disabled:opacity-50',
    
    // Active - subtle press effect
    'active:translate-y-px active:shadow-none',
  ],
  {
    variants: {
      variant: {
        default: [
          'bg-primary text-primary-foreground',
          'hover:bg-primary/90',  // 10% darken
          'active:bg-primary/95',
        ].join(' '),
        // ... other variants
      },
      size: {
        default: 'h-8 px-3 py-1.5',     // 32px height
        sm: 'h-7 px-2.5 text-xs',       // 28px height
        lg: 'h-10 px-5 text-base',      // 40px height
        icon: 'h-8 w-8',                // 32px touch target
        'icon-sm': 'h-7 w-7',           // 28px touch target
      },
    },
  }
);
```

#### Input States (Requirement 4.5)

```typescript
// input.tsx refinements
const inputVariants = cva(
  [
    'flex h-8 w-full rounded-md border border-input bg-background px-3 py-1',
    'text-sm shadow-sm transition-colors duration-150',
    'placeholder:text-muted-foreground',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
    'disabled:cursor-not-allowed disabled:opacity-50',
  ].join(' '),
  {
    variants: {
      error: {
        true: 'border-danger ring-1 ring-danger',
        false: '',
      },
    },
  }
);
```

#### Touch Targets (Requirement 4.7)

- **Minimum touch target**: 32x32px on desktop, 44x44px on mobile
- **Button sizes**: `h-8 w-8` (32px) desktop, `h-11 w-11` (44px) mobile
- **Spacing between touch targets**: Minimum 8px

### 4. Dark Mode Implementation

#### Elevated Surfaces (Requirement 5.2)

Dark mode uses layered elevation:

```css
.dark {
  /* Layer 0 - Background */
  --background: 240 8% 7%;
  
  /* Layer 1 - Surface (slightly elevated) */
  --surface: 240 8% 9%;
  
  /* Layer 2 - Cards (more elevated) */
  --card: 240 8% 10%;
  --popover: 240 8% 12%;
  
  /* Layer 3 - Modals (most elevated) */
  --modal: 240 8% 14%;
}
```

#### Reduced Contrast (Requirement 5.3)

Dark mode text hierarchy:

```css
.dark {
  /* Primary text - reduced from 93% to 85% */
  --foreground: 240 5% 85%;
  
  /* Secondary text - reduced */
  --muted-foreground: 240 5% 62%;
  
  /* Tertiary - more subtle */
  --accent-foreground: 240 5% 70%;
}
```

#### Theme Persistence (Requirement 5.6)

The theme preference is stored in localStorage:

```typescript
// Theme toggle implementation
const getThemePreference = (): 'light' | 'dark' | 'system' => {
  const stored = localStorage.getItem('theme');
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored;
  }
  return 'system';
};

const setThemePreference = (theme: 'light' | 'dark' | 'system') => {
  localStorage.setItem('theme', theme);
  applyTheme(theme);
};
```

### 5. Mobile Responsiveness

#### Breakpoint System (Requirement 6.1)

```css
/* Mobile-first breakpoints */
--breakpoint-sm: 40rem;   /* 640px */
--breakpoint-md: 48rem;   /* 768px */
--breakpoint-lg: 64rem;   /* 1024px */
--breakpoint-xl: 80rem;   /* 1280px */
```

#### Responsive Layout Behavior

| Component | Desktop (≥768px) | Mobile (<768px) |
|-----------|------------------|-----------------|
| Sidebar | Fixed 236px / 60px collapsed | Off-canvas drawer |
| Header | Full navigation | Hamburger menu |
| Tables | Full width | Horizontal scroll + sticky first column |
| Cards/StatCards | Grid layout | Single column stack |
| Pagination | Full controls | Prev/Next only |
| Buttons | 32px height | 44px height |

#### Sidebar Mobile Behavior

```typescript
// SidebarDrawer component for mobile
interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

// Mobile: Off-canvas drawer with overlay
// Desktop: Fixed sidebar with collapse toggle

// Collapse behavior
const SIDEBAR_WIDTH = {
  expanded: 236,  // px
  collapsed: 60,  // px
};
```

#### Table Mobile Behavior

```typescript
// Table responsive wrapper
interface TableResponsiveProps {
  stickyFirstColumn?: boolean;
}

// Implementation: horizontal scroll container
// First column: position: sticky; left: 0;
```

### 6. Animation System

#### Animation Utilities (Requirement 7.1-7.3)

The existing animations are preserved:

```css
/* index.css additions */

@keyframes fade-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slide-in-right {
  from { opacity: 0; transform: translateX(100%); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes pulse-soft {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Duration utilities */
.duration-150 { transition-duration: 150ms; }
.duration-180 { animation-duration: 180ms; }
.duration-200 { transition-duration: 200ms; }
.duration-300 { transition-duration: 300ms; }
```

#### Reduced Motion Support (Requirement 7.7)

The existing reduced motion support is preserved:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

#### Component Animation Specifications

| Animation | Duration | Easing | Trigger |
|-----------|----------|--------|---------|
| Fade-in | 180ms | ease-out | Element mount |
| Button hover | 150ms | ease | Hover state |
| Focus ring | 150ms | ease | Focus state |
| Sidebar collapse | 200ms | ease-in-out | Toggle |
| Toast enter | 200ms | ease-out | Show |
| Toast exit | 150ms | ease-in | Hide |
| Modal open | 200ms | ease-out | Open |

### 7. Component Specifications

#### 7.1 Sidebar (Requirement 11)

```typescript
interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  className?: string;
}

// Widths
const SIDEBAR_CONFIG = {
  expanded: 236,  // px
  collapsed: 60,  // px
  mobile: '100%', // Full width drawer
};

// Features:
// - Brand mark at top (logo + "Ghost QA")
// - Navigation items with icons
// - Active page indicator (left accent bar)
// - Section titles with label-caps
// - Collapse/expand toggle (desktop only)
// - Mobile: drawer with backdrop overlay
```

#### 7.2 Header (Requirement 12)

```typescript
interface HeaderProps {
  onMenuClick?: () => void;  // Mobile hamburger
  className?: string;
}

// Features:
// - Sticky position with backdrop-blur
// - ThemeMenu (light/dark/system)
// - User avatar (initials circle) + email
// - Dropdown menu with sign-out
// - Current time (24-hour format)
// - Hamburger menu (mobile only)
```

#### 7.3 RootLayout (Requirement 13)

```typescript
interface RootLayoutProps {
  children: ReactNode;
  sidebar?: ReactNode;
  header?: ReactNode;
}

// Features:
// - Combines Header + Sidebar + main
// - ErrorBoundary wrapper
// - Main padding: p-6 (24px) mobile, p-8 (32px) desktop
// - Responsive layout handling
// - Scroll position preservation
```

#### 7.4 Cards (Requirement 15)

```typescript
// Existing Card component structure preserved
// Refinements:
// - CardTitle: font-semibold, tracking-tight
// - CardDescription: text-muted-foreground
// - CardContent: p-4 padding
// - CardFooter: border-t separator
```

#### 7.5 Tables (Requirement 14)

```typescript
// Table refinements:
// - TableHead: uppercase, label-caps, muted-foreground
// - TableRow: hover:bg-muted/60
// - TableCell: px-3 py-2.5, tabular-nums for numbers
// - Optional sticky header
// - Optional alternating row backgrounds
```

#### 7.6 StatCards (Requirement 17)

```typescript
// Existing component structure preserved
// Refinements:
// - Label: label-caps (small-caps)
// - Value: text-2xl, tabular-nums, tone-specific color
// - Accent: 2px left border with tone color
// - Optional caption and icon
// - Optional href for clickable
```

#### 7.7 Badges (Requirement 16)

```typescript
// Existing Badge component structure preserved
// Refinements:
// - Size: text-2xs (11px)
// - Dot indicator support
// - Pulse animation for in-progress
// - Semantic color variants
```

#### 7.8 Pagination (Requirement 18)

```typescript
interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

// Features:
// - Current/total display
// - Previous/Next buttons
// - Numbered links with ellipsis
// - Disabled states at boundaries
// - Mobile: prev/next only
```

#### 7.9 PageHeader (Requirement 19)

```typescript
interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  meta?: MetaItem[];
  actions?: ReactNode;
  className?: string;
}

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface MetaItem {
  label: string;
  value: string | number;
}
```

#### 7.10 Brand (Requirement 20)

```typescript
interface BrandProps {
  collapsed?: boolean;  // Show simplified mark when collapsed
  className?: string;
}

// Features:
// - Full: Logo + "Ghost QA" + subtitle
// - Collapsed: Logo mark only (BrandMark)
// - Works in both themes
```

### 8. Form Components

#### 8.1 Input (Requirement 21)

```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  className?: string;
}

// Features:
// - Height: h-8 (32px)
// - Padding: px-3
// - Placeholder: muted-foreground
// - Focus: ring-2 ring-ring
// - Error: border-danger, ring-danger
// - Disabled: reduced opacity, no pointer events
```

#### 8.2 Select (Requirement 22)

```typescript
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  className?: string;
}

// Matches Input styling
// Custom chevron icon
// Native accessibility
```

#### 8.3 Label (Requirement 23)

```typescript
interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  className?: string;
}

// Size: text-xs (12px)
// Weight: font-medium
// Peer focus: peer-focus:text-primary
// Peer disabled: peer-disabled:opacity-50
```

#### 8.4 Button (Requirement 24)

```typescript
// Existing buttonVariants preserved
// All interaction states already implemented
```

### 9. Feedback Components

#### 9.1 Alerts (Requirement 25)

```typescript
interface AlertProps {
  variant?: 'default' | 'info' | 'success' | 'warning' | 'destructive';
  title?: string;
  description?: string;
  className?: string;
}

// Features:
// - Appropriate icon per variant
// - Semantic color scheme
// - ARIA role: alert (errors/warnings), status (others)
```

#### 9.2 Toasts (Requirement 26)

```typescript
interface ToastProps {
  id: string;
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  description?: string;
  action?: ReactNode;
  duration?: number;  // default 5000ms
  onDismiss: () => void;
}

// Features:
// - Top-right position
// - Auto-dismiss
// - Action button support
// - Slide + fade animation
// - Close button
// - Stack multiple toasts
```

#### 9.3 Spinners (Requirement 27)

```typescript
interface SpinnerProps {
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}

// Features:
// - Circular rotate animation
// - Primary color for spinning portion
// - aria-label for accessibility
// - Sizes: sm (16px), default (24px), lg (32px)
```

#### 9.4 Skeletons (Requirement 28)

```typescript
interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
}

// Features:
// - Pulse animation
// - Muted background
// - Custom dimensions via className
// - Match content shape
```

#### 9.5 Progress (Requirement 29)

```typescript
interface ProgressProps {
  value: number;  // 0-100
  max?: number;
  className?: string;
}

// Features:
// - Determinate bar
// - Primary color fill
// - Custom height support
// - ARIA attributes
```

### 10. Empty and Error States

#### Empty States (Requirement 9)

```typescript
interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

// Features:
// - Centered layout
// - Muted colors (not prominent)
// - Optional icon, title, description, action
```

#### Error Handling (Requirement 10)

- Alert with destructive variant for errors
- AlertCircle icon
- FieldError component for form validation
- Input error border (danger color)
- Toast for transient errors

## Data Models

### Design Token Structure

```typescript
interface DesignTokens {
  colors: {
    background: string;
    surface: string;
    foreground: string;
    primary: string;
    primaryForeground: string;
    secondary: string;
    secondaryForeground: string;
    muted: string;
    mutedForeground: string;
    accent: string;
    accentForeground: string;
    border: string;
    borderStrong: string;
    input: string;
    ring: string;
    success: string;
    warning: string;
    danger: string;
    info: string;
  };
  spacing: {
    1: string;
    2: string;
    3: string;
    4: string;
    // ... through 12
  };
  typography: {
    fontSans: string;
    fontMono: string;
    text2xs: string;
    textXs: string;
    textSm: string;
    textBase: string;
  };
  shadows: {
    sm: string;
    md: string;
  };
  radius: string;
}
```

### Component Prop Types

All component prop types follow the existing patterns with TypeScript interfaces exported from each component file.

## Error Handling

### Error Boundary

The RootLayout includes an ErrorBoundary wrapping all content:

```typescript
// ErrorBoundary component already exists at:
// frontend/src/components/common/ErrorBoundary.tsx
```

### Form Validation

- Use existing FieldError component for inline validation messages
- Input shows error border and ring when `aria-invalid="true"`
- Error messages linked via `aria-describedby`

### Toast Notifications

Transient errors display as toast notifications:
- Duration: 5 seconds default
- Auto-dismiss
- Action button for retry when appropriate

## Testing Strategy

### Testing Approach

This is a UI styling and interaction refinement project. Property-based testing is NOT appropriate for this feature because:

1. **UI Rendering Focus**: The changes primarily affect visual presentation, CSS styling, and interaction states—not logic or data transformations
2. **No Pure Functions**: There are no functions with predictable input/output behavior to test
3. **Visual Verification**: Correctness is determined by visual inspection rather than automated assertions
4. **Existing Foundation**: The codebase already has a solid foundation with semantic design tokens

### Recommended Testing Methods

#### Snapshot Testing
- Capture component renders and compare against baseline
- Useful for detecting unintended style changes
- Tools: Vitest with `@vitest/ui` or Jest snapshots

#### Integration Testing
- Test component interactions (e.g., sidebar toggle, theme switching)
- Verify responsive behavior at different breakpoints
- Tools: Playwright or Cypress

#### Manual Testing Checklist
- [ ] Visual verification against design specifications
- [ ] Responsive behavior at all breakpoints
- [ ] Dark mode appearance and contrast
- [ ] Keyboard navigation and focus states
- [ ] Reduced motion preference
- [ ] Screen reader navigation
- [ ] Touch target sizes on mobile

### Accessibility Testing
- Automated: axe-core, eslint-plugin-jsx-a11y
- Manual: Keyboard-only navigation, screen reader testing
- Tools: NVDA, VoiceOver, axe DevTools

### Performance Considerations
- CSS custom properties are performant (no runtime overhead)
- Animations use CSS transforms (GPU accelerated)
- Reduced motion media query prevents unnecessary animations

## Implementation Notes

### Backward Compatibility

All existing components preserve their public APIs. Changes are additive:
- New CSS classes added without removing existing ones
- Variant options extend, not replace
- No breaking changes to existing prop types

### Gradual Implementation

The design can be implemented incrementally by component category:
1. Design tokens (CSS additions)
2. Core interaction states (Button, Input)
3. Layout components (Sidebar, Header)
4. Data display components (Table, Card, StatCard)
5. Feedback components (Toast, Alert)
6. Mobile responsiveness
7. Accessibility refinements

### Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge - latest 2 versions)
- CSS custom properties require approximately IE11+
- For IE11, consider postcss-custom-properties fallback

## References

- Existing design tokens: `frontend/src/index.css`
- Existing components: `frontend/src/components/ui/`
- Common components: `frontend/src/components/common/`
- Tailwind CSS: https://tailwindcss.com/docs
- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- Reduced Motion: https://web.dev/prefers-reduced-motion/