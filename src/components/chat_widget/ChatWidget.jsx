import React, { useEffect, useMemo, useRef, useState } from 'react';

import Alert from '@mui/material/Alert';
import Avatar from '@mui/material/Avatar';
import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardHeader from '@mui/material/CardHeader';
import Divider from '@mui/material/Divider';
import Fab from '@mui/material/Fab';
import Fade from '@mui/material/Fade';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Link from '@mui/material/Link';
import Popper from '@mui/material/Popper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import ChatIcon from '@mui/icons-material/Chat';
import CloseIcon from '@mui/icons-material/Close';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import { blue } from '@mui/material/colors';
import { alpha, styled } from '@mui/material/styles';

import { Trans, useTranslation } from 'react-i18next';

import { useDispatch, useSelector } from 'react-redux';
import { blockUser, unblockUser } from 'redux/reducers/chat';

import { DateTime } from 'luxon';

import {
  useGetPastMessagesQuery,
  useGetRandomUsernameQuery,
} from 'redux/api/drf/chat';
import { useGetMessagesQuery } from 'redux/api/websocket/chat';

import useRefWithCallback from 'hooks/useRefWithCallback';

import { DATE_FORMAT_API_QUERY } from 'constants';

import ChatInput from './ChatInput';
import ChatMenu from './ChatMenu';
import ChatMessage from './ChatMessage';

export default function ChatWidget({ isVisible }) {
  const dispatch = useDispatch();

  const blockUserTimeoutRef = useRef();

  const messagesContainerRef = useRef();

  const { t } = useTranslation();

  const { loggedin, user } = useSelector((state) => state.auth);
  const { blocklist, enableNotification, nickname } = useSelector(
    (state) => state.chat
  );

  const chatUsername = user?.username ?? nickname;

  const [anchorEl, setAnchorEl] = useState(null);

  const [display, setDisplay] = useState('block');
  const [hovered, setHovered] = useState(false);
  const [open, setOpen] = useState(false);
  const [badgeCount, setBadgeCount] = useState(0);

  const [visibleMessages, setVisibleMessages] = useState([]);
  const [newMessage, setNewMessage] = useState(null);
  const [newMessages, setNewMessages] = useState([]);

  const [isAutoScroll, setIsAutoScroll] = useState(true);

  const [startTime, setStartTime] = useState(null);
  const [endTime, setEndTime] = useState(null);

  const [blockedUser, setBlockedUser] = useState(null);

  const { refCallback: lastVisibleMessagePlaceholderRef, ref } =
    useRefWithCallback(
      (node) => {
        if (isAutoScroll) {
          setTimeout(() => {
            node.scrollIntoView(false);
            window.scrollBy(0, -10);
          }, 0);
        }
      },
      [isAutoScroll]
    );

  const { data: pastMessages, isFetching: isPastMessagesFetching } =
    useGetPastMessagesQuery({
      startTime,
      endTime,
    });
  const { data } = useGetMessagesQuery();

  useGetRandomUsernameQuery({}, { skip: loggedin || nickname });

  const renderMessages = useMemo(
    () =>
      [...(visibleMessages || []), ...(newMessages || [])].filter(
        (item) =>
          !(item.username !== chatUsername && item.status === 'blocked') &&
          !blocklist.includes(item.username)
      ),
    [visibleMessages, newMessages, blocklist]
  );

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
        // bottomPlaceholderRef.current.scrollIntoView();
      }
    }
  }, [open, isAutoScroll, newMessage, newMessages]);

  useEffect(() => {
    if (data?.message) {
      const { message } = data;
      if (!(message.username !== chatUsername && message.status === 'blocked'))
        setNewMessage(data?.message);
    }
  }, [data]);

  useEffect(() => {
    setBadgeCount(newMessages.length);
  }, [newMessages]);

  useEffect(() => {
    if (pastMessages?.length > 0)
      setVisibleMessages((state) => [...(pastMessages || []), ...state]);
  }, [pastMessages]);

  useEffect(() => {
    if (blockedUser) {
      dispatch(blockUser(blockedUser));
      clearTimeout(blockUserTimeoutRef.current);
    }
  }, [blockedUser]);

  useEffect(() => {
    if (!isVisible) {
      setAnchorEl(null);
      setOpen(false);
      setDisplay('none');
    } else setDisplay('block');
  }, [isVisible]);

  return (
    <>
      <Box
        onMouseLeave={() => setHovered(false)}
        sx={{
          display,
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
            color="primary"
            variant={hovered || open ? 'extended' : 'circular'}
            onMouseEnter={() => setHovered(true)}
            onClick={(event) => {
              setAnchorEl(event.currentTarget);
              setOpen((state) => !state);
            }}
          >
            <ChatIcon fontSize="large" />
            {(hovered || open) && (
              <Typography sx={{ fontWeight: 700, ml: 1 }}>
                {t('Chat')}
              </Typography>
            )}
          </Fab>
        </Badge>
      </Box>
      <Popper
        transition
        open={open}
        anchorEl={anchorEl}
        placement="top-end"
        popperOptions={{ strategy: 'fixed' }}
      >
        {({ TransitionProps }) => (
          <Fade {...TransitionProps} unmountOnExit={false} timeout={350}>
            <Card
              raised
              sx={{
                display,
                mb: 1,
                height: 500,
                width: 350,
                position: 'relative',
              }}
            >
              <Header
                avatar={
                  <OnlineBadge
                    overlap="circular"
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                    variant="dot"
                  >
                    <Avatar
                      alt={t('userFullName', {
                        firstName: user?.first_name,
                        lastName: user?.last_name,
                      })}
                      src={user?.profile?.picture}
                      sx={{ bgcolor: blue[400] }}
                    />
                  </OnlineBadge>
                }
                action={
                  <Stack direction="row">
                    <ChatMenu />
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
                  </Stack>
                }
                // title={t('userFullName', {
                //   firstName: user?.first_name,
                //   lastName: user?.last_name,
                // })}
                title={`@${chatUsername}`}
                subheader="Online"
                titleTypographyProps={{
                  sx: { fontStyle: 'italic', fontWeight: 700 },
                }}
              />
              <Box sx={{ height: 72 }} />
              {isPastMessagesFetching && <LinearProgress color="info" />}
              <Stack sx={{ height: 428, justifyContent: 'space-between' }}>
                <Box
                  ref={messagesContainerRef}
                  sx={{ maxHeight: 383, p: 2, overflowY: 'auto' }}
                  onScroll={(e) => {
                    const { clientHeight, scrollHeight, scrollTop } = e.target;
                    const total = scrollTop + clientHeight;
                    if (total <= clientHeight) {
                      // scrolled to top
                    } else if (total >= scrollHeight) {
                      // scrolled to bottom
                    }
                    if (scrollHeight - total > 1000 && isAutoScroll)
                      setIsAutoScroll(false);
                    else if (scrollHeight - total <= 1000 && !isAutoScroll)
                      setIsAutoScroll(true);
                  }}
                >
                  {ref.current && (
                    <Box sx={{ textAlign: 'center', mb: 2, mt: 0 }}>
                      <LoadMoreLink
                        href="#"
                        underline="hover"
                        onClick={() => {
                          const [firstMessage] = renderMessages;
                          const newEndTime = firstMessage
                            ? DateTime.fromISO(firstMessage.datetime).minus({
                                second: 1,
                              })
                            : DateTime.now();
                          setStartTime(
                            newEndTime
                              .minus({ hours: 2 })
                              .toFormat(DATE_FORMAT_API_QUERY)
                          );
                          setEndTime(
                            newEndTime.toFormat(DATE_FORMAT_API_QUERY)
                          );
                        }}
                      >
                        {t('Load more messages')}...
                      </LoadMoreLink>
                    </Box>
                  )}
                  {renderMessages.map((item, idx) => (
                    <Box key={item.id}>
                      <ChatMessage
                        {...item}
                        isNewMessage={
                          !!newMessages.find((o) => o.id === item.id)
                        }
                        isOwnMessage={item.username === chatUsername}
                        onBlockUser={(blockedUsername) =>
                          setBlockedUser(blockedUsername)
                        }
                        onIsSeen={() => {
                          const messageSeen = newMessages.find(
                            (o) => o.id === item.id
                          );
                          if (messageSeen) {
                            setVisibleMessages((state) => [
                              ...state,
                              messageSeen,
                            ]);
                            setNewMessages((state) =>
                              state.filter((o) => o.id !== messageSeen.id)
                            );
                          }
                        }}
                      />
                      <Box
                        ref={
                          idx === renderMessages.length - 1 - badgeCount
                            ? lastVisibleMessagePlaceholderRef
                            : null
                        }
                        sx={{ scrollMarginBottom: '2em' }}
                      />
                    </Box>
                  ))}
                </Box>
                <Box sx={{ position: 'relative' }}>
                  {badgeCount > 0 && (
                    <IconButton
                      onClick={() => {
                        setVisibleMessages((state) => [
                          ...state,
                          ...newMessages,
                        ]);
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
                            <span
                              style={{ fontStyle: 'italic', fontWeight: 700 }}
                            >
                              @{{ user: blockedUser }}
                            </span>
                            . Their messages will be automatically hidden.
                          </Trans>
                        </Alert>
                      )}
                    </Box>
                  </Fade>
                  <Divider />
                  <ChatInput user={user ?? { username: nickname }} />
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

const LoadMoreLink = styled(Link)(() => ({
  fontSize: 12,
  fontStyle: 'italic',
  fontWeight: 700,
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
