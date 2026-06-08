---
name: Emerald Intelligence
colors:
  surface: '#0c141e'
  surface-dim: '#0c141e'
  surface-bright: '#323a46'
  surface-container-lowest: '#070f19'
  surface-container-low: '#141c27'
  surface-container: '#18202b'
  surface-container-high: '#232a36'
  surface-container-highest: '#2d3541'
  on-surface: '#dbe3f2'
  on-surface-variant: '#bbcac0'
  inverse-surface: '#dbe3f2'
  inverse-on-surface: '#29313c'
  outline: '#85948b'
  outline-variant: '#3c4a42'
  surface-tint: '#3fdfa5'
  primary: '#41e0a6'
  on-primary: '#003825'
  primary-container: '#00c48c'
  on-primary-container: '#004a33'
  inverse-primary: '#006c4b'
  secondary: '#c9bfff'
  on-secondary: '#2e009c'
  secondary-container: '#4720ca'
  on-secondary-container: '#baaeff'
  tertiary: '#ffbb5a'
  on-tertiary: '#452b00'
  tertiary-container: '#e39f37'
  on-tertiary-container: '#5b3900'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#63fcc0'
  primary-fixed-dim: '#3fdfa5'
  on-primary-fixed: '#002114'
  on-primary-fixed-variant: '#005138'
  secondary-fixed: '#e5deff'
  secondary-fixed-dim: '#c9bfff'
  on-secondary-fixed: '#1a0063'
  on-secondary-fixed-variant: '#441cc8'
  tertiary-fixed: '#ffddb4'
  tertiary-fixed-dim: '#ffb954'
  on-tertiary-fixed: '#291800'
  on-tertiary-fixed-variant: '#633f00'
  background: '#0c141e'
  on-background: '#dbe3f2'
  surface-variant: '#2d3541'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  container-margin: 24px
  gutter: 16px
---

## Brand & Style

The design system is engineered for a premium financial AI experience, balancing the austerity of traditional banking with the agility of modern fintech. It targets high-net-worth individuals and retail investors who require instant, data-driven insights.

The aesthetic is **Modern Glassmorphic**, utilizing deep charcoal layers and translucent panels to create a sense of infinite digital space. The emotional response is one of "Confident Precision"—achieved through high-contrast typography, emerald accents signifying growth, and subtle violet glows that denote the presence of advanced artificial intelligence.

## Colors

The palette is anchored in a multi-layered dark theme. The **Primary Background** provides a deep, non-distracting canvas, while the **Secondary Surface** is used for interactive elements and data cards.

- **Emerald Green (#00C48C):** Used exclusively for "Success" states, growth indicators, and primary action buttons.
- **Vibrant Violet (#7B61FF):** Reserved for AI-generated content, sparkle icons, and processing animations.
- **Gold (#FFB74D):** Used for citations, premium tier badges, and regulatory highlights to ensure authoritative visibility.
- **Danger (#FF6B6B):** Utilized for critical regulatory warnings and negative market trends.

## Typography

This design system utilizes **Inter** across all levels to maintain a systematic, utilitarian feel. 

- **Headlines:** Use tight letter-spacing and bold weights to establish a strong hierarchy. 
- **Body Text:** Optimized for readability in chat interfaces with generous line height (1.5x).
- **Labels:** Used for metadata, button text, and micro-copy, utilizing the Medium (500) weight to ensure legibility against dark backgrounds.
- **Citations:** Small, gold-tinted labels are used when the AI references specific fund documents or regulatory filings.

## Layout & Spacing

The system follows a **Fixed Grid** approach for desktop (12 columns) and a **Fluid Grid** for mobile devices. 

- **Chat Interface:** The central conversation thread is constrained to a max-width of 800px on desktop to prevent eye fatigue.
- **Sidebar Panels:** Fixed 280px width for market watchlists and portfolio summaries.
- **Rhythm:** An 8px linear scale governs all padding and margins. Vertical rhythm in the chat is kept tight (16px between bubbles) to maintain the flow of conversation, while larger gaps (32px) separate distinct topics or financial reports.

## Elevation & Depth

Depth is achieved through **Glassmorphism** rather than traditional drop shadows.

- **Level 0 (Base):** #0D0F14 (Solid).
- **Level 1 (Panels):** #141720 with a 1px border (#1E2330).
- **Level 2 (Overlays/Modals):** Semi-transparent #141720 (85% opacity) with a 12px Backdrop Blur and a subtle inner glow (Top-down, 1px white at 5% opacity).
- **AI Highlight:** Elements generated by the AI feature a subtle outer glow using a desaturated version of the Accent Secondary (#7B61FF) at 10% opacity.

## Shapes

The shape language is sophisticated and approachable. 

- **Panels/Containers:** 16px (rounded-lg) for high-level structure like the chat window or sidebar.
- **Cards/Buttons:** 12px (standard) for internal components like fund cards, quick-reply chips, and primary actions.
- **Inputs:** 8px for text input fields to maintain a professional, slightly sharper edge compared to rounded buttons.

## Components

### Buttons
- **Primary:** Emerald Green fill with white text. High-contrast.
- **Secondary:** Transparent with #1E2330 border. 
- **AI Action:** Gradient border (Emerald to Violet) for special "Analyze" or "Predict" functions.

### Chat Bubbles
- **User:** Right-aligned, Dark Grey (#1E2330) background.
- **AI Assistant:** Left-aligned, Secondary Surface (#141720) with a violet accent line on the left border.

### Input Fields
- Dark background (#0D0F14) with a 1px border. On focus, the border transitions to Emerald Green with a 4px soft outer glow.

### Fund Cards
- Contains fund name (Bold), current NAV, and a mini-sparkline chart. 
- Positive trends use Emerald Green; negative trends use Danger Red.
- Citations appear as small gold-colored superscript or footers within the card.

### Chips/Quick Replies
- Small, rounded-pill shapes with a subtle violet border, used to suggest follow-up questions to the user.