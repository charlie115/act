import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ListSubheader from '@mui/material/ListSubheader';
import Menu from '@mui/material/Menu';
import MenuList from '@mui/material/MenuList';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import SvgIcon from '@mui/material/SvgIcon';

import BookmarkAddIcon from '@mui/icons-material/BookmarkAdd';
import BookmarkRemoveIcon from '@mui/icons-material/BookmarkRemove';
import MenuIcon from '@mui/icons-material/Menu';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import PushPinIcon from '@mui/icons-material/PushPin';
import PushPinOutlinedIcon from '@mui/icons-material/PushPinOutlined';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

import { useDispatch, useSelector } from 'react-redux';
import { toggleBookmarkMarketCodePair } from 'redux/reducers/home';

import { useTranslation } from 'react-i18next';

import AnimatedClick from 'components/AnimatedClick';
import DropdownMenu from 'components/DropdownMenu';

import { MARKET_CODE_LIST } from 'constants/lists';

function MarketCodeSelector({ onChange }) {
  const dispatch = useDispatch();

  const { i18n, t } = useTranslation();

  const [marketCodeList, setMarketCodeList] = useState([]);
  const [targetMarketCode, setTargetMarketCode] = useState(0);
  const [originMarketCode, setOriginMarketCode] = useState(5);
  const [targetAnchorEl, setTargetAnchorEl] = useState(null);
  const [originAnchorEl, setOriginAnchorEl] = useState(null);

  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);

  const [bookmarkedPairs, setBookmarkedPairs] = useState([]);
  const [isBookmarked, setIsBookmarked] = useState(false);

  const bookmarkedMarketCodePairs = useSelector(
    (state) => state.home.bookmarkedMarketCodePairs
  );

  const handleMenuClose = () => {
    setMenuOpen(false);
    setMenuAnchorEl(null);
  };

  useEffect(() => {
    if (onChange && marketCodeList.length > 0)
      onChange({
        targetMarketCode: marketCodeList[targetMarketCode].value,
        originMarketCode: marketCodeList[originMarketCode].value,
      });
  }, [targetMarketCode, originMarketCode, marketCodeList]);

  useEffect(() => {
    setMarketCodeList(
      MARKET_CODE_LIST.map((market, index) => ({
        ...market,
        index,
        label: market.getLabel(),
        icon: (
          <SvgIcon>
            <market.icon />
          </SvgIcon>
        ),
        // secondaryIcon: (
        //   <PushPinIcon
        //     onClick={(e) => {
        //       e.stopPropagation();
        //     }}
        //   />
        // ),
      }))
    );
  }, [i18n.language]);

  useEffect(() => {
    const selectedPair = bookmarkedMarketCodePairs.find(
      (pair) => pair[0] === targetMarketCode && pair[1] === originMarketCode
    );
    setIsBookmarked(!!selectedPair);
    setBookmarkedPairs(
      bookmarkedMarketCodePairs.filter(
        (pair) =>
          !(pair[0] === targetMarketCode && pair[1] === originMarketCode)
      )
    );
  }, [bookmarkedMarketCodePairs, targetMarketCode, originMarketCode]);

  return (
    <Stack
      direction="row"
      spacing={1}
      sx={{
        alignItems: 'center',
        flex: 0.9,
        mb: { xs: 3, md: 0 },
      }}
    >
      <MoreVertIcon
        onClick={(event) => {
          setMenuAnchorEl(event.currentTarget);
          setMenuOpen((state) => !state);
        }}
        sx={{ cursor: 'pointer', ':hover': { opacity: 0.7 } }}
      />
      <DropdownMenu
        options={marketCodeList}
        value={marketCodeList[targetMarketCode]}
        tooltipTitle={t('Base Market Code')}
        onSelectItem={(item) => {
          setTargetMarketCode(item.index);
          if (item.index === originMarketCode)
            setOriginMarketCode(
              item.index === marketCodeList.length - 1 ? 0 : item.index + 1
            );
        }}
        buttonStyle={{ justifyContent: 'start', px: 2 }}
        containerStyle={{ alignSelf: 'stretch', flex: 1.5 }}
      />
      <AnimatedClick
        animation="flipOutY"
        onClick={() => {
          setTargetAnchorEl(null);
          setOriginAnchorEl(null);
          setTargetMarketCode(originMarketCode);
          setOriginMarketCode(targetMarketCode);
        }}
        containerStyle={{
          zIndex: targetAnchorEl || originAnchorEl ? 1500 : null,
        }}
      >
        <SyncAltIcon
          color="secondary"
          fontSize="small"
          sx={{ cursor: 'pointer' }}
        />
      </AnimatedClick>
      <DropdownMenu
        options={marketCodeList}
        value={marketCodeList[originMarketCode]}
        disabledValue={marketCodeList[targetMarketCode]}
        tooltipTitle={t('Origin Market Code')}
        onSelectItem={(item) => setOriginMarketCode(item.index)}
        buttonStyle={{ justifyContent: 'start', px: 2 }}
        containerStyle={{ alignSelf: 'stretch', flex: 1.5 }}
      />
      <Menu
        id="market-code-selector-menu"
        aria-controls={menuOpen ? 'market-code-selector-menu' : undefined}
        aria-expanded={menuOpen ? 'true' : undefined}
        aria-haspopup="true"
        anchorEl={menuAnchorEl}
        autoFocus={false}
        open={menuOpen}
        onClose={handleMenuClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <MenuItem disabled>{t('Currently Selected Pair')}</MenuItem>
        <ListItem
          secondaryAction={
            <IconButton
              edge="end"
              aria-label="bookmark"
              onClick={() =>
                dispatch(
                  toggleBookmarkMarketCodePair([
                    targetMarketCode,
                    originMarketCode,
                  ])
                )
              }
            >
              {isBookmarked ? (
                <BookmarkRemoveIcon color="accent" />
              ) : (
                <BookmarkAddIcon />
              )}
            </IconButton>
          }
          sx={{ bgcolor: 'primary.main' }}
        >
          {marketCodeList[targetMarketCode]?.label}
          <SyncAltIcon color="secondary" fontSize="small" sx={{ mx: 1 }} />
          {marketCodeList[originMarketCode]?.label}
        </ListItem>
        <Divider />
        <MenuItem disabled>{t('Bookmarked Pairs')}</MenuItem>
        {bookmarkedPairs.map((pair) => (
          <ListItem
            key={pair.join()}
            onClick={() => {
              setTargetMarketCode(pair[0]);
              setOriginMarketCode(pair[1]);
              handleMenuClose();
            }}
            secondaryAction={
              <IconButton
                edge="end"
                aria-label="bookmark"
                onClick={(e) => {
                  e.stopPropagation();
                  dispatch(toggleBookmarkMarketCodePair([pair[0], pair[1]]));
                }}
              >
                <BookmarkRemoveIcon color="accent" />
              </IconButton>
            }
            sx={{ cursor: 'pointer', ':hover': { bgcolor: 'primary.main' } }}
          >
            {marketCodeList[pair[0]]?.label}
            <SyncAltIcon color="secondary" fontSize="small" sx={{ mx: 1 }} />
            {marketCodeList[pair[1]]?.label}
          </ListItem>
        ))}
      </Menu>
    </Stack>
  );
}

export default React.memo(MarketCodeSelector);
