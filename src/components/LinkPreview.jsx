import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import PhotoRoundedIcon from '@mui/icons-material/PhotoRounded';

import { useTranslation } from 'react-i18next';

export default function LinkPreview({ url, rawUrl }) {
  const { t } = useTranslation();

  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetches the link preview data when the URL prop changes
    const fetchData = async () => {
      try {
        const response = await fetch(url);
        const data = await response.text();

        const parser = new DOMParser();
        const doc = parser.parseFromString(data, 'text/html');
        const title = doc.querySelector('title')?.textContent || '';
        const description =
          doc
            .querySelector('meta[name="description"]')
            ?.getAttribute('content') || '';
        const image =
          doc
            .querySelector('meta[property="og:image"]')
            ?.getAttribute('content') || '';

        setPreviewData({ title, description, image });
        setLoading(false);
      } catch (error) {
        setLoading(false);
      }
    };

    fetchData();
  }, [url]);

  if (loading) {
    return <Typography>...</Typography>;
  }

  if (!previewData) {
    return (
      <Card
        sx={{ cursor: 'pointer', width: 280 }}
        onClick={() => window.open(rawUrl, '_blank', 'noreferrer')}
      >
        <CardContent sx={{ bgcolor: 'grey.400', opacity: 0.45 }}>
          <Stack
            alignItems="center"
            justifyContent="center"
            sx={{ height: 120 }}
          >
            <PhotoRoundedIcon fontSize="large" />
            <Box component="small">{t('No preview available')}</Box>
          </Stack>
        </CardContent>
        <CardActions sx={{ bgcolor: 'light.main' }}>
          <Link
            href={rawUrl}
            rel="noopener"
            target="_blank"
            sx={{
              overflowWrap: 'break-word',
              wordWrap: 'break-word',

              MsWordBreak: 'break-all',
              wordBreak: 'break-all',

              MsHyphens: 'auto',
              MozHyphens: 'auto',
              WebkitHyphens: 'auto',
              hyphens: 'auto',
            }}
          >
            {rawUrl}
          </Link>
        </CardActions>
      </Card>
    );
  }

  return (
    <Box>
      <Typography variant="h3">{previewData?.title}</Typography>
      <Typography>{previewData?.description}</Typography>
      {previewData?.image && <img src={previewData.image} alt={url} />}
    </Box>
  );
}
