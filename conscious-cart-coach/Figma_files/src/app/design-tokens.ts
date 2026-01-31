/**
 * Conscious Cart Coach Design System
 * Design Tokens - Single source of truth for all design values
 */

export const designTokens = {
  /**
   * COLOR PALETTE
   * Warm, earthy tones that emphasize sustainability and natural choices
   */
  colors: {
    // Primary Brand Colors - Warm earth tones
    brand: {
      primary: '#6b5f3a',         // Deep olive - Primary actions
      primaryHover: '#5b4f2a',    // Darker olive - Hover states
      primaryLight: '#8b7a5a',    // Light olive - Borders
      accent: '#d9b899',          // Warm beige - Secondary actions
      accentHover: '#c9a889',     // Darker beige - Hover states
    },

    // Background Colors
    background: {
      page: '#f5e6d3',            // Cream background - Main page
      header: '#f5d7b1',          // Light tan - Header
      card: '#ffffff',            // White - Cards/panels
      input: '#fef4e6',           // Very light cream - Input fields
      lightAccent: '#f5e6d3',     // Light accent background
    },

    // Text Colors
    text: {
      primary: '#4a3f2a',         // Dark brown - Primary text
      secondary: '#6b5f4a',       // Medium brown - Secondary text
      tertiary: '#8b7a5a',        // Light brown - Tertiary text
      white: '#ffffff',           // White text
    },

    // Border Colors
    border: {
      light: '#e5d5b8',           // Light tan border
      medium: '#e5c7a1',          // Medium tan border
      dark: '#8b7a5a',            // Dark tan border
    },

    // Semantic Colors
    semantic: {
      success: '#7a6f4a',         // Success green-brown
      warning: '#d9b899',         // Warning amber
      error: '#c9665a',           // Error red-brown
      info: '#6b5f4a',            // Info blue-brown
    },

    // Ethical Tags - Background colors for product tags
    tags: {
      organic: '#e8f5e9',         // Light green
      local: '#e3f2fd',           // Light blue
      bestValue: '#fff8e1',       // Light yellow
      seasonal: '#f3e5f5',        // Light purple
      lowPackaging: '#fce4ec',    // Light pink
    },

    // Disabled States
    disabled: {
      background: '#e5d5c0',
      backgroundAlt: '#c5baa8',
      text: '#a69c88',
    },
  },

  /**
   * TYPOGRAPHY
   * Font families, sizes, weights, and line heights
   */
  typography: {
    // Font Families
    fontFamily: {
      primary: 'system-ui, -apple-system, sans-serif',
      heading: 'Georgia, serif',
      monospace: 'monospace',
    },

    // Font Sizes
    fontSize: {
      xs: '0.75rem',      // 12px
      sm: '0.875rem',     // 14px
      base: '1rem',       // 16px
      lg: '1.125rem',     // 18px
      xl: '1.25rem',      // 20px
      '2xl': '1.5rem',    // 24px
      '3xl': '1.875rem',  // 30px
      '4xl': '2.25rem',   // 36px
    },

    // Font Weights
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },

    // Line Heights
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },

  /**
   * SPACING
   * Consistent spacing scale for margins, padding, and gaps
   */
  spacing: {
    '0': '0',
    '1': '0.25rem',    // 4px
    '2': '0.5rem',     // 8px
    '3': '0.75rem',    // 12px
    '4': '1rem',       // 16px
    '5': '1.25rem',    // 20px
    '6': '1.5rem',     // 24px
    '8': '2rem',       // 32px
    '10': '2.5rem',    // 40px
    '12': '3rem',      // 48px
    '16': '4rem',      // 64px
    '20': '5rem',      // 80px
  },

  /**
   * BORDER RADIUS
   * Rounded corners for various elements
   */
  borderRadius: {
    none: '0',
    sm: '0.25rem',     // 4px
    base: '0.375rem',  // 6px
    md: '0.5rem',      // 8px
    lg: '0.625rem',    // 10px
    xl: '0.75rem',     // 12px
    full: '9999px',    // Fully rounded
  },

  /**
   * SHADOWS
   * Box shadows for depth and elevation
   */
  shadows: {
    none: 'none',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
  },

  /**
   * BREAKPOINTS
   * Responsive design breakpoints
   */
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },

  /**
   * Z-INDEX
   * Layering and stacking order
   */
  zIndex: {
    base: 0,
    dropdown: 10,
    sticky: 20,
    modal: 30,
    popover: 40,
    tooltip: 50,
  },

  /**
   * TRANSITIONS
   * Animation durations and timing functions
   */
  transitions: {
    duration: {
      fast: '150ms',
      base: '200ms',
      slow: '300ms',
    },
    timing: {
      ease: 'ease',
      easeIn: 'ease-in',
      easeOut: 'ease-out',
      easeInOut: 'ease-in-out',
    },
  },

  /**
   * COMPONENT-SPECIFIC TOKENS
   */
  components: {
    // Button Styles
    button: {
      padding: {
        sm: '0.5rem 1rem',
        base: '0.75rem 1.5rem',
        lg: '1rem 2rem',
      },
      height: {
        sm: '2rem',
        base: '2.5rem',
        lg: '3rem',
      },
    },

    // Input Styles
    input: {
      height: '2.5rem',
      padding: '0.5rem 0.75rem',
      borderWidth: '1px',
    },

    // Card Styles
    card: {
      padding: '1.5rem',
      borderWidth: '1px',
      borderRadius: '0.5rem',
    },

    // Tag/Badge Styles
    tag: {
      padding: '0.25rem 0.75rem',
      borderRadius: '9999px',
      fontSize: '0.75rem',
    },
  },
};

/**
 * USAGE EXAMPLES:
 * 
 * Import in your components:
 * import { designTokens } from '@/app/design-tokens';
 * 
 * Use in inline styles:
 * style={{ color: designTokens.colors.text.primary }}
 * 
 * Use in Tailwind classes (reference for custom values):
 * className="text-[${designTokens.colors.text.primary}]"
 */

export type DesignTokens = typeof designTokens;
