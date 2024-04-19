import React, { useEffect, useMemo, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import LinearProgress from '@mui/material/LinearProgress';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';

import {
  useGetMessagesQuery,
  usePatchMessageMutation,
} from 'redux/api/drf/messagecore';

import { DateTime } from 'luxon';

import orderBy from 'lodash/orderBy';

import { usePrevious } from '@uidotdev/usehooks';

import useElementScroll from 'hooks/useElementScroll';
import useScript from 'hooks/useScript';

import { RIGHT_SIDEBAR_WIDTH } from 'constants';

import ChatMessage from './ChatMessage';
import TelegramMessageTypeFilterMenu from './TelegramMessageTypeFilterMenu';

import {
  LoadMoreLink,
  MessagesContainer,
  ScrollToBottomIcon,
} from './StyledChatComponents';

export default function TelegramMessages({ display, isOpen, onNewMessages }) {
  const location = useLocation();
  const navigate = useNavigate();

  const { t } = useTranslation();

  const theme = useTheme();

  const { timezone } = useSelector((state) => state.app);
  const { loggedin, telegramBot, user } = useSelector((state) => state.auth);

  const [messagesContainerRef, { y, height }, scrollTo] = useElementScroll();

  const [pastPage, setPastPage] = useState(null);

  const [newMessages, setNewMessages] = useState([]);
  const [seenMessages, setSeenMessages] = useState([]);

  const [pastMessages, setPastMessages] = useState([]);

  const [isAutoScroll, setIsAutoScroll] = useState(true);

  const [firstMessageId, setFirstMessageId] = useState(null);
  const [lastMessageId, setLastMessageId] = useState(null);

  const [messageTypeFilter, setMessageTypeFilter] = useState('ALL');

  const [patchMessage] = usePatchMessageMutation();
  const { data, isLoading } = useGetMessagesQuery(
    {},
    {
      skip: !loggedin || !telegramBot,
      pollingInterval: process.env.NODE_ENV === 'development' ? 10000 : 3000,
    }
  );
  const {
    data: pastData,
    isFetching: isPastFetching,
    isSuccess: isPastSuccess,
  } = useGetMessagesQuery(
    { page: pastPage, tz: timezone },
    { skip: !pastPage }
  );

  const messageList = useMemo(
    () =>
      pastMessages
        .concat(
          orderBy(
            [...(seenMessages || []), ...(newMessages || [])],
            (o) => DateTime.fromISO(o.datetime).toMillis(),
            'asc'
          )
        )
        .filter(
          (message) =>
            messageTypeFilter === 'ALL' || message.type === messageTypeFilter
        ),
    [pastMessages, newMessages, seenMessages, messageTypeFilter]
  );

  useEffect(() => {
    if (data?.results) {
      const { results } = data;
      const read = results?.filter((item) => item.read) || [];
      const unread = results?.filter((item) => !item.read) || [];
      setSeenMessages(read);
      setNewMessages(unread);
    }
  }, [data?.results]);

  useEffect(() => {
    if (pastData?.results) {
      const { results } = pastData;
      setPastMessages((state) => [
        ...orderBy(
          results,
          (o) => DateTime.fromISO(o.datetime).toMillis(),
          'asc'
        ),
        ...state,
      ]);
    }
  }, [pastData?.results]);

  useEffect(() => {
    if (messageList.length) {
      setFirstMessageId(messageList[0]?.id);
      setLastMessageId(messageList[messageList.length - 1]?.id);
    }
  }, [messageList]);

  useEffect(() => {
    onNewMessages(newMessages?.length);
  }, [newMessages]);

  const prevFirstMessageId = usePrevious(firstMessageId);
  useEffect(() => {
    if (
      isPastSuccess &&
      prevFirstMessageId &&
      prevFirstMessageId !== firstMessageId
    ) {
      const prevFirstMessageEl = document.getElementById(
        `m-${prevFirstMessageId}`
      );
      prevFirstMessageEl?.scrollIntoView({ behavior: 'instant' });
    }
  }, [firstMessageId]);

  useEffect(() => {
    if (lastMessageId && isAutoScroll)
      scrollTo({
        top: height,
        behavior: 'smooth',
      });
  }, [lastMessageId, height, isAutoScroll]);

  useEffect(() => {
    scrollTo({
      top: messagesContainerRef.current?.scrollHeight,
      behavior: 'instant',
    });
  }, [messageTypeFilter]);

  useEffect(() => {
    if (display && isOpen && isAutoScroll)
      scrollTo({
        top: messagesContainerRef.current?.scrollHeight,
        behavior: 'instant',
      });
  }, [display, isOpen, isAutoScroll]);

  useEffect(() => {
    if (display) {
      if (height - y > 1000 && isAutoScroll) setIsAutoScroll(false);
      else if (height - y <= 1000 && !isAutoScroll) setIsAutoScroll(true);
    }
  }, [display, y, height]);

  useEffect(() => {
    setIsAutoScroll(display);
  }, [display]);

  useScript(
    telegramBot && user && !user?.telegram_chat_id
      ? 'https://telegram.org/js/telegram-widget.js?22'
      : null,
    {
      nodeId: 'telegram-messages-button',
      attributes: {
        'data-onauth': 'TelegramWidget.dataOnAuth(user)',
        'data-request-access': 'write',
        'data-telegram-login': telegramBot,
        'data-size': 'medium',
      },
    },
    []
  );

  return (
    <Box
      sx={{
        bgcolor: 'background.paper',
        flex: display ? 1 : 0,
        width: display ? RIGHT_SIDEBAR_WIDTH : 0,
      }}
    >
      {data?.results.length > 0 && (
        <Box sx={{ position: 'relative' }}>
          <TelegramMessageTypeFilterMenu
            display={display}
            onChange={(value) => setMessageTypeFilter(value)}
          />
        </Box>
      )}
      <MessagesContainer
        ref={messagesContainerRef}
        id="telegram-messages-container"
      >
        {loggedin && telegramBot ? (
          <>
            {(isLoading || isPastFetching) && <LinearProgress color="info" />}
            <Box sx={{ textAlign: 'center', mb: 2, mt: 0 }}>
              {((!pastData && data?.next) || pastData?.next) && (
                <LoadMoreLink
                  disabled={isPastFetching}
                  href="#"
                  underline="hover"
                  onClick={(e) => {
                    e.preventDefault();
                    setPastPage((state) => (state ? state + 1 : 2));
                  }}
                >
                  {t('Load more messages')}...
                </LoadMoreLink>
              )}
            </Box>
            {messageList.map((item) => (
              <Box key={item.id}>
                <ChatMessage
                  disableBlocking
                  id={item.id}
                  datetime={item.datetime}
                  message={item.content}
                  username={item.telegram_bot_username}
                  messageBoxStyle={{
                    maxWidth: 320,
                    color:
                      item.type !== 'info'
                        ? `${item.type}.${
                            theme.palette.mode === 'dark' ? 'light' : 'main'
                          }`
                        : undefined,
                  }}
                  isNewMessage={!item.read}
                  onIsSeen={() => {
                    if (!item.read) patchMessage({ id: item.id, read: true });
                    const messageSeen = newMessages.find(
                      (o) => o.id === item.id
                    );
                    if (messageSeen) {
                      setSeenMessages((state) => [...state, messageSeen]);
                      setNewMessages((state) =>
                        state.filter((o) => o.id !== messageSeen.id)
                      );
                    }
                  }}
                />
              </Box>
            ))}
          </>
        ) : (
          <>
            {display && !loggedin && (
              <Button
                color="error"
                size="large"
                variant="contained"
                onClick={() =>
                  navigate('/login', { state: { from: location } })
                }
                sx={{
                  position: 'absolute',
                  top: '35%',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  zIndex: 3,
                }}
              >
                {t('Login')}
              </Button>
            )}
            {display && loggedin && !telegramBot && (
              <Box id="telegram-messages-button" />
            )}
          </>
        )}
      </MessagesContainer>
      <Box sx={{ position: 'relative' }}>
        {display && height - y > 1000 && (
          <ScrollToBottomIcon
            onClick={() => {
              setSeenMessages((state) => [...state, ...newMessages]);
              setNewMessages([]);
              setIsAutoScroll(true);
            }}
          >
            <Badge badgeContent={newMessages.length} color="info">
              <ExpandMoreIcon fontSize="large" />
            </Badge>
          </ScrollToBottomIcon>
        )}
      </Box>
    </Box>
  );
}
