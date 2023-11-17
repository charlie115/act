import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Skeleton from '@mui/material/Skeleton';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { useGetAnnouncementsQuery } from 'redux/api/drf/newscore';

import { useTranslation } from 'react-i18next';

import { matchSorter } from 'match-sorter';

import differenceBy from 'lodash/differenceBy';
import uniqBy from 'lodash/uniqBy';

import NewsItem from 'components/NewsItem';

import BinanceSvg from 'assets/svg/binance_logo.svg';
import BithumbSvg from 'assets/svg/bithumb_logo.svg';
import BybitSvg from 'assets/svg/bybit_logo.svg';
import OkxSvg from 'assets/svg/okx_logo.svg';
import UPbitSvg from 'assets/svg/upbit_logo.svg';

const THUMBNAILS = {
  binance: { img: BinanceSvg, bgcolor: 'dark.main' },
  bithumb: { img: BithumbSvg, bgcolor: 'white.main' },
  bybit: { img: BybitSvg, bgcolor: 'dark.main' },
  okx: { img: OkxSvg, bgcolor: 'white.main' },
  upbit: { img: UPbitSvg, bgcolor: 'white.main' },
};

export default function AnnouncementList({ filters, timezone, onUnreadData }) {
  const { t } = useTranslation();

  const [filteredAnnouncementList, setFilteredAnnouncementList] = useState([]);
  const [latestAnnouncementList, setLatestAnnouncementList] = useState([]);
  const [announcementList, setAnnouncementList] = useState([]);

  const [page, setPage] = useState();
  const [startTime, setStartTime] = useState();
  const [endTime, setEndTime] = useState();

  const { data: latestAnnouncements, isLoading } = useGetAnnouncementsQuery(
    {},
    { pollingInterval: 1000 * 60, skip: filters?.startTime && filters?.endTime }
  );
  const {
    data: filteredAnnouncements,
    isUninitialized: isFilteredAnnouncementsUninitialized,
  } = useGetAnnouncementsQuery(
    { page, startTime, endTime, timezone },
    { skip: !(page || (startTime && endTime)) }
  );

  useEffect(() => {
    setStartTime(filters?.startTime);
    setEndTime(filters?.endTime);

    setPage();

    setLatestAnnouncementList([]);
    setFilteredAnnouncementList([]);
  }, [filters?.startTime, filters?.endTime]);

  useEffect(() => {
    setLatestAnnouncementList((state) => {
      const latest = differenceBy(latestAnnouncements?.results, state, 'id');
      return [...latest, ...state];
    });
  }, [latestAnnouncements?.results]);

  useEffect(() => {
    setFilteredAnnouncementList((state) =>
      state.concat(filteredAnnouncements?.results || [])
    );
  }, [filteredAnnouncements]);

  useEffect(() => {
    if (filters?.search.length)
      setAnnouncementList(
        matchSorter(
          uniqBy(
            [...latestAnnouncementList, ...filteredAnnouncementList],
            'id'
          ),
          filters?.search.join(' '),
          {
            keys: ['title', 'subtitle', 'content', 'exchange'],
            threshold: matchSorter.rankings.WORD_STARTS_WITH,
          }
        )
      );
    else
      setAnnouncementList(
        uniqBy([...latestAnnouncementList, ...filteredAnnouncementList], 'id')
      );
  }, [filteredAnnouncementList, latestAnnouncementList, filters?.search]);

  useEffect(() => {
    if (latestAnnouncementList.length)
      onUnreadData(
        latestAnnouncementList.length -
          (latestAnnouncements?.results?.length || 0)
      );
  }, [latestAnnouncements?.results, latestAnnouncementList]);

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
        <Stack sx={{ flex: 1 }}>
          <Skeleton variant="text" />
          <Skeleton variant="text" />
          <Skeleton variant="text" />
        </Stack>
      </Stack>
    ));

  if (announcementList.length === 0)
    return (
      <Typography
        align="center"
        variant="h6"
        sx={{ color: 'secondary.main', fontStyle: 'italic' }}
      >
        {t('No announcements found.')}
      </Typography>
    );

  return (
    <>
      <Box sx={{ p: 2 }}>Filter by category</Box>
      {announcementList?.map((item) => (
        <NewsItem
          key={item.id}
          searchWords={filters?.search}
          {...item}
          thumbnail={THUMBNAILS[item.exchange.toLowerCase()].img}
          slotProps={{
            thumbnail: {
              fit: 'contain',
              sx: {
                bgcolor: THUMBNAILS[item.exchange.toLowerCase()].bgcolor,
                borderRadius: 1,
                p: 1,
              },
            },
          }}
          sx={{ alignItems: 'center' }}
        />
      ))}
      {((isFilteredAnnouncementsUninitialized && announcementList.length > 0) ||
        filteredAnnouncements?.nextPage) && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
          <Button
            color="info"
            onClick={() => setPage(filteredAnnouncements?.nextPage || 2)}
            sx={{ fontStyle: 'italic', my: 3, px: 5 }}
          >
            {t('Load more announcements...')}
          </Button>
        </Box>
      )}
    </>
  );
}
