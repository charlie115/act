import React, { useEffect, useMemo, useState } from 'react';

import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';

import { useGetPastMessagesQuery } from 'redux/api/drf/chat';
import { useGetChatMessagesQuery } from 'redux/api/websocket/chat';

import { usePrevious } from '@uidotdev/usehooks';

import sortBy from 'lodash/sortBy';

import useElementScroll from 'hooks/useElementScroll';

import { RIGHT_SIDEBAR_WIDTH } from 'constants';

import ChatMessage from './ChatMessage';
import {
  LoadMoreLink,
  MessagesContainer,
  ScrollToBottomIcon,
} from './StyledChatComponents';

export default function CommunityMessages({
  active,
  display,
  isOpen,
  chatUsername,
  blocklist,
  onBlockUser,
  onNewMessages,
}) {
  const { t } = useTranslation();

  const { timezone } = useSelector((state) => state.app);

  const [messagesContainerRef, { y, height }, scrollTo] = useElementScroll();

  const [pastPage, setPastPage] = useState(1);

  const [newMessage, setNewMessage] = useState(null);
  const [newMessages, setNewMessages] = useState([]);
  const [seenMessages, setSeenMessages] = useState([]);

  const [firstMessageId, setFirstMessageId] = useState(null);
  const [lastMessageId, setLastMessageId] = useState(null);

  const [isAutoScroll, setIsAutoScroll] = useState(true);

  const { data } = useGetChatMessagesQuery({}, { skip: !active });
  const {
    data: pastData,
    isFetching: isPastFetching,
    isSuccess: isPastSuccess,
  } = useGetPastMessagesQuery(
    { page: pastPage, tz: timezone },
    { skip: !active }
  );

  const messageList = useMemo(
    () =>
      [...(seenMessages || []), ...(newMessages || [])].filter(
        (item) =>
          !(item.username !== chatUsername && item.status === 'blocked') &&
          !blocklist.includes(item.username)
      ),
    [seenMessages, newMessages, blocklist]
  );

  useEffect(() => {
    if (data?.message) {
      const { message } = data;
      if (!(message.username !== chatUsername && message.status === 'blocked'))
        setNewMessage(data?.message);
      if (message.username === chatUsername) setIsAutoScroll(true);
    }
  }, [data, chatUsername]);

  useEffect(() => {
    if (newMessage) {
      if (!isOpen || !isAutoScroll) {
        setNewMessages((state) => {
          const [lastItem] = state.slice(-1);
          if (lastItem?.id !== newMessage.id) return [...state, newMessage];
          return state;
        });
        setNewMessage(null);
      } else {
        setNewMessage(null);
        setNewMessages([]);
        setSeenMessages((state) => [...state, ...newMessages, newMessage]);
      }
    }
  }, [newMessage, chatUsername, isOpen, isAutoScroll]);

  useEffect(() => {
    if (pastData?.results?.length > 0)
      setSeenMessages((state) => [
        ...sortBy(pastData?.results, 'datetime').map((item, idx) => ({
          ...item,
          id: `past-${idx}-${item.datetime}`,
        })),
        ...state,
      ]);
  }, [pastData]);

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
      pastPage > 1 &&
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

  return (
    <Box
      sx={{
        bgcolor: 'background.paper',
        flex: display ? 1 : 0,
        width: display ? RIGHT_SIDEBAR_WIDTH : 0,
      }}
    >
      <MessagesContainer
        ref={messagesContainerRef}
        id="community-messages-container"
      >
        {isPastFetching && <LinearProgress color="info" />}
        <Box sx={{ textAlign: 'center', mb: 2, mt: 0 }}>
          {pastData?.next && (
            <LoadMoreLink
              disabled={isPastFetching}
              href="#"
              underline="hover"
              onClick={(e) => {
                e.preventDefault();
                setPastPage(pastPage + 1);
              }}
            >
              {t('Load more messages')}...
            </LoadMoreLink>
          )}
        </Box>
        {messageList.map((item) => (
          <Box key={item.id}>
            <ChatMessage
              {...item}
              isNewMessage={!!newMessages.find((o) => o.id === item.id)}
              isOwnMessage={item.username === chatUsername}
              onBlockUser={onBlockUser}
              onIsSeen={() => {
                const messageSeen = newMessages.find((o) => o.id === item.id);
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
