---
name: Crimson Intelligence
colors:
  surface: '#1d1011'
  surface-dim: '#1d1011'
  surface-bright: '#463536'
  surface-container-lowest: '#170b0c'
  surface-container-low: '#261819'
  surface-container: '#2a1c1d'
  surface-container-high: '#352627'
  surface-container-highest: '#413132'
  on-surface: '#f6dcdd'
  on-surface-variant: '#e1bec0'
  inverse-surface: '#f6dcdd'
  inverse-on-surface: '#3c2c2d'
  outline: '#a8898b'
  outline-variant: '#594042'
  surface-tint: '#ffb2b9'
  primary: '#ffb2b9'
  on-primary: '#67001e'
  primary-container: '#ae1c3f'
  on-primary-container: '#ffc2c7'
  inverse-primary: '#b42243'
  secondary: '#bcc7de'
  on-secondary: '#263143'
  secondary-container: '#3e495d'
  on-secondary-container: '#aeb9d0'
  tertiary: '#b7c8e1'
  on-tertiary: '#213145'
  tertiary-container: '#4b5b71'
  on-tertiary-container: '#c2d3ed'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdadc'
  primary-fixed-dim: '#ffb2b9'
  on-primary-fixed: '#40000f'
  on-primary-fixed-variant: '#91002e'
  secondary-fixed: '#d8e3fb'
  secondary-fixed-dim: '#bcc7de'
  on-secondary-fixed: '#111c2d'
  on-secondary-fixed-variant: '#3c475a'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#1d1011'
  on-background: '#f6dcdd'
  surface-variant: '#413132'
typography:
  display-sm:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-agent:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-main:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-data:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  sidebar-width: 260px
  chat-max-width: 900px
  gutter: 1rem
  stack-xs: 0.25rem
  stack-sm: 0.5rem
  stack-md: 1rem
  inset-compact: 0.75rem
  inset-standard: 1rem
---

## Brand & Style
The design system is engineered for high-stakes data analysis environments where precision, speed, and multi-agent coordination are paramount. The personality is authoritative yet unobtrusive, prioritizing information density and clarity over decorative flair.

The style is **Corporate Modern with a Technical Edge**. It utilizes a "Utility-First" aesthetic, combining the systematic rigor of enterprise software with the sleekness of modern AI interfaces. It focuses on a clear visual hierarchy to distinguish between different AI agents and their respective outputs, ensuring that the user remains the conductor of the data orchestra.

## Colors
The palette is anchored by a deep crimson primary (#AE1C3F), used strategically for action states and brand presence. 

**Dark Mode (Default):** Uses a sophisticated "Deep Slate" foundation. Backgrounds utilize Slate-950, while cards and sidebars use Slate-900 and Slate-800 to create depth without relying on heavy shadows.
**Light Mode:** Transitions to "Soft Gray" scales. Backgrounds use Slate-50, with pure white surfaces for chat bubbles and cards to maximize legibility.
**Semantic Accents:** Support colors include emerald for successful data queries, amber for processing warnings, and the primary crimson for critical errors or primary CTAs.

## Typography
This design system employs **Inter** for all UI and conversational text to ensure maximum readability across various pixel densities. For data-specific elements, such as logs, agent status indicators, and code snippets, **JetBrains Mono** is utilized to provide a distinct technical texture.

Typography scales are kept tight to support high-density layouts. Contrast is maintained through weight shifts (Medium to Semibold) rather than aggressive size increases, keeping the interface feeling compact and professional.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model. A fixed-width sidebar (260px) houses chat history and workspace management, while the main chat area fluidly expands up to a maximum readable width of 900px.

A strict **4px grid** governs all spacing.
- **High Density:** Components use `inset-compact` (12px) padding to ensure more data is visible on screen at once.
- **Agent Grouping:** Messages from different agents are separated by `stack-md` (16px), while internal message elements (name, timestamp, content) use `stack-xs` (4px).
- **Reflow:** On tablet, the sidebar collapses into a drawer. On mobile, the chat cards expand to 100% width with 12px horizontal margins.

## Elevation & Depth
Depth in this design system is achieved through **Tonal Layering** rather than traditional shadows. 

1.  **Level 0 (Base):** The main background (Slate-950 in dark mode).
2.  **Level 1 (Sidebar/Navigation):** A slightly lighter tone (Slate-900) to create a structural anchor.
3.  **Level 2 (Chat Cards):** Agent message cards use a distinct surface color (Slate-800) with a subtle 1px border (Slate-700) to define their boundaries.
4.  **Level 3 (Popovers/Tooltips):** These use a high-contrast surface with a soft, diffused 15% opacity shadow to float above the workspace.

Backdrop blurs (12px) are used exclusively for the header bar and the input area background to maintain context of the scrolling content beneath.

## Shapes
The shape language is **Soft and Precise**. A 4px standard radius (`rounded-sm`) is applied to buttons, input fields, and small UI widgets to maintain a professional, slightly technical feel. Larger containers like agent cards and the main chat input utilize an 8px radius (`rounded-lg`) to provide a subtle visual distinction from functional utility elements. Interactive states do not change shape, only fill and border color.

## Components
**Agent Message Cards:**
Distinct cards for different agents. Each card features a top-aligned header with a small 24x24px avatar, the agent's name in `headline-agent`, and a "Role" chip. Background colors for cards should subtly shift or include a 2px left-border accent in a unique color (e.g., Primary, Teal, or Indigo) to identify which agent is speaking.

**Data Visualization Placeholders:**
Charts and tables should be contained within the agent's card or as a subsequent "Result" block. These blocks use a darker, recessed background with a `label-mono` header.

**Sleek Input Area:**
A non-expanding, floating text area anchored to the bottom. It features a "Command" icon on the left for agent selection and a "Send" button on the right using the Primary Crimson color.

**Buttons & Chips:**
Buttons are high-contrast with minimal padding. Chips are used for "Agent Tags" or "Data Source" indicators, using low-opacity fills of the primary color with `label-mono` text.

**Scrollbars:**
Minimalist "Ghost" scrollbars that only appear on hover to reduce visual noise in high-density data views.
