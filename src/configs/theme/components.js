import { alpha } from '@mui/material/styles';

export default {
  // Button - Modern styling with hover effects
  MuiButton: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: theme.shape.borderRadius,
        textTransform: 'none',
        fontWeight: theme.typography.fontWeightMedium,
        transition: theme.transitions.create(['background-color', 'box-shadow', 'transform'], {
          duration: theme.transitions.duration.short,
        }),
        '&:hover': {
          transform: 'translateY(-1px)',
        },
        '&:active': {
          transform: 'translateY(0)',
        },
        '&:focus-visible': {
          outline: `2px solid ${theme.palette.primary?.main || '#007cff'}`,
          outlineOffset: 2,
          boxShadow: `0 0 0 4px ${alpha(theme.palette.primary?.main || '#007cff', 0.2)}`,
        },
      }),
      contained: ({ theme, ownerState }) => ({
        boxShadow: theme.shadows[2],
        background: ownerState.color === 'primary' ? theme.palette.gradients.primary : undefined,
        '&:hover': {
          boxShadow: theme.shadows[4],
        },
        '&:disabled': {
          backgroundColor: theme.palette.grey[300],
          opacity: 0.6,
          boxShadow: 'none',
        },
      }),
      outlined: ({ ownerState, theme }) => ({
        borderWidth: '1.5px',
        backgroundColor: theme.palette.mode === 'dark'
          ? alpha(theme.palette[ownerState.color]?.main || theme.palette.primary?.main || '#007cff', 0.08)
          : alpha(theme.palette[ownerState.color]?.main || theme.palette.primary?.main || '#007cff', 0.04),
        '&:hover': {
          borderWidth: '1.5px',
          backgroundColor: alpha(
            theme.palette[ownerState.color]?.main || theme.palette.primary?.main || '#007cff',
            0.12
          ),
        },
        '&:disabled': {
          borderColor: theme.palette.grey[300],
          color: theme.palette.grey[500],
          opacity: 0.6,
        },
      }),
      text: ({ theme }) => ({
        '&:hover': {
          backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.08),
        },
      }),
      // Size variants with smaller dimensions
      sizeSmall: {
        fontSize: '0.75rem', // 12px
        padding: '4px 10px',
      },
      sizeMedium: {
        fontSize: '0.8125rem', // 13px
        padding: '6px 14px',
      },
      sizeLarge: {
        fontSize: '0.875rem', // 14px
        padding: '8px 18px',
      },
    },
  },

  // Paper - Add elevation and modern styling
  MuiPaper: {
    styleOverrides: {
      root: ({ theme }) => ({
        backgroundImage: 'none',
        borderRadius: theme.shape.borderRadius,
        transition: theme.transitions.create(['box-shadow'], {
          duration: theme.transitions.duration.short,
        }),
      }),
      elevation1: ({ theme }) => ({
        boxShadow: theme.shadows[1],
      }),
      elevation2: ({ theme }) => ({
        boxShadow: theme.shadows[2],
      }),
      elevation3: ({ theme }) => ({
        boxShadow: theme.shadows[3],
      }),
    },
  },

  // Card - Modern card styling
  MuiCard: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: theme.shape.borderRadius,
        boxShadow: theme.shadows[1],
        transition: theme.transitions.create(['box-shadow', 'transform'], {
          duration: theme.transitions.duration.short,
        }),
        '&:hover': {
          boxShadow: theme.shadows[4],
          transform: 'translateY(-2px)',
        },
      }),
    },
  },

  // Input fields - Modern styling
  MuiTextField: {
    defaultProps: {
      variant: 'outlined',
    },
  },

  MuiOutlinedInput: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: theme.shape.borderRadius / 1.5,
        transition: theme.transitions.create(['border-color', 'box-shadow'], {
          duration: theme.transitions.duration.short,
        }),
        '&:hover .MuiOutlinedInput-notchedOutline': {
          borderColor: theme.palette.inputBorderColorHover,
        },
        '&.Mui-focused': {
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: theme.palette.inputBorderColorFocus,
            borderWidth: '2px',
          },
        },
      }),
      notchedOutline: ({ theme }) => ({
        borderColor: theme.palette.inputBorderColor,
      }),
      input: {
        padding: '14px 16px',
      },
    },
  },

  MuiFilledInput: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: `${theme.shape.borderRadius / 1.5}px ${theme.shape.borderRadius / 1.5}px 0 0`,
        backgroundColor: alpha(theme.palette.grey?.[500] || '#64748b', 0.08),
        '&:hover': {
          backgroundColor: alpha(theme.palette.grey?.[500] || '#64748b', 0.12),
        },
        '&.Mui-focused': {
          backgroundColor: alpha(theme.palette.grey?.[500] || '#64748b', 0.12),
        },
      }),
      input: { 
        padding: '20px 16px 8px',
      },
    },
  },

  // Dialog - Better z-index and backdrop
  MuiDialog: { 
    styleOverrides: { 
      root: { zIndex: 1300 },
      paper: ({ theme }) => ({
        borderRadius: theme.shape.borderRadius * 1.5,
        boxShadow: theme.shadows[10],
      }),
    },
  },

  // Menu - Modern dropdown styling
  MuiMenu: { 
    styleOverrides: { 
      root: { zIndex: 1300 },
      paper: ({ theme }) => ({
        marginTop: theme.spacing(1),
        borderRadius: theme.shape.borderRadius,
        boxShadow: theme.shadows[8],
      }),
    },
  },

  MuiMenuItem: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: theme.shape.borderRadius / 2,
        margin: theme.spacing(0.5, 1),
        fontSize: '0.875rem',
        transition: theme.transitions.create(['background-color'], {
          duration: theme.transitions.duration.shortest,
        }),
        '@media (max-width:600px)': {
          fontSize: '0.875rem', // Keep readable size on mobile instead of body1's 0.4rem
        },
      }),
    },
  },

  // Popper
  MuiPopper: { styleOverrides: { root: { zIndex: 1300 } } },

  // Table - Modern table styling
  MuiTableCell: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderColor: theme.palette.divider,
        padding: theme.spacing(2),
      }),
      head: ({ theme }) => ({
        fontWeight: theme.typography.fontWeightBold,
        backgroundColor: theme.palette.mode === 'dark' 
          ? theme.palette.background.paper 
          : theme.palette.grey[50],
      }),
    },
  },

  MuiTableRow: {
    styleOverrides: {
      root: ({ theme }) => ({
        '&:hover': {
          backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.04),
        },
      }),
    },
  },

  MuiTableSortLabel: {
    styleOverrides: { 
      root: { 
        width: 'auto',
        fontWeight: 'inherit',
      },
    },
  },

  // Tabs - Modern tab styling
  MuiTab: {
    styleOverrides: {
      root: ({ theme }) => ({
        color: theme.palette.text.secondary,
        fontWeight: theme.typography.fontWeightMedium,
        textTransform: 'none',
        minHeight: 48,
        padding: theme.spacing(1.5, 2),
        transition: theme.transitions.create(['color', 'background-color'], {
          duration: theme.transitions.duration.short,
        }),
        '&:hover': {
          color: theme.palette.text.primary,
          backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.04),
        },
        '&.Mui-selected': {
          color: theme.palette.primary.main,
          fontWeight: theme.typography.fontWeightBold,
        },
      }),
    },
  },

  MuiTabs: {
    styleOverrides: {
      root: ({ ownerState, theme }) => ({
        borderColor: theme.palette.divider,
        minHeight: 48,
        '& .MuiTabs-indicator': {
          backgroundColor: theme.palette.primary.main,
          height: 3,
          borderRadius: '3px 3px 0 0',
          transition: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
        },
        ...(ownerState.orientation === 'horizontal'
          ? {
              borderBottomStyle: 'solid',
              borderBottomWidth: 1,
            }
          : {
              borderRightStyle: 'solid',
              borderRightWidth: 1,
            }),
      }),
      scrollButtons: ({ theme }) => ({
        '&.Mui-disabled': {
          opacity: 0.3,
        },
        transition: theme.transitions.create(['opacity'], {
          duration: theme.transitions.duration.short,
        }),
      }),
    },
  },

  // Toggle Button - Modern styling
  MuiToggleButton: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: theme.shape.borderRadius / 1.5,
        borderColor: theme.palette.divider,
        color: theme.palette.text.secondary,
        transition: theme.transitions.create(['background-color', 'color'], {
          duration: theme.transitions.duration.short,
        }),
        '&:hover': {
          backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.08),
        },
        '&.Mui-selected': {
          backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.12),
          color: theme.palette.primary.main,
          fontWeight: theme.typography.fontWeightBold,
          '&:hover': {
            backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.16),
          },
        },
        '&:disabled': {
          borderColor: theme.palette.grey[300],
          color: theme.palette.grey[500],
          opacity: 0.6,
        },
      }),
    },
  },

  // AppBar - Modern header styling
  MuiAppBar: {
    styleOverrides: {
      root: ({ theme }) => ({
        backgroundImage: 'none',
        boxShadow: theme.shadows[1],
        borderBottom: `1px solid ${theme.palette.divider}`,
        backdropFilter: 'blur(20px)',
        backgroundColor: alpha(theme.palette.background?.paper || '#ffffff', 0.8),
      }),
    },
  },

  // Drawer - Modern sidebar styling
  MuiDrawer: {
    styleOverrides: {
      paper: ({ theme }) => ({
        borderRight: `1px solid ${theme.palette.divider}`,
        backgroundImage: 'none',
      }),
    },
  },

  // Chip - Modern chip styling
  MuiChip: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: theme.shape.borderRadius / 2,
        fontWeight: theme.typography.fontWeightMedium,
      }),
      filled: ({ theme, ownerState }) => ({
        backgroundColor: alpha(
          theme.palette[ownerState.color]?.main || theme.palette.grey?.[300] || '#cbd5e1',
          0.12
        ),
        color: theme.palette[ownerState.color]?.main || theme.palette.text.primary,
      }),
    },
  },

  // Tooltip
  MuiTooltip: {
    styleOverrides: {
      tooltip: ({ theme }) => ({
        backgroundColor: theme.palette.mode === 'dark' 
          ? theme.palette.grey[800] 
          : theme.palette.grey[700],
        borderRadius: theme.shape.borderRadius / 2,
        fontSize: theme.typography.caption.fontSize,
        padding: theme.spacing(1, 1.5),
      }),
    },
  },

  // Alert
  MuiAlert: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: theme.shape.borderRadius,
      }),
      standardSuccess: ({ theme }) => ({
        backgroundColor: alpha(theme.palette.success?.main || '#25C196', 0.12),
        color: theme.palette.success?.dark || '#00543d',
      }),
      standardError: ({ theme }) => ({
        backgroundColor: alpha(theme.palette.error?.main || '#ff0d45', 0.12),
        color: theme.palette.error?.dark || '#b71c1c',
      }),
      standardWarning: ({ theme }) => ({
        backgroundColor: alpha(theme.palette.warning?.main || '#faa12d', 0.12),
        color: theme.palette.warning?.dark || '#e65100',
      }),
      standardInfo: ({ theme }) => ({
        backgroundColor: alpha(theme.palette.info?.main || '#00bbff', 0.12),
        color: theme.palette.info?.dark || '#005999',
      }),
    },
  },


  // ListItemText - Override for navigation items
  MuiListItemText: {
    styleOverrides: {
      primary: ({ theme }) => ({
        fontSize: '0.875rem',
        '@media (max-width:600px)': {
          fontSize: '0.875rem', // Keep readable size on mobile
        },
      }),
    },
  },

};