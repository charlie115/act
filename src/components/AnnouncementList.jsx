import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Skeleton from '@mui/material/Skeleton';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import HighlightOffIcon from '@mui/icons-material/HighlightOff';

import { useGetAnnouncementsQuery } from 'redux/api/drf/newscore';

import { Trans, useTranslation } from 'react-i18next';

import { matchSorter } from 'match-sorter';

import differenceBy from 'lodash/differenceBy';
import uniqBy from 'lodash/uniqBy';

import NewsItem from 'components/NewsItem';

import BinanceSvg from 'assets/svg/binance_logo.svg';
import BithumbSvg from 'assets/svg/bithumb_logo.svg';
import BybitSvg from 'assets/svg/bybit_logo.svg';
import OkxSvg from 'assets/svg/okx_logo.svg';
import UPbitSvg from 'assets/svg/upbit_logo.svg';

const CATEGORIES = {
  Airdrop: { label: <Trans>Airdrop</Trans> },
  Maintenance: { color: 'secondary', label: <Trans>Maintenance</Trans> },
  Delisting: { color: 'error', label: <Trans>Delisting</Trans> },
  'Deposit/Withdrawal': {
    color: 'warning',
    label: <Trans>Deposit/Withdrawal</Trans>,
  },
  'New Listing': { color: 'success', label: <Trans>New Listing</Trans> },
  Notice: { color: 'info', label: <Trans>Notice</Trans> },
};

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

  const [categoryFilters, setCategoryFilters] = useState([]);

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
          ).filter(
            (item) =>
              categoryFilters.length === 0 ||
              categoryFilters.includes(item.category)
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
        uniqBy(
          [...latestAnnouncementList, ...filteredAnnouncementList],
          'id'
        ).filter(
          (item) =>
            categoryFilters.length === 0 ||
            categoryFilters.includes(item.category)
        )
      );
  }, [
    filteredAnnouncementList,
    latestAnnouncementList,
    categoryFilters,
    filters?.search,
  ]);

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
        sx={{ alignItems: 'center', mb: 1, mx: 1 }}
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

  return (
    <>
      <Stack
        useFlexGap
        alignItems="center"
        direction="row"
        flexWrap="wrap"
        spacing={1}
        sx={{ mb: 3, px: 2 }}
      >
        <Box sx={{ mr: 1 }}>{t('Filter by category')}</Box>
        {[
          'Notice',
          'Maintenance',
          'New Listing',
          'Delisting',
          'Deposit/Withdrawal',
          'Airdrop',
        ].map((category) => (
          <Chip
            key={category}
            size="small"
            label={CATEGORIES[category].label}
            color={CATEGORIES[category].color}
            variant={
              categoryFilters.includes(category) ? 'contained' : 'outlined'
            }
            onClick={() =>
              setCategoryFilters((state) => state.concat(category))
            }
            onDelete={
              categoryFilters.includes(category)
                ? () =>
                    setCategoryFilters((state) =>
                      state.filter((item) => item !== category)
                    )
                : undefined
            }
            sx={
              {
                // height: '16px',
                // opacity: categoryFilters.includes(category) ? 1 : 0.65,
              }
            }
          />
        ))}
        {categoryFilters.length > 0 && (
          <Tooltip title={t('Clear')}>
            <IconButton onClick={() => setCategoryFilters([])}>
              <HighlightOffIcon />
            </IconButton>
          </Tooltip>
        )}
      </Stack>
      {announcementList.length === 0 ? (
        <Typography
          align="center"
          variant="h6"
          sx={{ color: 'secondary.main', fontStyle: 'italic', mt: 3 }}
        >
          {t('No announcements found.')}
        </Typography>
      ) : (
        announcementList?.map((item) => (
          <NewsItem
            key={item.id}
            searchWords={filters?.search}
            {...item}
            category={CATEGORIES[item.category]}
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
        ))
      )}
      {((isFilteredAnnouncementsUninitialized && announcementList.length > 0) ||
        filteredAnnouncements?.nextPage) && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
          <Button
            color="info"
            onClick={() => setPage(filteredAnnouncements?.nextPage || 2)}
            sx={{ fontStyle: 'italic', mb: 6, px: 5 }}
          >
            {t('Load more announcements...')}
          </Button>
        </Box>
      )}
    </>
  );
}
