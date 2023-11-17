import React from 'react';

import Highlighter from 'react-highlight-words';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import PhotoRoundedIcon from '@mui/icons-material/PhotoRounded';
import ShareRoundedIcon from '@mui/icons-material/ShareRounded';

import Image from 'mui-image';

import { alpha, styled, useTheme } from '@mui/material/styles';

import { useDispatch } from 'react-redux';
import { setSnackbar } from 'redux/reducers/app';

import { useTranslation } from 'react-i18next';
import { DateTime } from 'luxon';

import copy from 'copy-to-clipboard';
import truncate from 'lodash/truncate';

const NewsItemContainer = styled((props) => (
  <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} {...props} />
))(({ theme }) => ({
  cursor: 'pointer',
  padding: 10,
  marginBottom: 5,
  ':hover': {
    backgroundColor: alpha(theme.palette.info.main, 0.1),
  },
}));

export default function NewsItem({
  datetime,
  subtitle,
  thumbnail,
  title,
  url,
  searchWords,
  slotProps,
  ...props
}) {
  const dispatch = useDispatch();

  const theme = useTheme();

  const { t } = useTranslation();

  return (
    <NewsItemContainer
      role="link"
      onClick={() => window.open(url, '_blank', 'noreferrer')}
      {...props}
    >
      <Box sx={{ display: 'flex', height: 100, width: 150 }}>
        {thumbnail ? (
          <Image
            errorIcon
            height={100}
            width={150}
            alt={thumbnail}
            src={thumbnail}
            sx={{ borderRadius: 1 }}
            {...(slotProps?.thumbnail || {})}
          />
        ) : (
          <Card
            sx={{
              display: 'flex',
              bgcolor: 'grey.400',
              flex: 1,
              alignItems: 'center',
              justifyContent: 'center',
              opacity: 0.5,
            }}
          >
            <PhotoRoundedIcon fontSize="large" />
          </Card>
        )}
      </Box>
      <Box sx={{ flex: 1 }}>
        <Typography variant="h5">
          <Highlighter searchWords={searchWords} textToHighlight={title} />
        </Typography>
        <Typography
          gutterBottom
          variant="subtitle1"
          sx={{ color: 'secondary.main' }}
        >
          <Highlighter
            searchWords={searchWords}
            textToHighlight={truncate(subtitle, { length: 120 })}
          />
        </Typography>
        <Box sx={{ fontSize: 11 }}>
          <Box
            component="small"
            sx={{
              bgcolor: alpha(theme.palette.secondary.main, 0.5),
              borderRadius: 0.5,
              px: 0.5,
              py: 0.15,
              mr: 1,
            }}
          >
            {DateTime.fromISO(datetime).toFormat('t')}
          </Box>
          {DateTime.fromISO(datetime).toFormat('DDDD')}
        </Box>
      </Box>
      <Box sx={{ alignSelf: 'center' }}>
        <IconButton
          onClick={(e) => {
            e.stopPropagation();
            copy(url);
            dispatch(
              setSnackbar({
                message: t(
                  'The URL to "{{title}}" has been copied to clipboard.',
                  { title }
                ),
                snackbarProps: { autoHideDuration: 1500, open: true },
                alertProps: { severity: 'success' },
              })
            );
          }}
        >
          <ShareRoundedIcon />
        </IconButton>
      </Box>
    </NewsItemContainer>
  );
}
