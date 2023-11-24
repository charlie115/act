import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Skeleton from '@mui/material/Skeleton';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { useGetNewsQuery } from 'redux/api/drf/newscore';

import { useTranslation } from 'react-i18next';

import { matchSorter } from 'match-sorter';

import differenceBy from 'lodash/differenceBy';
import uniqBy from 'lodash/uniqBy';

import NewsItem from 'components/NewsItem';

export default function NewsList({ filters, timezone, onUnreadData }) {
  const { t } = useTranslation();

  const [filteredNewsList, setFilteredNewsList] = useState([]);
  const [latestNewsList, setLatestNewsList] = useState([]);
  const [newsList, setNewsList] = useState([]);

  const [page, setPage] = useState();
  const [startTime, setStartTime] = useState();
  const [endTime, setEndTime] = useState();

  const { data: latestNews, isLoading } = useGetNewsQuery(
    {},
    { pollingInterval: 1000 * 60, skip: filters?.startTime && filters?.endTime }
  );
  const { data: filteredNews, isUninitialized: isFilteredNewsUninitialized } =
    useGetNewsQuery(
      { page, startTime, endTime, timezone },
      { skip: !(page || (startTime && endTime)) }
    );

  useEffect(() => {
    setStartTime(filters?.startTime);
    setEndTime(filters?.endTime);

    setPage();

    setLatestNewsList([]);
    setFilteredNewsList([]);
  }, [filters?.startTime, filters?.endTime]);

  useEffect(() => {
    setLatestNewsList((state) => {
      const latest = differenceBy(latestNews?.results, state, 'id');
      return [...latest, ...state];
    });
  }, [latestNews?.results]);

  useEffect(() => {
    setFilteredNewsList((state) => state.concat(filteredNews?.results || []));
  }, [filteredNews]);

  useEffect(() => {
    if (filters?.search.length)
      setNewsList(
        matchSorter(
          uniqBy([...latestNewsList, ...filteredNewsList], 'id'),
          filters?.search.join(' '),
          {
            keys: ['title', 'subtitle', 'content'],
            threshold: matchSorter.rankings.WORD_STARTS_WITH,
          }
        )
      );
    else setNewsList(uniqBy([...latestNewsList, ...filteredNewsList], 'id'));
  }, [filteredNewsList, latestNewsList, filters?.search]);

  useEffect(() => {
    if (latestNewsList.length)
      onUnreadData(latestNewsList.length - (latestNews?.results?.length || 0));
  }, [latestNews?.results, latestNewsList]);

  if (isLoading)
    return [...Array(3).keys()].map((item) => (
      <Stack
        key={item}
        direction={{ xs: 'column', md: 'row' }}
        spacing={2}
        sx={{ alignItems: 'center' }}
      >
        <Skeleton
          variant="rectangular"
          width={150}
          height={100}
          sx={{ borderRadius: 1 }}
        />
        <Stack spacing={1} sx={{ flex: 1 }}>
          <Skeleton variant="text" />
          <Skeleton variant="text" />
          <Skeleton variant="text" />
        </Stack>
      </Stack>
    ));

  if (newsList.length === 0)
    return (
      <Typography
        align="center"
        variant="h6"
        sx={{ color: 'secondary.main', fontStyle: 'italic' }}
      >
        {t('No news found.')}
      </Typography>
    );

  return (
    <>
      {newsList.length === 0 ? (
        <Typography
          align="center"
          variant="h6"
          sx={{ color: 'secondary.main', fontStyle: 'italic' }}
        >
          {t('No news found.')}
        </Typography>
      ) : (
        newsList?.map((item) => (
          <NewsItem key={item.id} searchWords={filters?.search} {...item} />
        ))
      )}
      {((isFilteredNewsUninitialized && newsList.length > 0) ||
        filteredNews?.nextPage) && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
          <Button
            color="info"
            onClick={() => setPage(filteredNews?.nextPage || 2)}
            sx={{ fontStyle: 'italic', my: 3, px: 5 }}
          >
            {t('Load more news...')}
          </Button>
        </Box>
      )}
    </>
  );
}
