import React from 'react';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';

import CommentIcon from '@mui/icons-material/Comment';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import VisibilityIcon from '@mui/icons-material/Visibility';

import formatIntlNumber from 'utils/formatIntlNumber';

export default function renderStatsCell({ row: { original } }) {
  return (
    <Stack alignItems="center" direction="row" spacing={2}>
      <Box>
        <ThumbUpIcon sx={{ fontSize: 11.5 }} />{' '}
        {formatIntlNumber(original.likes)}
      </Box>
      <Box>
        <CommentIcon sx={{ fontSize: 11.5 }} />{' '}
        {formatIntlNumber(original.comments)}
      </Box>
      <Box>
        <VisibilityIcon sx={{ fontSize: 11.5 }} />{' '}
        {formatIntlNumber(original.views)}
      </Box>
    </Stack>
  );
}
