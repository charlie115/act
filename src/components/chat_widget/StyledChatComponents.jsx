import React from 'react';

import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Tooltip, { tooltipClasses } from '@mui/material/Tooltip';

import { alpha, styled } from '@mui/material/styles';

export const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(0, 1),
  // necessary for content to be below app bar
  ...theme.mixins.toolbar,
  justifyContent: 'flex-start',
}));

export const LoadMoreLink = styled(Link)(() => ({
  fontSize: 12,
  fontStyle: 'italic',
  fontWeight: 700,
}));

export const MessageBox = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isBlocked' && prop !== 'isOwnMessage',
})(({ isBlocked, isOwnMessage, theme }) => {
  const isDark = theme.palette.mode === 'dark';

  let backgroundColor = isOwnMessage
    ? theme.palette.primary.main
    : theme.palette.grey[800];

  if (!isDark)
    backgroundColor = isOwnMessage
      ? theme.palette.primary.light
      : alpha(theme.palette.grey[100], 0.5);

  return {
    backgroundColor,
    minWidth: 150,
    maxWidth: 220,
    padding: 8,
    paddingBottom: 25,
    borderRadius: 4,
    opacity: isBlocked ? 0.5 : 1,
    position: 'relative',
  };
});

export const MessagesContainer = styled(Box)(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  height: window.innerHeight - 162,
  overflowX: 'hidden',
  overflowY: 'auto',
  padding: 8,
  position: 'relative',
  scrollBehavior: 'smooth !important',
  msOverflowStyle: 'none',
  '::-webkit-scrollbar': { display: 'none' },
}));

export const MessageUrl = styled(Link)(({ theme, color }) => ({
  overflowWrap: 'break-word',
  wordWrap: 'break-word',

  MsWordBreak: 'break-all',
  wordBreak: 'break-all',

  MsHyphens: 'auto',
  MozHyphens: 'auto',
  WebkitHyphens: 'auto',
  hyphens: 'auto',

  ':visited': { color: alpha(theme.palette[color].main, 0.8) },
}));

export const ScrollToBottomIcon = styled(IconButton)(({ theme }) => ({
  backgroundColor:
    theme.palette.mode === 'dark'
      ? alpha('#000', 0.3)
      : alpha(theme.palette.grey[100], 0.5),
  position: 'absolute',
  bottom: 10,
  right: 15,
}));

export const StyledTooltip = styled(({ className, ...props }) => (
  <Tooltip {...props} arrow classes={{ popper: className }} />
))(({ theme }) => ({
  [`& .${tooltipClasses.arrow}`]: {
    color:
      theme.palette.mode === 'dark'
        ? theme.palette.common.black
        : alpha(theme.palette.grey[100], 0.5),
  },
  [`& .${tooltipClasses.tooltip}`]: {
    backgroundColor:
      theme.palette.mode === 'dark'
        ? theme.palette.common.black
        : alpha(theme.palette.grey[100], 0.5),
  },
}));
