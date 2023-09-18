import React, { useState } from 'react';

import Avatar from '@mui/material/Avatar';
import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardHeader from '@mui/material/CardHeader';
import Divider from '@mui/material/Divider';
import Fab from '@mui/material/Fab';
import Fade from '@mui/material/Fade';
import IconButton from '@mui/material/IconButton';
import Popper from '@mui/material/Popper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import ChatIcon from '@mui/icons-material/Chat';
import CloseIcon from '@mui/icons-material/Close';

import { blue } from '@mui/material/colors';
import { styled } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import useRefWithCallback from 'hooks/useRefWithCallback';

import ChatInput from './ChatInput';
import ChatMessage from './ChatMessage';

const MESSAGES = [
  {
    id: 0,
    timestamp: '11:51 pm',
    message: 'Hi',
    senderName: 'Entyne',
    isOwnMessage: false,
  },
  {
    id: 1,
    timestamp: '11:51 pm',
    message: 'Hello',
    isOwnMessage: true,
  },
  {
    id: 2,
    timestamp: '11:51 pm',
    message:
      'The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog.',
    isOwnMessage: true,
  },
  {
    id: 3,
    timestamp: '11:51 pm',
    message:
      'The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog.The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog.',
    isOwnMessage: false,
  },
];

export default function ChatWidget() {
  const { t } = useTranslation();

  const [anchorEl, setAnchorEl] = useState(null);

  const [hovered, setHovered] = useState(false);
  const [open, setOpen] = useState(false);

  const { refCallback } = useRefWithCallback((node) => node.scrollIntoView());

  return (
    <>
      <Box sx={{ position: 'fixed', bottom: 0, right: 0, p: 2 }}>
        <Fab
          color="primary"
          variant={hovered || open ? 'extended' : 'circular'}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          onClick={(event) => {
            setAnchorEl(event.currentTarget);
            setOpen((state) => !state);
          }}
        >
          <ChatIcon fontSize="large" />
          {(hovered || open) && (
            <Typography sx={{ fontWeight: 700, ml: 1 }}>{t('Chat')}</Typography>
          )}
        </Fab>
      </Box>
      <Popper
        transition
        open={open}
        anchorEl={anchorEl}
        placement="top-end"
        popperOptions={{ strategy: 'fixed' }}
        sx={{ zIndex: 1800 }}
      >
        {({ TransitionProps }) => (
          <Fade {...TransitionProps} unmountOnExit={false} timeout={350}>
            <Card
              raised
              sx={{ mb: 1, height: 500, width: 350, position: 'relative' }}
            >
              <Header
                avatar={
                  <OnlineBadge
                    overlap="circular"
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                    variant="dot"
                  >
                    <Avatar
                      alt="Ernestine Lariosa"
                      src="/static/images/avatar/1.jpg"
                      sx={{ bgcolor: blue[400] }}
                    />
                  </OnlineBadge>
                }
                action={
                  <IconButton
                    aria-label="close-chat"
                    color="white"
                    onClick={() => {
                      setAnchorEl(null);
                      setOpen(false);
                    }}
                  >
                    <CloseIcon />
                  </IconButton>
                }
                title="Ernestine Lariosa"
                subheader="Online"
              />
              <Box sx={{ height: 72 }} />
              <Stack sx={{ height: 428, justifyContent: 'space-between' }}>
                <Box sx={{ maxHeight: 383, p: 2, overflowY: 'auto' }}>
                  {MESSAGES.map((item, idx) => (
                    <Box
                      ref={idx === MESSAGES.length - 1 ? refCallback : null}
                      key={item.id}
                    >
                      <ChatMessage {...item} />
                    </Box>
                  ))}
                </Box>
                <Box>
                  <Divider />
                  <ChatInput />
                </Box>
              </Stack>
            </Card>
          </Fade>
        )}
      </Popper>
    </>
  );
}

const Header = styled(CardHeader)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  position: 'fixed',
  left: 0,
  right: 0,
  zIndex: 2,
  borderTopLeftRadius: 4,
  borderTopRightRadius: 4,
  color: theme.palette.light.main,
  '& .MuiCardHeader-subheader': { color: theme.palette.light.main },
}));

const OnlineBadge = styled(Badge)(({ theme }) => ({
  '& .MuiBadge-badge': {
    backgroundColor: theme.palette.success.main,
    color: theme.palette.success.main,
    boxShadow: `0 0 0 1px ${theme.palette.light.main}`,
    '&::after': {
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      borderRadius: '50%',
      animation: 'ripple 1.2s infinite ease-in-out',
      border: '1px solid currentColor',
      content: '""',
    },
  },
  '@keyframes ripple': {
    '0%': {
      transform: 'scale(.8)',
      opacity: 1,
    },
    '100%': {
      transform: 'scale(2.4)',
      opacity: 0,
    },
  },
}));
