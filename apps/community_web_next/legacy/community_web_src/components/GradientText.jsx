import React, { memo } from 'react';
import { Box } from '@mui/material';
import { useTheme } from '@mui/material/styles';

/**
 * GradientText - Text with gradient fill using background-clip
 *
 * A refined text component that displays gradient-colored text.
 * Supports various preset gradients or custom gradient strings.
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Text content to display
 * @param {'primary'|'success'|'error'|'accent'|'info'|string} [props.variant='primary'] - Gradient variant or custom gradient
 * @param {string} [props.component='span'] - HTML element to render
 * @param {Object} [props.sx] - Additional MUI sx styles
 */
const GradientText = memo(({
  children,
  variant = 'primary',
  component = 'span',
  sx,
  ...props
}) => {
  const theme = useTheme();

  // Preset gradients
  const gradientPresets = {
    primary: theme.palette.gradients?.primary || 'linear-gradient(135deg, #007cff 0%, #4da6ff 100%)',
    success: theme.palette.gradients?.success || 'linear-gradient(135deg, #25C196 0%, #51d2ad 100%)',
    error: theme.palette.gradients?.error || 'linear-gradient(135deg, #ff0d45 0%, #ef5350 100%)',
    accent: theme.palette.gradients?.accent || 'linear-gradient(135deg, #fad532 0%, #f9a825 100%)',
    info: theme.palette.gradients?.info || 'linear-gradient(135deg, #00bbff 0%, #4dd5ff 100%)',
    gold: 'linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FFD700 100%)',
    rainbow: 'linear-gradient(135deg, #ff0d45 0%, #fad532 25%, #25C196 50%, #00bbff 75%, #007cff 100%)',
    sunset: 'linear-gradient(135deg, #ff0d45 0%, #faa12d 50%, #fad532 100%)',
    ocean: 'linear-gradient(135deg, #00bbff 0%, #007cff 50%, #0052b3 100%)',
  };

  // Determine the gradient to use
  const gradient = gradientPresets[variant] || variant;

  return (
    <Box
      component={component}
      sx={{
        background: gradient,
        backgroundClip: 'text',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        textFillColor: 'transparent',
        display: 'inline-block',
        ...sx,
      }}
      {...props}
    >
      {children}
    </Box>
  );
});

export default GradientText;
