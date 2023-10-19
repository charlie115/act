import React, { useRef, useState } from 'react';

import Box from '@mui/material/Box';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import IconButton from '@mui/material/IconButton';
import InputBase from '@mui/material/InputBase';
import Popper from '@mui/material/Popper';
import Stack from '@mui/material/Stack';

import EmojiEmotionsIcon from '@mui/icons-material/EmojiEmotions';
import SendIcon from '@mui/icons-material/Send';

import data from '@emoji-mart/data';
import Picker from '@emoji-mart/react';

import { styled } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import { useSendMessageMutation } from 'redux/api/websocket/chat';

function ChatInput({ user }) {
  const inputRef = useRef();

  const [sendMessage] = useSendMessageMutation();

  const [emojiPickerAnchorEl, setEmojiPickerAnchorEl] = useState(null);

  const [message, setMessage] = useState('');

  const theme = useSelector((state) => state.app.theme);

  const onSubmit = () => {
    if (/\S/.test(message)) {
      sendMessage({
        username: user?.username,
        email: user?.email,
        message,
      });
      setMessage('');
    }
  };

  return (
    <Stack
      direction="row"
      sx={{ alignItems: 'flex-end', justifyContent: 'space-between', p: 1 }}
    >
      <InputContainer
        sx={{ flex: 1, maxHeight: 120, overflowY: 'auto', px: 2 }}
      >
        <InputBase
          autoFocus
          fullWidth
          multiline
          size="large"
          value={message}
          onChange={(e) => {
            if (e.target.value !== '\n') setMessage(e.target.value);
            setEmojiPickerAnchorEl(null);
          }}
          onKeyPress={(e) => {
            if (e.key === 'Enter') onSubmit();
          }}
          inputProps={{ ref: inputRef }}
        />
      </InputContainer>
      <Stack direction="row" spacing={0}>
        <ClickAwayListener onClickAway={() => setEmojiPickerAnchorEl(null)}>
          <Box>
            <IconButton
              id="emoji-popover"
              color="info"
              size="small"
              onClick={(e) =>
                setEmojiPickerAnchorEl(
                  emojiPickerAnchorEl ? null : e.currentTarget
                )
              }
            >
              <EmojiEmotionsIcon />
            </IconButton>
            <Popper
              id={emojiPickerAnchorEl ? 'emoji-popover' : undefined}
              open={!!emojiPickerAnchorEl}
              anchorEl={emojiPickerAnchorEl}
              onClose={() => setEmojiPickerAnchorEl(null)}
            >
              <Picker
                data={data}
                theme={theme}
                onEmojiSelect={(val) => {
                  const { selectionStart, selectionEnd } = inputRef.current;
                  const text =
                    message.slice(0, selectionStart) +
                    val.native +
                    message.slice(selectionEnd);
                  setMessage(text);
                  inputRef.current.focus();
                }}
                previewConfig={{ showPreview: false }}
              />
            </Popper>
          </Box>
        </ClickAwayListener>
        <IconButton
          color="info"
          size="small"
          disabled={!/\S/.test(message)}
          onClick={onSubmit}
        >
          <SendIcon />
        </IconButton>
      </Stack>
    </Stack>
  );
}

const InputContainer = styled(Box)(() => ({
  flex: 1,
  maxHeight: 120,
  overflowY: 'auto',
  px: 2,
  msOverflowStyle: 'none',
  '::-webkit-scrollbar': { display: 'none' },
}));

export default React.memo(ChatInput);
