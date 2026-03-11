import React, { useEffect, useRef, useState } from 'react';

import Alert from '@mui/material/Alert';
import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Drawer from '@mui/material/Drawer';
import Fab from '@mui/material/Fab';
import Fade from '@mui/material/Fade';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';

import ChatIcon from '@mui/icons-material/Chat';
import CloseIcon from '@mui/icons-material/Close';

import { Trans, useTranslation } from 'react-i18next';

import { useDispatch, useSelector } from 'react-redux';
import { blockUser, unblockUser } from 'redux/reducers/chat';

import { useGetRandomUsernameQuery } from 'redux/api/drf/chat';

import { useHover, useVisibilityChange } from '@uidotdev/usehooks';

import noTextLogo from 'assets/png/logo-no-text.png';

import { RIGHT_SIDEBAR_WIDTH, USER_ROLE } from 'constants';

import ChatChannelSelector from './ChatChannelSelector';
import ChatInput from './ChatInput';
import ChatMenu from './ChatMenu';

import CommunityMessages from './CommunityMessages';
import TelegramMessages from './TelegramMessages';

import { DrawerHeader } from './StyledChatComponents';

export { DrawerHeader };

export default function ChatWidget({ isVisible, onStateChange }) {
  const dispatch = useDispatch();

  const blockUserTimeoutRef = useRef();

  const isFocused = useVisibilityChange();

  const { t } = useTranslation();

  const [fabRef, hovering] = useHover();

  const { loggedin, user } = useSelector((state) => state.auth);
  const { blocklist, enableNotification, nickname } = useSelector(
    (state) => state.chat
  );

  const chatUsername =
    user && user.role !== USER_ROLE.visitor ? user.username : nickname;

  const [badges, setBadges] = useState({});

  const [blockedUser, setBlockedUser] = useState(null);

  const [active, setActive] = useState(true);
  const [channel, setChannel] = useState(null);
  const [open, setOpen] = useState(false);

  const handleDrawerOpen = () => setOpen(true);
  const handleDrawerClose = () => setOpen(false);

  useGetRandomUsernameQuery(
    {},
    { skip: (loggedin && user?.role !== USER_ROLE.visitor) || nickname }
  );

  useEffect(() => {
    if (blockedUser) {
      dispatch(blockUser(blockedUser));
      clearTimeout(blockUserTimeoutRef.current);
    }
  }, [blockedUser]);

  useEffect(() => {
    onStateChange({ open });
  }, [open]);

  useEffect(() => {
    if (!isVisible) handleDrawerClose();
  }, [isVisible]);

  useEffect(() => {
    let timeout;
    if (!isFocused) {
      timeout = setTimeout(() => {
        setActive(false);
      }, 300000);
    } else setActive(true);

    return () => {
      if (timeout) clearTimeout(timeout);
    };
  }, [isFocused]);

  return (
    <>
      <Box
        sx={{
          display: isVisible ? 'block' : 'none',
          position: 'fixed',
          bottom: 0,
          right: 0,
          p: 1,
          zIndex: 10,
        }}
      >
        <Badge
          badgeContent={!open ? badges?.telegram || 0 : 0}
          color="error"
          overlap="circular"
          invisible={!enableNotification}
          anchorOrigin={{ vertical: 'top', horizontal: 'left' }}
          sx={{ '& .MuiBadge-badge': { zIndex: 1051 } }}
        >
          <Fab
            ref={fabRef}
            color="primary"
            variant={hovering ? 'extended' : 'circular'}
            onClick={handleDrawerOpen}
          >
            <ChatIcon fontSize="large" />
            {hovering && (
              <Typography sx={{ fontWeight: 700, ml: 1 }}>
                {t('Chat')}
              </Typography>
            )}
          </Fab>
        </Badge>
      </Box>
      <Drawer
        anchor="right"
        variant="persistent"
        open={open}
        sx={{
          width: RIGHT_SIDEBAR_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': { width: RIGHT_SIDEBAR_WIDTH },
        }}
      >
        <DrawerHeader>
          <IconButton onClick={handleDrawerClose}>
            <CloseIcon />
          </IconButton>
          <Box
            component="img"
            src={noTextLogo}
            alt="ArbiCrypto"
            sx={{ mr: 1, width: 24 }}
          />
          <Typography
            variant="h5"
            sx={{ fontWeight: 700, textTransform: 'uppercase' }}
          >
            {t('Chat')}
          </Typography>
          <ChatChannelSelector
            onChange={(selected) => setChannel(selected?.id)}
            badges={badges}
          />
          <ChatMenu />
        </DrawerHeader>
        <Divider />
        <Box sx={{ display: 'flex', overflow: 'hidden' }}>
          <TelegramMessages
            active={active}
            display={channel === 0}
            isOpen={open}
            onNewMessages={(count) =>
              setBadges((state) => ({ ...state, telegram: count }))
            }
          />
          <CommunityMessages
            active={active}
            display={channel === 1}
            isOpen={open}
            chatUsername={chatUsername}
            blocklist={blocklist}
            onBlockUser={(blockedUsername) => setBlockedUser(blockedUsername)}
            onNewMessages={(count) =>
              setBadges((state) => ({ ...state, community: count }))
            }
          />
        </Box>
        <Box sx={{ position: 'relative' }}>
          <Fade
            unmountOnExit
            in={blockedUser === blocklist?.slice(-1)?.[0]}
            timeout={{ enter: 1000, exit: 1000 }}
            addEndListener={() => {
              blockUserTimeoutRef.current = setTimeout(() => {
                setBlockedUser(null);
              }, 6000);
            }}
          >
            <Box>
              {blockedUser && (
                <Alert
                  icon={false}
                  severity="success"
                  variant="standard"
                  action={
                    <Button
                      color="inherit"
                      size="small"
                      onClick={() => {
                        dispatch(unblockUser(blockedUser));
                        setBlockedUser(null);
                        clearTimeout(blockUserTimeoutRef.current);
                      }}
                    >
                      {t('Undo')}
                    </Button>
                  }
                  sx={{ alignItems: 'center' }}
                >
                  <Trans>
                    You have blocked{' '}
                    <span style={{ fontStyle: 'italic', fontWeight: 700 }}>
                      @{{ user: blockedUser }}
                    </span>
                    . Their messages will be automatically hidden.
                  </Trans>
                </Alert>
              )}
            </Box>
          </Fade>
        </Box>
        <Box>
          <ChatInput
            open={open}
            user={user ?? { username: nickname }}
            disabled={channel === 0}
          />
        </Box>
      </Drawer>
    </>
  );
}
