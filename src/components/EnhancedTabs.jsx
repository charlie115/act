import React, { useState, useRef, useEffect } from 'react';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import { styled, alpha, keyframes } from '@mui/material/styles';

// Smooth entrance animation
const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

// Custom styled tabs container
const StyledTabs = styled(Tabs)(({ theme }) => ({
  minHeight: 48,
  '& .MuiTabs-flexContainer': {
    gap: theme.spacing(0.5),
  },
  '& .MuiTabs-indicator': {
    height: 3,
    borderRadius: '3px 3px 0 0',
    backgroundColor: theme.palette.primary.main,
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    boxShadow: `0 0 8px ${alpha(theme.palette.primary.main, 0.4)}`,
  },
  '& .MuiTabs-scrollButtons': {
    transition: 'all 0.2s ease',
    '&.Mui-disabled': {
      opacity: 0.3,
    },
    '&:hover': {
      backgroundColor: alpha(theme.palette.primary.main, 0.08),
    },
  },
}));

// Custom styled tab
const StyledTab = styled(Tab, {
  shouldForwardProp: (prop) => prop !== 'index',
})(({ theme, index = 0 }) => ({
  textTransform: 'none',
  fontWeight: 500,
  fontSize: '0.875rem',
  minHeight: 48,
  padding: theme.spacing(1.5, 2),
  borderRadius: '8px 8px 0 0',
  color: theme.palette.text.secondary,
  // Staggered entrance animation
  opacity: 0,
  animation: `${fadeIn} 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards`,
  animationDelay: `${index * 0.05}s`,
  transition: theme.transitions.create(
    ['color', 'background-color', 'transform'],
    { duration: 200 }
  ),
  '&:hover': {
    color: theme.palette.primary.main,
    backgroundColor: alpha(theme.palette.primary.main, 0.06),
  },
  '&.Mui-selected': {
    color: theme.palette.primary.main,
    fontWeight: 600,
    backgroundColor: alpha(theme.palette.primary.main, 0.04),
  },
  '&:focus-visible': {
    outline: `2px solid ${theme.palette.primary.main}`,
    outlineOffset: -2,
  },
  '&.Mui-disabled': {
    opacity: 0.5,
  },
}));

// Tab panel wrapper
const TabPanel = styled(Box)(() => ({
  animation: `${fadeIn} 0.3s ease-out`,
}));

/**
 * EnhancedTabs - Tabs with smooth sliding indicator and animations
 *
 * @param {Array} tabs - Array of tab objects: { label, value, icon?, disabled? }
 * @param {any} value - Current tab value
 * @param {function} onChange - Tab change handler
 * @param {string} variant - 'scrollable' | 'standard' | 'fullWidth'
 * @param {boolean} centered - Center tabs
 * @param {object} sx - Additional styles
 * @param {ReactNode} children - Tab panel content (optional)
 */
function EnhancedTabs({
  tabs = [],
  value,
  onChange,
  variant = 'scrollable',
  centered = false,
  orientation = 'horizontal',
  sx,
  tabSx,
  children,
  ...props
}) {
  const [indicatorStyle, setIndicatorStyle] = useState({});
  const tabsRef = useRef(null);

  // Calculate indicator position for smooth animation
  useEffect(() => {
    if (tabsRef.current) {
      const selectedTab = tabsRef.current.querySelector('.Mui-selected');
      if (selectedTab) {
        const { offsetLeft, offsetWidth } = selectedTab;
        setIndicatorStyle({
          left: offsetLeft,
          width: offsetWidth,
        });
      }
    }
  }, [value]);

  const handleChange = (event, newValue) => {
    if (onChange) {
      onChange(event, newValue);
    }
  };

  return (
    <Box sx={sx}>
      <StyledTabs
        ref={tabsRef}
        value={value}
        onChange={handleChange}
        variant={variant}
        centered={centered}
        orientation={orientation}
        scrollButtons="auto"
        allowScrollButtonsMobile
        TabIndicatorProps={{
          style: {
            ...indicatorStyle,
          },
        }}
        {...props}
      >
        {tabs.map((tab, index) => (
          <StyledTab
            key={tab.value ?? index}
            label={tab.label}
            value={tab.value ?? index}
            icon={tab.icon}
            iconPosition={tab.iconPosition || 'start'}
            disabled={tab.disabled}
            index={index}
            sx={tabSx}
          />
        ))}
      </StyledTabs>
      {children}
    </Box>
  );
}

/**
 * TabPanelContent - Wrapper for tab panel content with fade animation
 */
export function TabPanelContent({
  children,
  value,
  index,
  keepMounted = false,
  ...props
}) {
  const isActive = value === index;

  if (!keepMounted && !isActive) {
    return null;
  }

  return (
    <TabPanel
      role="tabpanel"
      hidden={!isActive}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...props}
    >
      {(keepMounted || isActive) && children}
    </TabPanel>
  );
}

/**
 * a11yProps - Accessibility props generator for tabs
 */
export const a11yProps = (index) => ({
  id: `tab-${index}`,
  'aria-controls': `tabpanel-${index}`,
});

export default EnhancedTabs;
