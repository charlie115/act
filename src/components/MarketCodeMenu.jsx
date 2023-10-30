import React, { useEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import Divider from '@mui/material/Divider';
import Grid from '@mui/material/Grid';
import Grow from '@mui/material/Grow';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListSubheader from '@mui/material/ListSubheader';
import Paper from '@mui/material/Paper';
import Popper from '@mui/material/Popper';
import Stack from '@mui/material/Stack';
import SvgIcon from '@mui/material/SvgIcon';

import BookmarkIcon from '@mui/icons-material/Bookmark';
import BookmarkRemoveIcon from '@mui/icons-material/BookmarkRemove';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import SyncAltIcon from '@mui/icons-material/SyncAlt';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useDispatch, useSelector } from 'react-redux';
import {
  // selectBookmarkMarketCodePair,
  toggleBookmarkMarketCodes,
} from 'redux/reducers/home';

import { useTranslation } from 'react-i18next';

import { useGetMarketCodesQuery } from 'redux/api/drf/infocore';

import orderBy from 'lodash/orderBy';

import { MARKET_CODE_LIST } from 'constants/lists';

function MarketCodeMenu({ onChange }) {
  const anchorRef = useRef();

  const dispatch = useDispatch();

  const { i18n, t } = useTranslation();

  const bookmarkedMarketCodes = useSelector(
    (state) => state.home.bookmarkedMarketCodes
  );

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [open, setOpen] = useState(false);

  const [marketCodes, setMarketCodes] = useState();

  const [targetMarketCode, setTargetMarketCode] = useState(null);
  const [originMarketCode, setOriginMarketCode] = useState(null);

  const [marketCodeList, setMarketCodeList] = useState([]);
  const [targetMarketCodeList, setTargetMarketCodeList] = useState([]);
  const [originMarketCodeList, setOriginMarketCodeList] = useState([]);

  const [bookmarkAnchor, setBookmarkAnchor] = useState(null);
  const [bookmarkOpen, setBookmarkOpen] = useState(false);
  const [bookmarkedPairs, setBookmarkedPairs] = useState([]);

  const { data, isFetching, refetch } = useGetMarketCodesQuery();

  const handleClose = () => {
    if (!(targetMarketCode?.value && originMarketCode?.value)) return;
    setOpen(false);
  };
  const handleListKeyDown = (e) => {
    if (e.key === 'Escape') handleClose();
  };
  const handleToggle = () => (open ? handleClose() : setOpen(true));
  const handleBookmarkMenuClose = () => {
    setBookmarkOpen(false);
    setBookmarkAnchor(null);
  };

  useEffect(() => {
    if (marketCodes) onChange(marketCodes);
  }, [marketCodes]);

  useEffect(() => {
    if (targetMarketCode?.value && originMarketCode?.value)
      if (
        !marketCodes ||
        marketCodes?.targetMarketCode !== targetMarketCode.value ||
        marketCodes?.originMarketCode !== originMarketCode.value
      ) {
        setMarketCodes({
          targetMarketCode: targetMarketCode.value,
          originMarketCode: originMarketCode.value,
        });
      }
  }, [targetMarketCode, originMarketCode]);

  useEffect(() => {
    const originList =
      marketCodeList.filter((item) =>
        targetMarketCode?.origins.find((o) => o === item.value)
      ) || [];
    setOriginMarketCodeList(originList);
  }, [marketCodeList, targetMarketCode]);

  useEffect(() => {
    const targetList = marketCodeList.map((target) => ({
      ...target,
      disabled: !data?.[target.value],
      origins: data?.[target.value] || [],
    }));
    setTargetMarketCodeList(orderBy(targetList, 'disabled'));
    setTargetMarketCode(
      (state) => targetList?.[state?.index] || targetList?.[0]
    );
    setOriginMarketCode((state) => {
      if (state) return marketCodeList[state?.index] || {};
      return marketCodeList[5];
    });
  }, [data, isFetching, marketCodeList]);

  useEffect(() => {
    if (marketCodeList.length > 0) {
      const marketCodePairs = [];
      Object.entries(bookmarkedMarketCodes).forEach(([target, origins]) => {
        const targetObj = marketCodeList[target];
        Object.keys(origins)
          .filter((origin) => origins[origin])
          .forEach((origin) =>
            marketCodePairs.push([
              {
                ...targetObj,
                disabled: !data?.[targetObj.value],
                origins: data?.[targetObj.value] || [],
              },
              marketCodeList[origin],
            ])
          );
      });
      setBookmarkedPairs(marketCodePairs);
    }
  }, [bookmarkedMarketCodes, marketCodeList, data]);

  useEffect(() => {
    if (bookmarkedPairs.length === 0) {
      setBookmarkAnchor(null);
      setBookmarkOpen(false);
    }
  }, [bookmarkedPairs]);

  useEffect(() => {
    setMarketCodeList(
      MARKET_CODE_LIST.map((market, index) => ({
        index,
        label: market.getLabel(),
        value: market.value,
        icon: (
          <SvgIcon sx={{ fontSize: { xs: 10, sm: 12, md: 14 } }}>
            <market.icon />
          </SvgIcon>
        ),
      }))
    );
  }, [i18n.language]);

  useEffect(() => {
    if (!open) setOriginMarketCodeList([]);
    else refetch();
  }, [open]);

  if (!(targetMarketCode?.value || originMarketCode?.value)) return null;

  return (
    <Box>
      <Stack
        direction="row"
        spacing={{ xs: 0.25, sm: 1 }}
        sx={{ alignItems: 'center', flex: 0.9, mb: 0 }}
      >
        <Button
          fullWidth
          ref={anchorRef}
          aria-controls={open ? 'dropdown-menu' : undefined}
          aria-expanded={open ? 'true' : undefined}
          aria-haspopup="true"
          size={isMobile ? 'medium' : 'large'}
          variant="outlined"
          onClick={handleToggle}
          sx={{
            alignSelf: 'stretch',
            justifyContent: 'flex-start',
            fontSize: {
              xs: '0.5rem',
              sm: '0.65rem',
              md: '0.75rem',
              lg: '0.85rem',
            },
            height: '100%',
            minWidth: { xs: '40%', sm: 320 },
            px: { xs: 0.5, sm: 1, md: 1.5 },
            '& .MuiButton-startIcon>*:nth-of-type(1)': {
              fontSize: {
                xs: '0.65rem',
                sm: '0.75rem',
                md: '0.65rem',
                lg: '0.95rem',
              },
            },
          }}
        >
          <Stack
            direction="row"
            spacing={{ xs: 0.5, sm: 1 }}
            sx={{ alignItems: 'center' }}
          >
            {targetMarketCode?.icon}
            <Box>{targetMarketCode?.label}</Box>
            <SyncAltIcon color="secondary" fontSize="small" />
            {originMarketCode?.icon || <WarningAmberIcon color="secondary" />}
            <Box>
              {originMarketCode?.label || (
                <Box component="small" sx={{ color: 'secondary.main' }}>
                  {t('Please select origin exchange')}
                </Box>
              )}
            </Box>
          </Stack>
        </Button>
        {bookmarkedPairs.length > 0 && (
          <MoreVertIcon
            onClick={(event) => {
              setBookmarkAnchor(event.currentTarget);
              setBookmarkOpen((state) => !state);
            }}
            sx={{
              cursor: 'pointer',
              fontSize: '0.9rem',
              ':hover': { opacity: 0.7 },
            }}
          />
        )}
      </Stack>
      <Popper
        transition
        anchorEl={anchorRef.current}
        open={open}
        role={undefined}
        placement="bottom-start"
        popperOptions={{ strategy: 'fixed' }}
        sx={{ zIndex: 100 }}
      >
        {({ TransitionProps, placement }) => (
          <Grow
            {...TransitionProps}
            sx={{
              transformOrigin:
                placement === 'bottom-start' ? 'left top' : 'left bottom',
            }}
          >
            <Box component={Paper}>
              {isFetching && <LinearProgress />}
              <ClickAwayListener onClickAway={handleClose}>
                <Box sx={{ pb: 1 }}>
                  {!isFetching && (
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'end',
                      }}
                    >
                      <Button
                        size="small"
                        onClick={() => {
                          const target = marketCodeList.find(
                            (o) => o.value === marketCodes.targetMarketCode
                          );
                          setTargetMarketCode({
                            ...target,
                            disabled: !data?.[target.value],
                            origins: data?.[target.value] || [],
                          });
                          setOriginMarketCode(
                            marketCodeList.find(
                              (o) => o.value === marketCodes.originMarketCode
                            )
                          );
                          setOpen(false);
                        }}
                      >
                        {t('Cancel')}
                      </Button>
                    </Box>
                  )}
                  <Divider />
                  <Grid container>
                    <Grid item xs={isFetching ? 12 : 6}>
                      <List onKeyDown={handleListKeyDown} sx={{ py: 0 }}>
                        <ListSubheader
                          sx={{ bgcolor: 'inherit', lineHeight: 2 }}
                        >
                          {t('Base Exchange')}
                        </ListSubheader>
                        {targetMarketCodeList.map((target) => (
                          <ListItem disablePadding key={target.value}>
                            <ListItemButton
                              disabled={
                                target.disabled ||
                                (isFetching &&
                                  target.value !== targetMarketCode.value)
                              }
                              selected={target.value === targetMarketCode.value}
                              onClick={() => {
                                setTargetMarketCode(target);
                                if (
                                  !target.origins?.find(
                                    (o) => o === originMarketCode?.value
                                  )
                                )
                                  setOriginMarketCode({});
                              }}
                              sx={{ p: { xs: 0.25, sm: 1 } }}
                            >
                              <ListItemIcon
                                sx={{ minWidth: { xs: 15, sm: 20, md: 25 } }}
                              >
                                {target.icon}
                              </ListItemIcon>
                              <ListItemText
                                primary={target.label}
                                sx={{ fontSize: '1.15em', mr: 2 }}
                              />
                              <Box>
                                <SyncAltIcon
                                  color="secondary"
                                  fontSize="small"
                                />
                              </Box>
                            </ListItemButton>
                          </ListItem>
                        ))}
                      </List>
                    </Grid>
                    {!isFetching && (
                      <Grid
                        item
                        xs={6}
                        className="animate__animated animate__fadeIn"
                      >
                        <List onKeyDown={handleListKeyDown} sx={{ py: 0 }}>
                          <ListSubheader
                            sx={{ bgcolor: 'inherit', lineHeight: 2 }}
                          >
                            {t('Origin Exchange')}
                          </ListSubheader>
                          {originMarketCodeList?.map((origin) => (
                            <ListItem disablePadding key={origin.index}>
                              <ListItemButton
                                disabled={
                                  origin.disabled ||
                                  (isFetching &&
                                    origin.value !== originMarketCode?.value)
                                }
                                selected={
                                  origin.value === originMarketCode?.value
                                }
                                onClick={() => {
                                  setOriginMarketCode(origin);
                                  setOpen(false);
                                }}
                                sx={{ p: { xs: 0.25, sm: 1 } }}
                              >
                                <ListItemIcon
                                  sx={{ minWidth: { xs: 15, sm: 20, md: 25 } }}
                                >
                                  {origin.icon}
                                </ListItemIcon>
                                <ListItemText
                                  primary={origin.label}
                                  sx={{ fontSize: '1.15em', mr: 2 }}
                                />
                                <IconButton
                                  size="small"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    dispatch(
                                      toggleBookmarkMarketCodes({
                                        target: targetMarketCode.index,
                                        origin: origin.index,
                                      })
                                    );
                                  }}
                                  sx={{ p: 0.25 }}
                                >
                                  <BookmarkIcon
                                    color={
                                      bookmarkedMarketCodes[
                                        targetMarketCode.index
                                      ]?.[origin.index]
                                        ? 'accent'
                                        : 'secondary'
                                    }
                                    fontSize="small"
                                  />
                                </IconButton>
                              </ListItemButton>
                            </ListItem>
                          ))}
                        </List>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              </ClickAwayListener>
            </Box>
          </Grow>
        )}
      </Popper>
      <Menu
        id="market-code-bookmark-menu"
        aria-controls={bookmarkOpen ? 'market-code-bookmark-menu' : undefined}
        aria-expanded={bookmarkOpen ? 'true' : undefined}
        aria-haspopup="true"
        anchorEl={bookmarkAnchor}
        autoFocus={false}
        open={bookmarkOpen}
        onClose={handleBookmarkMenuClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <MenuItem disabled>{t('Bookmarked Pairs')}</MenuItem>
        {bookmarkedPairs.map(([target, origin]) => (
          <ListItem
            disablePadding
            key={`${target.index}-${origin.index}`}
            secondaryAction={
              <IconButton
                edge="end"
                aria-label="bookmark"
                onClick={(e) => {
                  e.stopPropagation();
                  dispatch(
                    toggleBookmarkMarketCodes({
                      target: target.index,
                      origin: origin.index,
                    })
                  );
                }}
              >
                <BookmarkRemoveIcon color="accent" />
              </IconButton>
            }
          >
            <ListItemButton
              disabled={target.disabled}
              selected={
                target.value === marketCodes?.targetMarketCode &&
                origin.value === marketCodes?.originMarketCode
              }
              onClick={() => {
                setTargetMarketCode(target);
                setOriginMarketCode(origin);
                handleBookmarkMenuClose();
              }}
              sx={{ fontSize: 11 }}
            >
              {target.label}
              <SyncAltIcon
                color="secondary"
                fontSize="medium"
                sx={{ px: 0.5 }}
              />
              {origin.label}
            </ListItemButton>
          </ListItem>
        ))}
      </Menu>
    </Box>
  );
}

export default React.memo(MarketCodeMenu);
