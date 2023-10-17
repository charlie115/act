import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Avatar from '@mui/material/Avatar';
import Backdrop from '@mui/material/Backdrop';
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
import Popper from '@mui/material/Popper';
import SpeedDial from '@mui/material/SpeedDial';
import SpeedDialAction from '@mui/material/SpeedDialAction';
import SpeedDialIcon from '@mui/material/SpeedDialIcon';
import Stack from '@mui/material/Stack';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Typography from '@mui/material/Typography';

import ChatIcon from '@mui/icons-material/Chat';
import CloseIcon from '@mui/icons-material/Close';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import PhoneIcon from '@mui/icons-material/Phone';
import FavoriteIcon from '@mui/icons-material/Favorite';
import PersonPinIcon from '@mui/icons-material/PersonPin';
import PhoneMissedIcon from '@mui/icons-material/PhoneMissed';
import FileCopyIcon from '@mui/icons-material/FileCopyOutlined';
import SaveIcon from '@mui/icons-material/Save';
import PrintIcon from '@mui/icons-material/Print';
import ShareIcon from '@mui/icons-material/Share';

import { blue } from '@mui/material/colors';
import { alpha, styled } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';

import { DateTime } from 'luxon';

import {
  useGetPastMessagesQuery,
  useGetRandomUsernameQuery,
} from 'redux/api/drf/chat';
import { useGetMessagesQuery } from 'redux/api/websocket/chat';

import useRefWithCallback from 'hooks/useRefWithCallback';

import { DATE_FORMAT_API_QUERY } from 'constants';

import ChatInput from './ChatInput';
import ChatMessage from './ChatMessage';

export default function ChatWidget() {
  const messagesContainerRef = useRef();
  const topPlaceholderRef = useRef();

  const { t } = useTranslation();

  const { loggedin, user, nickname } = useSelector((state) => state.auth);

  const [anchorEl, setAnchorEl] = useState(null);

  const [hovered, setHovered] = useState(false);
  const [open, setOpen] = useState(false);

  const [badgeCount, setBadgeCount] = useState(0);

  const [visibleMessages, setVisibleMessages] = useState([]);
  const [newMessage, setNewMessage] = useState(null);
  const [newMessages, setNewMessages] = useState([]);

  const [isAutoScroll, setIsAutoScroll] = useState(true);

  const [startTime, setStartTime] = useState(null);
  const [endTime, setEndTime] = useState(null);

  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  const { refCallback: lastVisibleMessagePlaceholderRef } = useRefWithCallback(
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
    () => [...(visibleMessages || []), ...(newMessages || [])],
    [visibleMessages, newMessages]
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
    if (data?.message) setNewMessage(data?.message);
  }, [data]);

  useEffect(() => {
    setBadgeCount(newMessages.length);
  }, [newMessages]);

  useEffect(() => {
    if (pastMessages?.length > 0)
      setVisibleMessages((state) => [...(pastMessages || []), ...state]);
  }, [pastMessages]);

  return (
    <>
      <Box
        onMouseLeave={() => setHovered(false)}
        sx={{
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
          anchorOrigin={{ vertical: 'top', horizontal: 'left' }}
          sx={{ '& .MuiBadge-badge': { zIndex: 1051 } }}
        >
          <Fab
            color="primary"
            variant={hovered || open ? 'extended' : 'circular'}
            // variant="circular"
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
                // title={t('userFullName', {
                //   firstName: user?.first_name,
                //   lastName: user?.last_name,
                // })}
                title={`@${user?.username || nickname}`}
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
                      setEndTime(newEndTime.toFormat(DATE_FORMAT_API_QUERY));
                    } else if (total >= scrollHeight) {
                      // scrolled to bottom
                    }
                    if (scrollHeight - total > 1000 && isAutoScroll)
                      setIsAutoScroll(false);
                    else if (scrollHeight - total <= 1000 && !isAutoScroll)
                      setIsAutoScroll(true);
                  }}
                >
                  <Box ref={topPlaceholderRef} />
                  {renderMessages.map((item, idx) => (
                    <Box key={item.id}>
                      <ChatMessage
                        {...item}
                        isNewMessage={
                          !!newMessages.find((o) => o.id === item.id)
                        }
                        isOwnMessage={
                          item.username === (user?.username ?? nickname)
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
