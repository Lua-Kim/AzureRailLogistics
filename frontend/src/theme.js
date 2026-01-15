// theme.js

export const lightTheme = {
  colors: {
    background: '#f8fafc', // Light gray background
    surface: '#ffffff', // White surface
    surfaceHighlight: '#e2e8f0', // Lighter gray for highlights
    surfaceTransparent: 'rgba(255, 255, 255, 0.8)',
    border: '#cbd5e1', // Gray border
    primary: '#3b82f6', // Same primary color
    primaryDark: '#2563eb',
    text: {
      main: '#0f172a', // Dark text for readability
      sub: '#475569',
      muted: '#94a3b8',
      inverse: '#ffffff' // White text on colored backgrounds
    },
    status: {
      success: '#16a34a',
      warning: '#f59e0b',
      danger: '#dc2626',
      live: '#16a34a'
    }
  },
  fonts: {
    main: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: 'monospace'
  },
  borderRadius: '16px'
};

export const darkTheme = {
  colors: {
    background: '#040508',
    surface: '#0b0e14',
    surfaceHighlight: '#1e293b',
    surfaceTransparent: 'rgba(15, 23, 42, 0.8)',
    border: '#1e293b',
    primary: '#3b82f6',
    primaryDark: '#2563eb',
    text: {
      main: '#e2e8f0',
      sub: '#94a3b8',
      muted: '#64748b',
      inverse: '#ffffff'
    },
    status: {
      success: '#10b981',
      warning: '#f59e0b',
      danger: '#ef4444',
      live: '#10b981'
    }
  },
  fonts: {
    main: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: 'monospace'
  },
  borderRadius: '16px'
};