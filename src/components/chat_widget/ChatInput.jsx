import React from 'react';

import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import InputBase from '@mui/material/InputBase';
import Stack from '@mui/material/Stack';

import EmojiEmotionsIcon from '@mui/icons-material/EmojiEmotions';
import SendIcon from '@mui/icons-material/Send';

import { alpha, styled, useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

// import { Controller, useForm, useWatch } from 'react-hook-form';

function ChatInput() {
  return (
    <Stack
      direction="row"
      sx={{ alignItems: 'flex-end', justifyContent: 'space-between', p: 1 }}
    >
      <InputContainer
        sx={{ flex: 1, maxHeight: 120, overflowY: 'auto', px: 2 }}
      >
        <InputBase autoFocus fullWidth multiline size="large" />
      </InputContainer>
      <Stack direction="row" spacing={0}>
        <IconButton color="secondary" size="small">
          <EmojiEmotionsIcon />
        </IconButton>
        <IconButton color="secondary" size="small">
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
