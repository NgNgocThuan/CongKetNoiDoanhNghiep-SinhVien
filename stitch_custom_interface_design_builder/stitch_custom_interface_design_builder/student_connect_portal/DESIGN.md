---
name: Student Connect Portal
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#444653'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#757684'
  outline-variant: '#c4c5d5'
  surface-tint: '#3755c3'
  primary: '#00288e'
  on-primary: '#ffffff'
  primary-container: '#1e40af'
  on-primary-container: '#a8b8ff'
  inverse-primary: '#b8c4ff'
  secondary: '#006a63'
  on-secondary: '#ffffff'
  secondary-container: '#99efe5'
  on-secondary-container: '#006f67'
  tertiary: '#611e00'
  on-tertiary: '#ffffff'
  tertiary-container: '#872d00'
  on-tertiary-container: '#ffa583'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#b8c4ff'
  on-primary-fixed: '#001453'
  on-primary-fixed-variant: '#173bab'
  secondary-fixed: '#9cf2e8'
  secondary-fixed-dim: '#80d5cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#00504a'
  tertiary-fixed: '#ffdbce'
  tertiary-fixed-dim: '#ffb59a'
  on-tertiary-fixed: '#380d00'
  on-tertiary-fixed-variant: '#802a00'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display:
    fontFamily: Bricolage Grotesque
    fontSize: 3rem
    fontWeight: '700'
    lineHeight: 3.5rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Bricolage Grotesque
    fontSize: 2.25rem
    fontWeight: '700'
    lineHeight: 2.75rem
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Bricolage Grotesque
    fontSize: 1.75rem
    fontWeight: '700'
    lineHeight: 2.25rem
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Bricolage Grotesque
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Bricolage Grotesque
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: 0em
  body-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: 1.75rem
  body-md:
    fontFamily: Be Vietnam Pro
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
  body-sm:
    fontFamily: Be Vietnam Pro
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.25rem
  label-md:
    fontFamily: Be Vietnam Pro
    fontSize: 0.875rem
    fontWeight: '600'
    lineHeight: 1.25rem
  label-sm:
    fontFamily: Be Vietnam Pro
    fontSize: 0.75rem
    fontWeight: '600'
    lineHeight: 1rem
    letterSpacing: 0.025em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
---

## Brand & Style

This design system establishes a high-clarity, authoritative yet dynamic tri-stakeholder portal bridging students, corporate partners, and university administration. Balancing institutional rigor with accessible, student-first vitality, the visual narrative relies on clean administrative efficiency energized by expressive typography.

The interface evokes confidence, forward momentum, and structured transparency. Eschewing superfluous decorative gradients and disruptive animations, it adopts an editorial corporate utility style: razor-sharp information density, crisp outlines, expansive white-slate breathing room, and intentional typographic hierarchy. Every view respects the demands of three distinct user mentalities—rapid opportunity discovery for students, rigorous talent evaluation for enterprises, and high-fidelity governance for academic coordinators.

## Colors

The palette operates under a high-legibility light mode, pairing deep institution-grade blue with structured slate neutrals and balanced teal accents.

- **Primary (`#1E40AF`)**: Anchors primary interactions, navigation tabs, authoritative actions, and verified academic credentials. Interactive hover states transition to `#1D4ED8`.
- **Secondary / Accent (`#0F766E`)**: A deep, grounded teal applied to enterprise highlights, internship metrics, skill tags, and collaborative milestones.
- **Canvas & Surface Tiering**: The base canvas is grounded in slate-tinted canvas `#F8FAFC`, while functional workspaces and cards sit on pristine `#FFFFFF` surfaces bounded by `#E2E8F0` borders.
- **Semantic Feedback Tokens**:
  - *Success*: `#16A34A` text on `#DCFCE7` surface (application accepted, agreement signed).
  - *Pending / Review*: `#D97706` text on `#FEF3C7` surface (under evaluation, pending review).
  - *Critical / Error*: `#DC2626` text on `#FEE2E2` surface (rejected, deadline missed).
  - *Informational*: `#1E40AF` text on `#DBEAFE` surface (guideline notices, portal announcements).

## Typography

The typographic hierarchy pairs the charismatic structure of `Bricolage Grotesque` for titles and section anchors with the refined legibility of `Be Vietnam Pro` for administrative dense tabular screens, applicant dossiers, and Vietnamese diacritical fidelity.

- **Headlines & Section Displays**: `Bricolage Grotesque` delivers contemporary confidence to student hubs, company profile banners, and high-level analytical dashboards.
- **Body & Numerical Records**: `Be Vietnam Pro` at `14px` (`0.875rem`) and `16px` (`1rem`) handles deep descriptive copy, enterprise requirements, and audit reports without visual fatigue.
- **System Labels & Status Indicators**: High-weight labels in `Be Vietnam Pro` (600 semi-bold) preserve clarity in status badges, navigation indicators, and table header rows.

## Layout & Spacing

A strictly enforced 8-point layout rhythm governs all structural offsets, card paddings, and alignment rules.

- **Desktop (1024px and above)**: 12-column responsive fluid grid bounded by a max container width of 1440px. Gutters are locked at 24px (`1.5rem`), with 32px (`2rem`) page-level margins. Multi-column views accommodate complex tri-panel split panes (e.g., pipeline columns, student profile previews, filter sidebars).
- **Tablet (768px – 1023px)**: 8-column layout with 24px gutters. Side navigation drawers collapse to utility rails or slide-out panels.
- **Mobile (below 768px)**: 4-column layout, 16px (`1rem`) gutters and canvas margins. Data tables seamlessly transition to vertical stacked summary cards.
- **Component Flow**: Spacing between field groups and form clusters defaults to `space-md` (16px), while distinct dashboard metric widgets separate by `space-lg` (24px) to preserve hierarchy.

## Elevation & Depth

Depth is established primarily through crisp structural boundaries and soft, diffuse ambient shadows to maintain an honest, high-trust administrative atmosphere.

- **Tier 0 (Canvas)**: `#F8FAFC` flat surface for backdrops, main page containers, and secondary panel dividers.
- **Tier 1 (Surface Cards & Workspaces)**: `#FFFFFF` background bound by a 1px solid `#E2E8F0` border. Shadow: `0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.05)`.
- **Tier 2 (Elevated & Active Panels)**: Interactive cards on hover, contextual menus, and floating toolbar clusters. Border remains `#E2E8F0`. Shadow: `0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.05)`.
- **Tier 3 (Modals & Command Overlays)**: Application review sheets, approval dialogs, and flyout filters. Shadow: `0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.08)`. Backdrops employ a neutral slate tint (`rgba(15, 23, 42, 0.45)`).

## Shapes

The design system adopts a fluid pill-to-curved visual contour balance (Level 3), offsetting the strictness of institutional forms with accessible, human-centric softness.

- **Base Radius (16px / `1rem`)**: Applied to foundational content blocks, administrative cards, data visualization containers, and modal dialogs.
- **Pill Formats (9999px / Full Radius)**: Applied systematically to status indicators, category chips, interactive pills, user identity avatars, and primary quick-action buttons.
- **Inner Controls (10px–12px)**: Text inputs, form controls, and nested list items retain balanced, ergonomic corner radii (`0.625rem` to `0.75rem`) to maintain precision and focus inside larger rounded containers.

## Components

### Buttons
- **Primary**: Solid `#1E40AF` fill with white text, fully rounded pill radius, `12px 24px` padding. Transitions on hover to `#1D4ED8`. Focus state introduces a 2px offset ring in `#1E40AF`.
- **Secondary / Enterprise**: Outline style with `#E2E8F0` border, `#0F172A` text, and `#FFFFFF` background. Hover triggers background shift to `#F1F5F9`.
- **Accent (Milestone / Internship)**: Solid `#0F766E` fill, white text, pill radius for corporate recruitment workflows.

### Chips & Status Badges
- Pill-shaped with `4px 12px` padding, displaying `label-sm` typography.
- Status variants map to semantic pairs:
  - *Accepted / Validated*: `#DCFCE7` background, `#16A34A` text, with an inline 6px emerald indicator dot.
  - *Pending / Evaluation*: `#FEF3C7` background, `#D97706` text.
  - *Rejected / Inactive*: `#FEE2E2` background, `#DC2626` text.
  - *System / Info*: `#DBEAFE` background, `#1E40AF` text.

### Form Inputs & Selectors
- Background `#FFFFFF`, border `1px solid #E2E8F0`, corner radius `12px`, padding `10px 16px`. Text color `#0F172A`, placeholder color `#94A3B8`.
- Focus state: Border transforms to `#1E40AF` accompanied by a subtle `0 0 0 3px rgba(30, 64, 175, 0.12)` halo.
- Labels are positioned outside the input block at `label-md`, anchored in `#0F172A`.

### Cards & Container Panels
- Base containers feature a crisp white surface (`#FFFFFF`), `1px solid #E2E8F0` border, `16px` radius, and Level 1 elevation.
- Interactive job, project, or student application cards introduce a top-border highlight or micro-elevation shift (`translateY(-2px)`) on hover without disruptive transitions.

### Lists & Data Tables
- Table headers use uppercase `label-sm` with `#64748B` text on `#F8FAFC` background.
- Row items are separated by `1px solid #E2E8F0`, maintaining a minimum height of `56px` to ensure comfortable touch targets and scanability. Alternating row fills are avoided in favor of clean whitespace and single-row hover states (`#F8FAFC`).

### Selection Controls (Checkboxes & Radios)
- Checkboxes: `18px x 18px`, `4px` corner radius, border `1.5px solid #CBD5E1`. Checked state transitions to `#1E40AF` with a white checkmark icon.
- Radios: Circular with identical border tokens, displaying an internal `#1E40AF` pill dot upon selection.