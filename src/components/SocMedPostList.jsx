import React, { Fragment, useEffect, useState } from 'react';

import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import ListItemText from '@mui/material/ListItemText';
import Skeleton from '@mui/material/Skeleton';
import Stack from '@mui/material/Stack';
import SvgIcon from '@mui/material/SvgIcon';
import Typography from '@mui/material/Typography';

import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded';
import ShareRoundedIcon from '@mui/icons-material/ShareRounded';

import { alpha, useTheme } from '@mui/material/styles';

import { useGetSocialMediaPostsQuery } from 'redux/api/drf/newscore';

import { useTranslation } from 'react-i18next';

import { matchSorter } from 'match-sorter';

import linkify from 'linkify-it';

import copy from 'copy-to-clipboard';

import differenceBy from 'lodash/differenceBy';
import truncate from 'lodash/truncate';
import uniqBy from 'lodash/uniqBy';

import { DateTime } from 'luxon';

import { useDispatch } from 'react-redux';
import { setSnackbar } from 'redux/reducers/app';

import formatShortNumber from 'utils/formatShortNumber';

import LinkPreview from 'components/LinkPreview';

import { ReactComponent as CommentSvg } from 'assets/icons/font-awesome/comment-solid.svg';
import { ReactComponent as HeartSvg } from 'assets/icons/font-awesome/heart-solid.svg';
import { ReactComponent as QuoteRightSvg } from 'assets/icons/font-awesome/quote-right-solid.svg';
import { ReactComponent as RetweetSvg } from 'assets/icons/font-awesome/retweet-solid.svg';

import { REGEX } from 'constants';

const STATS_LIST = [
  {
    key: 'comment',
    icon: (
      <SvgIcon>
        <CommentSvg />
      </SvgIcon>
    ),
  },
  {
    key: 'retweet',
    icon: (
      <SvgIcon>
        <RetweetSvg />
      </SvgIcon>
    ),
  },
  {
    key: 'quote',
    icon: (
      <SvgIcon>
        <QuoteRightSvg />
      </SvgIcon>
    ),
  },
  {
    key: 'heart',
    icon: (
      <SvgIcon>
        <HeartSvg />
      </SvgIcon>
    ),
  },
];

const linkifyIt = linkify()
  .add('@', {
    validate: (text, pos, self) => {
      const tail = text.slice(pos);
      if (!self.re.twitter) {
        self.re.twitter = new RegExp(
          `^([a-zA-Z0-9_]){1,15}(?!_)(?=$|${self.re.src_ZPCc})`
        );
      }
      if (self.re.twitter.test(tail)) {
        if (pos >= 2 && tail[pos - 2] === '@') return false;
        return tail.match(self.re.twitter)[0].length;
      }
      return 0;
    },
    normalize(match) {
      match.url = `https://twitter.com/${match.url.replace(/^@/, '')}`;
    },
  })
  .add('#', {
    validate: (text, pos, self) => {
      const tail = text.slice(pos);
      if (!self.re.twitter) {
        self.re.twitter = new RegExp(
          `^([a-zA-Z0-9_]){1,15}(?!_)(?=$|${self.re.src_ZPCc})`
        );
      }
      if (self.re.twitter.test(tail)) {
        if (pos >= 2 && tail[pos - 2] === '#') return false;
        return tail.match(self.re.twitter)[0].length;
      }
      return 0;
    },
    normalize(match) {
      match.url = `https://twitter.com/hashtag/${match.url.replace(
        /^#/,
        ''
      )}?src=hashtag_click`;
    },
  })
  .add('$', {
    validate: (text, pos, self) => {
      const tail = text.slice(pos);
      if (!self.re.coin) {
        self.re.coin = /^([a-zA-Z]){1,15}/;
      }
      if (self.re.coin.test(tail)) {
        if (pos >= 2 && tail[pos - 2] === '$') return false;
        return tail.match(self.re.coin)[0].length;
      }
      return 0;
    },
    normalize(match) {
      match.url = `https://twitter.com/search?q=%24${match.url.replace(
        /^$/,
        ''
      )}&src=cashtag_click`;
    },
  });

const getContentElements = (content, item) => {
  const elements = [];
  const matches = linkifyIt.match(content);
  if (matches?.length > 0) {
    let currIndex = 0;
    matches.forEach((match, idx) => {
      const { index, lastIndex } = match;
      const textBeforeUrl = truncate(content.slice(currIndex, index), {
        length: 320,
        omission: '... ',
        separator: ' ',
      });
      const url = content
        .slice(index, lastIndex)
        .replace(REGEX.ctrlCharactersRegex, '');
      elements.push({
        element: textBeforeUrl,
        id: `${item.id}-${idx}-text`,
      });
      elements.push({
        element: (
          <Link
            href={
              !match.schema && match.raw.endsWith('…')
                ? item.url
                : match.url.replace('nitter', 'twitter')
            }
            rel="noopener"
            target="_blank"
            color="info.main"
            underline="hover"
            onClick={(e) => e.stopPropagation()}
          >
            {url.replace('nitter', 'twitter')}
          </Link>
        ),
        id: `${item.id}-${index}-${lastIndex}-url`,
      });
      currIndex = lastIndex;
    });
  } else
    elements.push({
      element: truncate(content, {
        length: 320,
        omission: '... ',
        separator: ' ',
      }),
      id: `${item.id}-text`,
    });

  return elements;
};

export default function SocMedPostList({ filters, timezone, onUnreadData }) {
  const dispatch = useDispatch();
  const { t } = useTranslation();

  const theme = useTheme();

  const [filteredPostList, setFilteredPostList] = useState([]);
  const [latestPostList, setLatestPostList] = useState([]);
  const [postList, setPostList] = useState([]);

  const [page, setPage] = useState();
  const [startTime, setStartTime] = useState();
  const [endTime, setEndTime] = useState();

  const { data: latestPosts, isLoading } = useGetSocialMediaPostsQuery(
    {},
    { pollingInterval: 1000 * 60, skip: filters?.startTime && filters?.endTime }
  );
  const { data: filteredPosts, isUninitialized: isFilteredPostsUninitialized } =
    useGetSocialMediaPostsQuery(
      { page, startTime, endTime, timezone },
      { skip: !(page || (startTime && endTime)) }
    );

  useEffect(() => {
    setStartTime(filters?.startTime);
    setEndTime(filters?.endTime);

    setPage();

    setLatestPostList([]);
    setFilteredPostList([]);
  }, [filters?.startTime, filters?.endTime]);

  useEffect(() => {
    setLatestPostList((state) => {
      const latest = differenceBy(latestPosts?.results, state, 'id');
      return [...latest, ...state].map((item) => {
        const { content } = item;
        const elements = getContentElements(content, item);

        return { ...item, elements };
      });
    });
  }, [latestPosts?.results]);

  useEffect(() => {
    setFilteredPostList((state) =>
      state.concat(filteredPosts?.results || []).map((item) => {
        const { content } = item;
        const elements = getContentElements(content, item);

        return { ...item, elements };
      })
    );
  }, [filteredPosts]);

  useEffect(() => {
    if (filters?.search.length)
      setPostList(
        matchSorter(
          uniqBy([...latestPostList, ...filteredPostList], 'id'),
          filters?.search.join(' '),
          {
            keys: ['name', 'username', 'content'],
            threshold: matchSorter.rankings.WORD_STARTS_WITH,
          }
        )
      );
    else setPostList(uniqBy([...latestPostList, ...filteredPostList], 'id'));
  }, [filteredPostList, latestPostList, filters?.search]);

  useEffect(() => {
    if (latestPostList.length)
      onUnreadData(latestPostList.length - (latestPosts?.results?.length || 0));
  }, [latestPosts?.results, latestPostList]);

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

  return (
    <>
      {postList.length === 0 ? (
        <Typography
          align="center"
          variant="h6"
          sx={{ color: 'secondary.main', fontStyle: 'italic' }}
        >
          {t('No posts found.')}
        </Typography>
      ) : (
        <List>
          {postList?.map((item) => (
            <Fragment key={item.id}>
              <ListItem
                alignItems="flex-start"
                // onClick={() => window.open(item.url, '_blank', 'noreferrer')}
                // sx={{ cursor: 'pointer' }}
              >
                <ListItemAvatar>
                  <Avatar alt={item.name} src={item.extra_data?.avatar} />
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Link
                      href={item.url}
                      rel="noopener"
                      target="_blank"
                      color="text.primary"
                      underline="none"
                    >
                      <Typography component="span" sx={{ fontWeight: 700 }}>
                        {item.name}
                      </Typography>
                      <Typography
                        component="small"
                        color="text.secondary"
                        sx={{ ml: 0.5 }}
                      >
                        {item.username}
                      </Typography>
                      {item.extra_data?.verified && (
                        <CheckCircleRoundedIcon
                          color="twitter"
                          sx={{ fontSize: 14, ml: 0.5 }}
                        />
                      )}
                      <Typography
                        component="small"
                        variant="subtitle"
                        color="grey.600"
                        sx={{ ml: 1 }}
                      >
                        {DateTime.fromISO(item.datetime).toLocaleString(
                          DateTime.DATETIME_MED
                        )}
                      </Typography>
                    </Link>
                  }
                  secondary={
                    <>
                      <Typography
                        gutterBottom
                        component="div"
                        color="text.secondary"
                        onClick={() =>
                          window.open(item.url, '_blank', 'noreferrer')
                        }
                        sx={{
                          cursor: 'pointer',
                          display: 'inline',
                          fontSize: 16,
                          whiteSpace: 'pre-line',
                        }}
                      >
                        {item.elements?.map((el) => (
                          <Fragment key={el.id}>{el.element}</Fragment>
                        ))}
                      </Typography>
                      {(item.extra_data?.attachments?.gallery ||
                        item.extra_data?.attachments?.video) && (
                        <Stack
                          useFlexGap
                          direction="row"
                          flexWrap="wrap"
                          spacing={0.5}
                          onClick={() =>
                            window.open(item.url, '_blank', 'noreferrer')
                          }
                          sx={{
                            cursor: 'pointer',
                            mb: 2,
                            width: { xs: 180, md: 500 },
                          }}
                        >
                          {[
                            ...(item.extra_data.attachments?.gallery || []),
                            ...(item.extra_data.attachments?.video || []),
                          ]?.map((img) => (
                            <Box
                              key={img}
                              component="img"
                              alt={img}
                              src={img}
                              height={180}
                              // width={320}
                              sx={{
                                borderRadius: 1,
                                objectFit: 'cover',
                                width: { xs: 80, md: 240 },
                              }}
                            />
                          ))}
                        </Stack>
                      )}
                      {item.extra_data?.quote?.url && (
                        <Box
                          sx={{
                            pl: 2,
                            borderLeft: `5px ${alpha(
                              theme.palette.grey['300'],
                              0.25
                            )} solid`,
                            borderRadius: 1,
                          }}
                        >
                          <LinkPreview
                            url={`${item.extra_data?.quote?.url.replace(
                              'x.com',
                              'nitter.net'
                            )}#m`}
                            rawUrl={item.extra_data.quote.url}
                          />
                        </Box>
                      )}
                      <Stack direction="row" spacing={2} mt={1}>
                        {STATS_LIST.map((stat) => (
                          <Stack
                            key={stat.key}
                            direction="row"
                            alignItems="center"
                            onClick={() =>
                              window.open(item.url, '_blank', 'noreferrer')
                            }
                          >
                            <SvgIcon
                              sx={{
                                cursor: 'pointer',
                                fontSize: { xs: 14, md: 16 },
                                mr: 1,
                              }}
                            >
                              {stat.icon}
                            </SvgIcon>
                            {formatShortNumber(
                              item.extra_data?.stats?.[`${stat.key}_count`]
                            )}
                          </Stack>
                        ))}
                      </Stack>
                    </>
                  }
                  secondaryTypographyProps={{
                    component: 'div',
                    paragraph: false,
                  }}
                />
                <IconButton
                  onClick={(e) => {
                    e.stopPropagation();
                    copy(item.url);
                    dispatch(
                      setSnackbar({
                        message: t(
                          "The URL to {{username}}'s post has been copied to clipboard.",
                          { username: `${item.username}` }
                        ),
                        snackbarProps: { autoHideDuration: 1500, open: true },
                        alertProps: { severity: 'success' },
                      })
                    );
                  }}
                >
                  <ShareRoundedIcon />
                </IconButton>
              </ListItem>
              <Divider variant="inset" component="li" />
            </Fragment>
          ))}
        </List>
      )}
      {((isFilteredPostsUninitialized && postList.length > 0) ||
        filteredPosts?.nextPage) && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
          <Button
            color="info"
            onClick={() => setPage(filteredPosts?.nextPage || 2)}
            sx={{ fontStyle: 'italic', my: 3, px: 5 }}
          >
            {t('Load more posts...')}
          </Button>
        </Box>
      )}
    </>
  );
}
