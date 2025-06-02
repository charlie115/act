import { alpha as muiAlpha } from '@mui/material/styles';

// Safe theme utilities that work even when theme is not fully loaded
export function safeAlpha(color, opacity = 1) {
  try {
    // Handle null/undefined color
    if (!color) {
      return `rgba(0, 0, 0, ${opacity})`;
    }
    
    // Handle already processed rgba/rgb colors
    if (typeof color === 'string' && (color.startsWith('rgba') || color.startsWith('rgb'))) {
      return color;
    }
    
    // Handle hex colors directly
    if (typeof color === 'string' && color.startsWith('#')) {
      const hex = color.replace('#', '');
      const r = parseInt(hex.substr(0, 2), 16);
      const g = parseInt(hex.substr(2, 2), 16);
      const b = parseInt(hex.substr(4, 2), 16);
      return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }
    
    // Try MUI alpha function
    return muiAlpha(color, opacity);
  } catch (error) {
    // Fallback to transparent color
    return `rgba(0, 0, 0, ${opacity})`;
  }
}

// Safe color getter that provides fallbacks
export function safeColor(theme, path, fallback = '#000000') {
  try {
    const keys = path.split('.');
    let value = theme;
    
    keys.forEach((key) => {
      if (value && typeof value === 'object' && key in value) {
        value = value[key];
      } else {
        value = null;
      }
    });
    
    if (value === null) {
      return fallback;
    }
    
    return value || fallback;
  } catch (error) {
    return fallback;
  }
}

// Common color fallbacks
export const COLOR_FALLBACKS = {
  'primary.main': '#007cff',
  'primary.light': '#4da6ff',
  'primary.dark': '#0066d9',
  'secondary.main': '#64748b',
  'error.main': '#ff0d45',
  'warning.main': '#faa12d',
  'info.main': '#00bbff',
  'success.main': '#25C196',
  'background.paper': '#ffffff',
  'background.default': '#fafbfc',
  'text.primary': '#1a1d29',
  'text.secondary': '#64748b',
  'divider': 'rgba(0, 0, 0, 0.08)',
  'grey.50': '#f8fafc',
  'grey.100': '#f1f5f9',
  'grey.200': '#e2e8f0',
  'grey.300': '#cbd5e1',
  'grey.400': '#94a3b8',
  'grey.500': '#64748b',
  'grey.600': '#475569',
  'grey.700': '#334155',
  'grey.800': '#1e293b',
  'grey.900': '#0f172a',
};

// Safe theme getter with automatic fallbacks
export function getThemeColor(theme, path) {
  const fallback = COLOR_FALLBACKS[path] || '#000000';
  return safeColor(theme, `palette.${path}`, fallback);
}