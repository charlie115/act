import React from 'react';

import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';

import { styled } from '@mui/material/styles';

export default function ChatMessage({
  message,
  isOwnMessage,
  senderName,
  timestamp,
}) {
  return (
    <Stack
      direction={isOwnMessage ? 'row-reverse' : 'row'}
      spacing={1}
      sx={{ alignItems: 'flex-start', mb: 2 }}
    >
      {!isOwnMessage && (
        <Avatar
          alt={senderName}
          src="/static/images/avatar/1.jpg"
          sx={{ height: 32, width: 32 }}
        />
      )}

      <Tooltip
        title={timestamp}
        placement={isOwnMessage ? 'left-start' : 'right-start'}
        PopperProps={{
          disablePortal: true,
          popperOptions: {
            positionFixed: true,
            modifiers: {
              preventOverflow: {
                enabled: true,
                boundariesElement: 'window',
              },
            },
          },
          sx: { zIndex: 1800 },
        }}
      >
        <MessageBox isOwnMessage={isOwnMessage}>{message}</MessageBox>
      </Tooltip>
    </Stack>
  );
}

const MessageBox = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isOwnMessage',
})(({ isOwnMessage, theme }) => {
  const isDark = theme.palette.mode === 'dark';

  let backgroundColor = isOwnMessage
    ? theme.palette.primary.main
    : theme.palette.grey[800];

  if (!isDark)
    backgroundColor = isOwnMessage
      ? theme.palette.primary.light
      : theme.palette.grey[100];

  return {
    backgroundColor,
    minWidth: 150,
    maxWidth: 220,
    padding: 8,
    borderRadius: 8,
  };
});
