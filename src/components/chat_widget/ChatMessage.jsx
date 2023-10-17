import React, { Fragment, useEffect, useRef, useState } from 'react';

import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { styled } from '@mui/material/styles';

import { DateTime } from 'luxon';
import linkify from 'linkify-it';

import { useInView } from 'react-intersection-observer';
import { usePrevious } from '@uidotdev/usehooks';

import stringToColor from 'utils/stringToColor';

const ctrlCharactersRegex =
  // eslint-disable-next-line no-control-regex
  /[\u0000-\u001F\u007F-\u009F\u2000-\u200D\uFEFF]/gim;

export default function ChatMessage({
  isNewMessage,
  isOwnMessage,
  message,
  username,
  datetime,
  onIsSeen,
}) {
  const { ref, inView, entry } = useInView({
    /* Optional options */
    delay: 100,
    threshold: 1,
    trackVisibility: true,
  });

  const [elements, setElements] = useState([]);

  const prevIsNewMessage = usePrevious(isNewMessage);

  useEffect(() => {
    const matches = linkify().match(message);
    if (matches?.length > 0) {
      const newElements = [];
      let currIndex = 0;
      matches.forEach((match, idx) => {
        const { index, lastIndex } = match;
        const textBeforeUrl = message.slice(currIndex, index);
        const url = message
          .slice(index, lastIndex)
          .replace(ctrlCharactersRegex, '');
        newElements.push({
          element: textBeforeUrl,
          id: `${idx}-text`,
        });
        newElements.push({
          element: (
            <MessageUrl
              href={url}
              color={isOwnMessage ? 'accent' : 'primary'}
              rel="noopener"
              target="_blank"
              underline="hover"
            >
              {url}
            </MessageUrl>
          ),
          id: `${idx}-url`,
        });
        currIndex = lastIndex;
      });
      setElements(newElements);
    } else
      setElements([
        {
          element: message,
          id: '0-text',
        },
      ]);
  }, []);

  useEffect(() => {
    if (isNewMessage && inView && onIsSeen) onIsSeen();
  }, [isNewMessage, inView, entry]);

  return (
    <Stack
      direction={isOwnMessage ? 'row-reverse' : 'row'}
      spacing={1}
      sx={{ alignItems: 'flex-start', mb: 2 }}
    >
      {/* {!isOwnMessage && (
        <Avatar
          alt={username}
          src="/static/images/avatar/1.jpg"
          sx={{ height: 32, width: 32 }}
        />
      )} */}

      <Box>
        {!isOwnMessage && (
          <Typography sx={{ color: 'secondary.main', fontSize: 11, mb: 0.25 }}>
            <span
              style={{
                color: stringToColor(username),
                fontSize: 15,
              }}
            >
              &#9679;
            </span>
            @{username}
          </Typography>
        )}
        <Tooltip
          title={DateTime.fromISO(datetime).toFormat('HH:mm')}
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
          <MessageBox
            isOwnMessage={isOwnMessage}
            className={
              prevIsNewMessage && !isNewMessage
                ? 'animate__animated animate__pulse'
                : null
            }
          >
            {elements.map((el) => (
              <Fragment key={el.id}>{el.element}</Fragment>
            ))}
          </MessageBox>
        </Tooltip>
        <Box ref={ref} />
      </Box>
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

const MessageUrl = styled(Link)(() => ({
  overflowWrap: 'break-word',
  wordWrap: 'break-word',

  MsWordBreak: 'break-all',
  wordBreak: 'break-all',

  MsHyphens: 'auto',
  MozHyphens: 'auto',
  WebkitHyphens: 'auto',
  hyphens: 'auto',

  ':visited': {
    // color: alpha(theme.palette.info.main, 0.8),
  },
}));
