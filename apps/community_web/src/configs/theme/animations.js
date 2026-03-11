import { keyframes } from '@mui/material/styles';

/**
 * Centralized Animation Utilities
 * TradingView Pro style - purposeful, subtle, professional
 */

// ============================================
// ENTRANCE ANIMATIONS
// ============================================

// Fade in with upward motion
export const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

// Fade in with scale
export const fadeInScale = keyframes`
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
`;

// Slide in from right
export const slideInRight = keyframes`
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

// Slide in from left
export const slideInLeft = keyframes`
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

// ============================================
// DATA/TRADING ANIMATIONS
// ============================================

// Price increase flash (green)
export const flashGreen = keyframes`
  0% {
    background-color: transparent;
  }
  15% {
    background-color: rgba(37, 193, 150, 0.25);
  }
  100% {
    background-color: transparent;
  }
`;

// Price decrease flash (red)
export const flashRed = keyframes`
  0% {
    background-color: transparent;
  }
  15% {
    background-color: rgba(255, 13, 69, 0.25);
  }
  100% {
    background-color: transparent;
  }
`;

// Subtle pulse for live data
export const pulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
`;

// Number count up animation
export const countUp = keyframes`
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
`;

// Glow pulse for important indicators
export const glowPulse = keyframes`
  0%, 100% {
    box-shadow: 0 0 8px rgba(0, 124, 255, 0.2);
  }
  50% {
    box-shadow: 0 0 16px rgba(0, 124, 255, 0.4);
  }
`;

// Success glow pulse
export const glowPulseSuccess = keyframes`
  0%, 100% {
    box-shadow: 0 0 8px rgba(37, 193, 150, 0.2);
  }
  50% {
    box-shadow: 0 0 16px rgba(37, 193, 150, 0.4);
  }
`;

// ============================================
// LOADING ANIMATIONS
// ============================================

// Shimmer effect for skeleton loading
export const shimmer = keyframes`
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
`;

// Spinner rotation
export const spin = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

// Breathing/pulsing for loading states
export const breathe = keyframes`
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(0.98);
    opacity: 0.8;
  }
`;

// ============================================
// MICRO-INTERACTIONS
// ============================================

// Subtle bounce on click
export const bounce = keyframes`
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(0.97);
  }
  100% {
    transform: scale(1);
  }
`;

// Float animation for scroll-to-top button
export const float = keyframes`
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
`;

// Ring expand for focus states
export const ringExpand = keyframes`
  from {
    box-shadow: 0 0 0 0 rgba(0, 124, 255, 0.4);
  }
  to {
    box-shadow: 0 0 0 4px rgba(0, 124, 255, 0);
  }
`;

// ============================================
// ANIMATION PRESETS (Ready-to-use styles)
// ============================================

// Premium easing curve (expo out)
const EASING_PREMIUM = 'cubic-bezier(0.16, 1, 0.3, 1)';
const EASING_SMOOTH = 'cubic-bezier(0.25, 0.1, 0.25, 1)';

export const animationPresets = {
  // Entrance animations
  fadeInUp: {
    opacity: 0,
    animation: `${fadeInUp} 0.4s ${EASING_PREMIUM} forwards`,
  },
  fadeInScale: {
    opacity: 0,
    animation: `${fadeInScale} 0.3s ${EASING_PREMIUM} forwards`,
  },
  slideInRight: {
    opacity: 0,
    animation: `${slideInRight} 0.4s ${EASING_PREMIUM} forwards`,
  },
  slideInLeft: {
    opacity: 0,
    animation: `${slideInLeft} 0.4s ${EASING_PREMIUM} forwards`,
  },

  // Staggered entrance (for lists)
  staggeredFadeIn: (index, baseDelay = 0.04) => ({
    opacity: 0,
    animation: `${fadeInUp} 0.4s ${EASING_PREMIUM} forwards`,
    animationDelay: `${index * baseDelay}s`,
  }),

  // Data flash animations
  dataFlashPositive: {
    animation: `${flashGreen} 0.6s ${EASING_SMOOTH}`,
  },
  dataFlashNegative: {
    animation: `${flashRed} 0.6s ${EASING_SMOOTH}`,
  },
  dataFlash: (isPositive) => ({
    animation: `${isPositive ? flashGreen : flashRed} 0.6s ${EASING_SMOOTH}`,
  }),

  // Glow effects
  glowPulse: {
    animation: `${glowPulse} 2s ease-in-out infinite`,
  },
  glowPulseSuccess: {
    animation: `${glowPulseSuccess} 2s ease-in-out infinite`,
  },

  // Loading states
  shimmer: {
    background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent)',
    backgroundSize: '200% 100%',
    animation: `${shimmer} 1.5s ease-in-out infinite`,
  },
  spin: {
    animation: `${spin} 1s linear infinite`,
  },
  breathe: {
    animation: `${breathe} 2s ease-in-out infinite`,
  },

  // Micro-interactions
  float: {
    animation: `${float} 3s ease-in-out infinite`,
  },
  bounce: {
    animation: `${bounce} 0.2s ease-out`,
  },
};

// ============================================
// TRANSITION PRESETS
// ============================================

export const transitionPresets = {
  // Quick hover feedback
  hover: 'all 0.2s cubic-bezier(0.25, 0.1, 0.25, 1)',
  // Smooth color transitions
  color: 'color 0.2s ease, background-color 0.2s ease',
  // Transform with spring
  transform: 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
  // Shadow depth changes
  shadow: 'box-shadow 0.25s ease',
  // Expand/collapse
  expand: 'all 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
  // Quick micro-interaction
  micro: 'all 0.15s ease-out',
};

// ============================================
// UTILITY HOOKS/HELPERS
// ============================================

/**
 * Get flash animation based on value change direction
 * @param {number} currentValue
 * @param {number} previousValue
 * @returns {object|null} Animation styles or null
 */
export const getValueChangeAnimation = (currentValue, previousValue) => {
  if (previousValue === undefined || currentValue === previousValue) {
    return null;
  }
  return currentValue > previousValue
    ? animationPresets.dataFlashPositive
    : animationPresets.dataFlashNegative;
};

export default {
  // Keyframes
  fadeInUp,
  fadeInScale,
  slideInRight,
  slideInLeft,
  flashGreen,
  flashRed,
  pulse,
  countUp,
  glowPulse,
  glowPulseSuccess,
  shimmer,
  spin,
  breathe,
  bounce,
  float,
  ringExpand,
  // Presets
  animationPresets,
  transitionPresets,
  // Helpers
  getValueChangeAnimation,
};
