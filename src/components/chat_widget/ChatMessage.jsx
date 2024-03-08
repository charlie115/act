import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import BlockIcon from '@mui/icons-material/Block';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

import { useTranslation } from 'react-i18next';

import { DateTime } from 'luxon';
import linkify from 'linkify-it';

import { useInView } from 'react-intersection-observer';
import { usePrevious } from '@uidotdev/usehooks';

import stringToColor from 'utils/stringToColor';

import { REGEX } from 'constants';

import { MessageBox, MessageUrl } from './StyledChatComponents';

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
  id,
  isNewMessage,
  isOwnMessage,
  message,
  status,
  username,
  datetime,
  onBlockUser,
  onIsSeen,
  disableBlocking,
  messageBoxStyle,
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
    if (isNewMessage && inView && onIsSeen) onIsSeen(id);
  }, [isNewMessage, inView, entry]);

  return (
    <Stack
      id={`m-${id}`}
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
              <span style={{ color: stringToColor(username), fontSize: 15 }}>
                &#9679;
              </span>
              @{username}
            </Typography>
            {!disableBlocking && (
              <IconButton
                aria-label="block-user"
                color="secondary"
                size="small"
                onClick={() => onBlockUser(username)}
                sx={{ display: 'inline', ml: 1, p: 0.25 }}
              >
                <BlockIcon sx={{ fontSize: 12 }} />
              </IconButton>
            )}
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
          <MessageBox
            isBlocked={status === 'blocked'}
            isOwnMessage={isOwnMessage}
            className={
              prevIsNewMessage && !isNewMessage
                ? 'animate__animated animate__pulse'
                : null
            }
            sx={messageBoxStyle}
          >
            {elements.map((el) => (
              <Box key={el.id} component="span">
                {el.element}
              </Box>
            ))}
            <Box
              component="small"
              sx={{
                position: 'absolute',
                bottom: -5,
                right: 0,
                p: 1,
                color: isOwnMessage ? 'grey.200' : 'secondary.main',
              }}
            >
              {DateTime.fromISO(datetime).toLocaleString(
                DateTime.DATETIME_SHORT
              )}
            </Box>
          </MessageBox>
        </Stack>
        <Box ref={ref} />
      </Box>
    </Stack>
  );
}
