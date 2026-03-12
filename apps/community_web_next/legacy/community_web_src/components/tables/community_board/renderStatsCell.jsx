import React from 'react';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Stack from '@mui/material/Stack';

import CommentIcon from '@mui/icons-material/Comment';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import VisibilityIcon from '@mui/icons-material/Visibility';

import formatIntlNumber from 'utils/formatIntlNumber';

export default function renderStatsCell({ row: { original } }) {
  return (
    <Grid container spacing={2} sx={{ px: 3 }}>
      <Grid item xs>
        <CommentIcon sx={{ fontSize: 11.5 }} />{' '}
        {formatIntlNumber(original.comments)}
      </Grid>
      <Grid item xs>
        <VisibilityIcon sx={{ fontSize: 11.5 }} />{' '}
        {formatIntlNumber(original.views)}
      </Grid>
      <Grid item xs>
        <Stack direction="row" spacing={1}>
          <Box>
            <ThumbUpIcon sx={{ fontSize: 11.5 }} />{' '}
            {formatIntlNumber(original.likes)}
          </Box>
          <Box>
            <ThumbDownIcon sx={{ fontSize: 11.5 }} />{' '}
            {formatIntlNumber(original.dislikes)}
          </Box>
        </Stack>
      </Grid>
    </Grid>
  );
}
