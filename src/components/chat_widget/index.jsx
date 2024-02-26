import React, { useEffect, useMemo, useRef, useState } from 'react';

import Alert from '@mui/material/Alert';
import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Drawer from '@mui/material/Drawer';
import Fab from '@mui/material/Fab';
import Fade from '@mui/material/Fade';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

import ChatIcon from '@mui/icons-material/Chat';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import CloseIcon from '@mui/icons-material/Close';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import { alpha, styled, useTheme } from '@mui/material/styles';

import { Trans, useTranslation } from 'react-i18next';

import { useDispatch, useSelector } from 'react-redux';
import { blockUser, unblockUser } from 'redux/reducers/chat';

import {
  useGetPastMessagesQuery,
  useGetRandomUsernameQuery,
} from 'redux/api/drf/chat';
import { useGetMessagesQuery } from 'redux/api/websocket/chat';

import { useHover } from '@uidotdev/usehooks';

import useElementScroll from 'hooks/useElementScroll';
import useRefWithCallback from 'hooks/useRefWithCallback';

import noTextLogo from 'assets/png/logo-no-text.png';

import { RIGHT_SIDEBAR_WIDTH, USER_ROLE } from 'constants';

import ChatChannelSelector from './ChatChannelSelector';
import ChatChannelTabs from './ChatChannelTabs';
import ChatInput from './ChatInput';
import ChatMenu from './ChatMenu';
import ChatMessage from './ChatMessage';

export default function ChatWidget({ isVisible, onStateChange }) {
  const dispatch = useDispatch();

  const blockUserTimeoutRef = useRef();
  // const messagesContainerRef = useRef();

  const { t } = useTranslation();
  const theme = useTheme();

  const [fabRef, hovering] = useHover();

  const { timezone } = useSelector((state) => state.app);
  const { loggedin, user } = useSelector((state) => state.auth);
  const { blocklist, enableNotification, nickname } = useSelector(
    (state) => state.chat
  );

  const chatUsername =
    user && user.role !== USER_ROLE.visitor ? user.username : nickname;

  const [badgeCount, setBadgeCount] = useState(0);

  const [visibleMessages, setVisibleMessages] = useState([]);
  const [newMessage, setNewMessage] = useState(null);
  const [newMessages, setNewMessages] = useState([]);

  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const [pastMessagesPage, setPastMessagesPage] = useState(1);

  const [blockedUser, setBlockedUser] = useState(null);

  const [active, setActive] = useState(true);
  const [channel, setChannel] = useState(null);
  const [open, setOpen] = useState(false);

  const handleDrawerOpen = () => setOpen(true);
  const handleDrawerClose = () => setOpen(false);

  const [messagesContainerRef, { y, height }, scrollTo] = useElementScroll();

  const { refCallback: lastVisibleMessagePlaceholderRef, ref } =
    useRefWithCallback(
      (node) => {
        if (open && isAutoScroll) {
          setTimeout(() => {
            node.scrollIntoView({
              behavior: 'smooth',
              block: 'end',
              inline: 'end',
            });
          }, 0);
        }
      },
      [isAutoScroll, open]
    );

  useGetRandomUsernameQuery(
    {},
    { skip: (loggedin && user?.role !== USER_ROLE.visitor) || nickname }
  );

  const { data } = useGetMessagesQuery({}, { skip: !active });

  const {
    data: pastMessages,
    error: pastMessagesError,
    isError: isPastMessagesError,
    isFetching: isPastMessagesFetching,
    isSuccess: isPastMessagesSuccess,
  } = useGetPastMessagesQuery(
    { page: pastMessagesPage, tz: timezone },
    { skip: pastMessagesPage === null || !active }
  );

  const messageList = useMemo(
    () =>
      [...(visibleMessages || []), ...(newMessages || [])].filter(
        (item) =>
          !(item.username !== chatUsername && item.status === 'blocked') &&
          !blocklist.includes(item.username)
      ),
    [visibleMessages, newMessages, blocklist]
  );

  useEffect(() => {
    if (data?.message) {
      const { message } = data;
      if (!(message.username !== chatUsername && message.status === 'blocked'))
        setNewMessage(data?.message);
    }
  }, [data]);

  useEffect(() => {
    if (pastMessages?.length > 0)
      setVisibleMessages((state) => [...(pastMessages || []), ...state]);
  }, [pastMessages]);

  useEffect(() => {
    setBadgeCount(newMessages.length);
  }, [newMessages, isAutoScroll]);

  useEffect(() => {
    if (newMessage) {
      if (!open || !isAutoScroll) {
        setNewMessages((state) => {
          const [lastItem] = state.slice(-1);
          if (lastItem?.id !== newMessage?.id) return [...state, newMessage];
          return state;
        });
        setNewMessage(null);
      } else {
        setNewMessage(null);
        setNewMessages([]);
        setVisibleMessages((state) => [...state, ...newMessages, newMessage]);
      }
    }
  }, [open, isAutoScroll, newMessage, newMessages]);

  useEffect(() => {
    if (
      isPastMessagesError &&
      pastMessagesError?.data?.detail === 'Invalid page.'
    )
      setPastMessagesPage(null);
  }, [pastMessagesError, isPastMessagesError]);

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
    if (open && isAutoScroll)
      scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'instant',
      });
  }, [open, isAutoScroll]);

  useEffect(() => {
    if (!isVisible) handleDrawerClose();
  }, [isVisible]);

  useEffect(() => {
    if (height - y > 1000 && isAutoScroll) setIsAutoScroll(false);
    else if (height - y <= 1000 && !isAutoScroll) setIsAutoScroll(true);
  }, [y, height]);

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
          badgeContent={!open ? badgeCount : 0}
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
          />
          <ChatMenu />
        </DrawerHeader>
        <Divider />
        {isPastMessagesFetching && <LinearProgress color="info" />}
        <MessagesContainer ref={messagesContainerRef}>
          {ref.current && (
            <Box sx={{ textAlign: 'center', mb: 2, mt: 0 }}>
              {isPastMessagesSuccess && pastMessagesPage !== null && (
                <LoadMoreLink
                  disabled={isPastMessagesFetching}
                  href="#"
                  underline="hover"
                  onClick={(e) => {
                    e.preventDefault();
                    setPastMessagesPage(pastMessagesPage + 1);
                  }}
                >
                  {t('Load more messages')}...
                </LoadMoreLink>
              )}
            </Box>
          )}
          {messageList.map((item) => (
            <Box key={item.id}>
              <ChatMessage
                {...item}
                isNewMessage={!!newMessages.find((o) => o.id === item.id)}
                isOwnMessage={item.username === chatUsername}
                onBlockUser={(blockedUsername) =>
                  setBlockedUser(blockedUsername)
                }
                onIsSeen={() => {
                  const messageSeen = newMessages.find((o) => o.id === item.id);
                  if (messageSeen) {
                    setVisibleMessages((state) => [...state, messageSeen]);
                    setNewMessages((state) =>
                      state.filter((o) => o.id !== messageSeen.id)
                    );
                  }
                }}
              />
            </Box>
          ))}
          <Box
            key={messageList[messageList.length - 1]?.id}
            ref={lastVisibleMessagePlaceholderRef}
            sx={{ scrollMarginBottom: '2em', height: '1px', width: '1px' }}
          />
        </MessagesContainer>
        <Box sx={{ position: 'relative' }}>
          {height - y > 1000 && (
            <IconButton
              onClick={() => {
                setVisibleMessages((state) => [...state, ...newMessages]);
                setNewMessages([]);
                setIsAutoScroll(true);
              }}
              sx={{
                bgcolor: alpha('#000', 0.1),
                position: 'absolute',
                top: -50,
                right: 15,
              }}
            >
              <Badge badgeContent={badgeCount} color="info">
                <ExpandMoreIcon fontSize="large" />
              </Badge>
            </IconButton>
          )}
          <Fade
            unmountOnExit
            in={blockedUser === blocklist?.slice(-1)?.[0]} // Write the needed condition here to make it appear
            timeout={{ enter: 1000, exit: 1000 }} // Edit these two values to change the duration of transition when the element is getting appeared and disappeard
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

export const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(0, 1),
  // necessary for content to be below app bar
  ...theme.mixins.toolbar,
  justifyContent: 'flex-start',
}));

const LoadMoreLink = styled(Link)(() => ({
  fontSize: 12,
  fontStyle: 'italic',
  fontWeight: 700,
}));

const MessagesContainer = styled(Box)(() => ({
  height: window.innerHeight - 162,
  overflowY: 'auto',
  padding: 8,
  scrollBehavior: 'smooth !important',
  msOverflowStyle: 'none',
  '::-webkit-scrollbar': { display: 'none' },
}));
