import React, { memo, useState, useEffect, useRef } from 'react';
import { Box } from '@mui/material';
import { useTheme, alpha } from '@mui/material/styles';

/**
 * AnimatedNumber - Smooth count-up animation for real-time number changes
 *
 * A refined number component with smooth interpolation between values.
 * Features flash animation on value change and monospace font for alignment.
 *
 * @param {Object} props
 * @param {number} props.value - The numeric value to display
 * @param {number} [props.decimals=2] - Number of decimal places
 * @param {number} [props.duration=500] - Animation duration in ms
 * @param {string} [props.prefix=''] - Prefix text (e.g., '$')
 * @param {string} [props.suffix=''] - Suffix text (e.g., '%')
 * @param {boolean} [props.showTrend=false] - Show color based on previous value comparison
 * @param {boolean} [props.flashOnChange=true] - Flash animation on value change
 * @param {string} [props.fontSize] - Font size override
 * @param {Object} [props.sx] - Additional MUI sx styles
 */
const AnimatedNumber = memo(({
  value,
  decimals = 2,
  duration = 500,
  prefix = '',
  suffix = '',
  showTrend = false,
  flashOnChange = true,
  fontSize,
  sx,
}) => {
  const theme = useTheme();
  const [displayValue, setDisplayValue] = useState(value);
  const [isFlashing, setIsFlashing] = useState(false);
  const [trend, setTrend] = useState('neutral'); // 'up', 'down', 'neutral'
  const prevValueRef = useRef(value);
  const animationRef = useRef(null);

  useEffect(() => {
    const prevValue = prevValueRef.current;

    // Determine trend direction
    if (showTrend && prevValue !== value) {
      if (value > prevValue) {
        setTrend('up');
      } else if (value < prevValue) {
        setTrend('down');
      }
    }

    // Trigger flash animation
    if (flashOnChange && prevValue !== value) {
      setIsFlashing(true);
      const flashTimer = setTimeout(() => setIsFlashing(false), 600);
      return () => clearTimeout(flashTimer);
    }

    // Animate number
    const startTime = performance.now();
    const startValue = displayValue;
    const diff = value - startValue;

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function (ease-out cubic)
      const easeOut = 1 - (1 - progress)**3;

      const currentValue = startValue + diff * easeOut;
      setDisplayValue(currentValue);

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);
    prevValueRef.current = value;

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [value, duration, showTrend, flashOnChange]);

  // Determine text color based on trend
  const getColor = () => {
    if (!showTrend) return 'inherit';
    if (trend === 'up') return theme.palette.success.main;
    if (trend === 'down') return theme.palette.error.main;
    return 'inherit';
  };

  // Flash background color based on trend
  const getFlashBackground = () => {
    if (!isFlashing) return 'transparent';
    if (trend === 'up') return alpha(theme.palette.success.main, 0.15);
    if (trend === 'down') return alpha(theme.palette.error.main, 0.15);
    return 'transparent';
  };

  const formattedValue = displayValue.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });

  return (
    <Box
      component="span"
      sx={{
        fontFamily: '"JetBrains Mono", "SF Mono", "Fira Code", monospace',
        fontFeatureSettings: '"tnum" 1',
        letterSpacing: '-0.01em',
        fontWeight: 600,
        fontSize: fontSize || 'inherit',
        color: getColor(),
        backgroundColor: getFlashBackground(),
        borderRadius: 0.5,
        px: isFlashing ? 0.5 : 0,
        transition: 'background-color 0.6s ease, color 0.2s ease, padding 0.15s ease',
        display: 'inline-block',
        ...sx,
      }}
    >
      {prefix}
      {formattedValue}
      {suffix}
    </Box>
  );
});

export default AnimatedNumber;
