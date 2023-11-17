import React, { Fragment, useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import BlockIcon from '@mui/icons-material/Block';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

import { alpha, styled } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import { DateTime } from 'luxon';
import linkify from 'linkify-it';

import { useInView } from 'react-intersection-observer';
import { usePrevious } from '@uidotdev/usehooks';

import stringToColor from 'utils/stringToColor';

import { REGEX } from 'constants';

const TOOLTIP_POPPER_OPTIONS = {
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
};

const linkifyIt = linkify().add('@', {
  validate: (text, pos, self) => {
    const tail = text.slice(pos);
    if (!self.re.twitter) {
      self.re.twitter = new RegExp(
        `^([a-zA-Z0-9_]){1,15}(?!_)(?=$|${self.re.src_ZPCc})`
      );
    }
    if (self.re.twitter.test(tail)) {
      if (pos >= 2 && tail[pos - 2] === '@') return false;
      return tail.match(self.re.twitter)[0].length;
    }
    return 0;
  },
});

export default function ChatMessage({
  isNewMessage,
  isOwnMessage,
  message,
  status,
  username,
  datetime,
  onBlockUser,
  onIsSeen,
}) {
  const { ref, inView, entry } = useInView({
    /* Optional options */
    delay: 100,
    threshold: 1,
    trackVisibility: true,
  });

  const { t } = useTranslation();

  const [elements, setElements] = useState([]);

  const prevIsNewMessage = usePrevious(isNewMessage);

  useEffect(() => {
    const matches = linkifyIt.match(message);

    if (matches?.length > 0) {
      const newElements = [];
      let currIndex = 0;
      matches.forEach((match, idx) => {
        const { index, lastIndex } = match;
        const textBeforeUrl = message.slice(currIndex, index);
        const url = message
          .slice(index, lastIndex)
          .replace(REGEX.ctrlCharactersRegex, '');
        newElements.push({
          element: textBeforeUrl,
          id: `${idx}-text`,
        });
        newElements.push({
          element: (
            <MessageUrl
              {...(match.schema === '@'
                ? { sx: { fontStyle: 'italic', pointerEvents: 'none' } }
                : { href: url, rel: 'noopener', target: '_blank' })}
              color={isOwnMessage ? 'accent' : 'primary'}
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
      <Box>
        {!isOwnMessage && (
          <>
            <Typography
              sx={{
                display: 'inline',
                color: 'secondary.main',
                fontSize: 11,
                mb: 0.25,
              }}
            >
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
            <IconButton
              aria-label="block-user"
              color="secondary"
              size="small"
              onClick={() => onBlockUser(username)}
              sx={{ display: 'inline', ml: 1, p: 0.25 }}
            >
              <BlockIcon sx={{ fontSize: 12 }} />
            </IconButton>
          </>
        )}
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          {status === 'blocked' && (
            <Tooltip
              title={t('Message not sent')}
              placement="left-start"
              PopperProps={TOOLTIP_POPPER_OPTIONS}
            >
              <InfoOutlinedIcon
                color="error"
                sx={{ cursor: 'pointer', fontSize: 14, opacity: 0.75 }}
              />
            </Tooltip>
          )}
          <Tooltip
            title={DateTime.fromISO(datetime).toFormat('HH:mm')}
            placement={isOwnMessage ? 'left-start' : 'right-start'}
            PopperProps={TOOLTIP_POPPER_OPTIONS}
          >
            <MessageBox
              isBlocked={status === 'blocked'}
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
        </Stack>
        <Box ref={ref} />
      </Box>
    </Stack>
  );
}

const MessageBox = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isBlocked' && prop !== 'isOwnMessage',
})(({ isBlocked, isOwnMessage, theme }) => {
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
    opacity: isBlocked ? 0.5 : 1,
  };
});

const MessageUrl = styled(Link)(({ theme, color }) => ({
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
