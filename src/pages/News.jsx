import React, { useEffect, useState } from 'react';

import SwipeableViews from 'react-swipeable-views';

import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';

import { styled, useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import { useTranslation } from 'react-i18next';

import { DateTime } from 'luxon';

import { useWindowScroll } from '@uidotdev/usehooks';

import AnnouncementList from 'components/AnnouncementList';
import CollapsibleSearch from 'components/CollapsibleSearch';
import DateRangePicker from 'components/DateRangePicker';
import NewsList from 'components/NewsList';
import SocMedPostList from 'components/SocMedPostList';
import TabPanel from 'components/TabPanel';

import { DATE_FORMAT_API_QUERY } from 'constants';

const StyledTab = styled(Tab)(({ theme }) => ({
  color: theme.palette.text.main,
  opacity: 0.7,
  textTransform: 'none',
  '&.Mui-selected': {
    color: theme.palette.text.main,
    fontWeight: 700,
    opacity: 1,
  },
}));

const NEWS_TYPE = {
  allNews: 0,
  socialMedia: 1,
  announcements: 2,
};

function a11yProps(id) {
  return {
    id: `news-tab-${id}`,
    'aria-controls': `news-tabpanel-${id}`,
  };
}

export default function News() {
  const theme = useTheme();

  const [{ y }, scrollTo] = useWindowScroll();

  const { t } = useTranslation();

  const { timezone } = useSelector((state) => state.app);

  const [currentTab, setCurrentTab] = useState(NEWS_TYPE.allNews);

  const [search, setSearch] = useState([]);

  const [unreadMessage, setUnreadMessage] = useState();

  const [startTime, setStartTime] = useState();
  const [endTime, setEndTime] = useState();

  const [announcementsBadge, setAnnouncementsBadge] = useState(false);
  const [newsBadge, setNewsBadge] = useState(false);
  const [socialMediaBadge, setSocialMediaBadge] = useState(false);

  useEffect(() => {
    scrollTo({ left: 0, top: 0, behavior: 'smooth' });
    setUnreadMessage();
    switch (currentTab) {
      case NEWS_TYPE.allNews:
        setNewsBadge(false);
        break;
      case NEWS_TYPE.socialMedia:
        setSocialMediaBadge(false);
        break;
      case NEWS_TYPE.announcements:
        setAnnouncementsBadge(false);
        break;
      default:
        break;
    }
  }, [currentTab]);

  return (
    <Box sx={{ flex: 1 }}>
      {unreadMessage && (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            position: 'sticky',
            top: 70,
            zIndex: 1,
          }}
        >
          <Button
            variant="contained"
            onClick={() => {
              setUnreadMessage();
              scrollTo({ left: 0, top: 0, behavior: 'smooth' });
            }}
            sx={{ borderRadius: 4, opacity: 0.85, px: 3 }}
          >
            {unreadMessage}
          </Button>
        </Box>
      )}
      <Stack
        direction="row"
        spacing={{ xs: 1, sm: 2 }}
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 3,
        }}
      >
        <Tabs
          // centered
          // disableRipple
          aria-label="news-tabs"
          value={currentTab}
          // indicatorColor="secondary"
          // textColor="secondary"
          // variant="fullWidth"
          onChange={(e, newValue) => setCurrentTab(newValue)}
          sx={{
            '& .MuiTabs-indicator': { bgcolor: 'text.main', height: '1px' },
          }}
        >
          <StyledTab
            label={
              <Badge color="error" variant="dot" invisible={!newsBadge}>
                {t('All News')}
              </Badge>
            }
            value={NEWS_TYPE.allNews}
            {...a11yProps(NEWS_TYPE.allNews)}
          />
          <StyledTab
            label={
              <Badge color="error" variant="dot" invisible={!socialMediaBadge}>
                {t('Social Media')}
              </Badge>
            }
            value={NEWS_TYPE.socialMedia}
            {...a11yProps(NEWS_TYPE.socialMedia)}
          />
          <StyledTab
            label={
              <Badge
                color="error"
                variant="dot"
                invisible={!announcementsBadge}
              >
                {t('Exchange Notice')}
              </Badge>
            }
            value={NEWS_TYPE.announcements}
            {...a11yProps(NEWS_TYPE.announcements)}
          />
        </Tabs>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center', px: 1 }}>
          <Box sx={{ p: 1 }}>
            <DateRangePicker
              onChange={({ from, to }) => {
                setStartTime(
                  DateTime.fromMillis(from)
                    .startOf('day')
                    .toFormat(DATE_FORMAT_API_QUERY)
                );
                setEndTime(
                  DateTime.fromMillis(to)
                    .endOf('day')
                    .toFormat(DATE_FORMAT_API_QUERY)
                );
              }}
              onClear={(range) => {
                if (range?.from && range?.to) {
                  setStartTime();
                  setEndTime();
                }
              }}
            />
          </Box>
          <CollapsibleSearch
            onChange={(value) => setSearch(value?.match(/[^ ]+/g) || [])}
          />
        </Stack>
      </Stack>
      <SwipeableViews
        axis={theme.direction === 'rtl' ? 'x-reverse' : 'x'}
        index={currentTab}
        onChangeIndex={(newIndex) => setCurrentTab(newIndex)}
      >
        <TabPanel
          index={NEWS_TYPE.allNews}
          dir={theme.direction}
          value={currentTab}
        >
          <NewsList
            filters={{ search, startTime, endTime }}
            timezone={timezone}
            isActive={currentTab === NEWS_TYPE.allNews}
            onUnreadData={(unread) => {
              if (currentTab === NEWS_TYPE.allNews)
                if (y > 150 && unread) setUnreadMessage(t('See latest news'));
                else setUnreadMessage();
              else setNewsBadge(unread > 0);
            }}
          />
        </TabPanel>
        <TabPanel index={1} dir={theme.direction} value={currentTab}>
          <SocMedPostList
            filters={{ search, startTime, endTime }}
            timezone={timezone}
            isActive={currentTab === NEWS_TYPE.socialMedia}
            onUnreadData={(unread) => {
              if (currentTab === NEWS_TYPE.socialMedia)
                if (y > 150 && unread) setUnreadMessage(t('See latest posts'));
                else setUnreadMessage();
              else setSocialMediaBadge(unread > 0);
            }}
          />
        </TabPanel>
        <TabPanel index={2} dir={theme.direction} value={currentTab}>
          <AnnouncementList
            filters={{ search, startTime, endTime }}
            timezone={timezone}
            isActive={currentTab === NEWS_TYPE.announcements}
            onUnreadData={(unread) => {
              if (currentTab === NEWS_TYPE.announcements)
                if (y > 150 && unread)
                  setUnreadMessage(t('See latest announcements'));
                else setUnreadMessage();
              else setAnnouncementsBadge(unread > 0);
            }}
          />
        </TabPanel>
      </SwipeableViews>
    </Box>
  );
}
