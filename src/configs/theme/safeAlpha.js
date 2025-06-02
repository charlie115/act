import { alpha as muiAlpha } from '@mui/material/styles';

// Safe alpha function that handles undefined colors
function safeAlpha(color, opacity) {
  try {
    if (!color) {
      // Return a fallback transparent color if color is undefined
      return `rgba(0, 0, 0, ${opacity})`;
    }
    return muiAlpha(color, opacity);
  } catch (error) {
    // Return a fallback transparent color on error
    return `rgba(0, 0, 0, ${opacity})`;
  }
}

export default safeAlpha;