import React, { useEffect, useState } from 'react';

import Button from '@mui/material/Button';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import SvgIcon from '@mui/material/SvgIcon';
import Tooltip from '@mui/material/Tooltip';

import SyncAltIcon from '@mui/icons-material/SyncAlt';

import { useTranslation } from 'react-i18next';

import isNumber from 'lodash/isNumber';

import AnimatedClick from 'components/AnimatedClick';

import { MARKETS } from 'constants/lists';

function MarketExchangeSelector({ onChange }) {
  const { i18n } = useTranslation();

  const [markets, setMarkets] = useState([]);

  const [baseMarket, setBaseMarket] = useState(0);
  const [compareMarket, setCompareMarket] = useState(2);

  const [baseAnchorEl, setBaseAnchorEl] = useState(null);
  const [compareAnchorEl, setCompareAnchorEl] = useState(null);

  useEffect(() => {
    if (onChange && markets.length > 0)
      onChange({
        baseMarket: markets[baseMarket].value,
        compareMarket: markets[compareMarket].value,
      });
  }, [baseMarket, compareMarket, markets]);

  useEffect(() => {
    setMarkets(
      MARKETS.map((market) => ({
        label: market.getLabel(),
        ...market,
      }))
    );
  }, [i18n.language]);

  const BaseIcon = markets[baseMarket]?.icon || 'div';
  const CompareIcon = markets[compareMarket]?.icon || 'div';

  return (
    <Stack
      direction="row"
      spacing={2}
      sx={{
        alignItems: 'center',
        flex: 0.9,
        mb: { xs: 3, md: 0 },
      }}
    >
      <Tooltip title="Base Exchange">
        <Button
          onClick={(e) => {
            setBaseAnchorEl(e.currentTarget);
            setCompareAnchorEl(null);
          }}
          size="large"
          variant="outlined"
          startIcon={
            <SvgIcon>
              <BaseIcon />
            </SvgIcon>
          }
          sx={{
            alignSelf: 'stretch',
            justifyContent: 'start',
            flex: 1.5,
            px: 2,
            zIndex: compareAnchorEl ? 10001 : null,
          }}
        >
          {markets[baseMarket]?.label}
        </Button>
      </Tooltip>
      <MarketMenu
        anchorEl={baseAnchorEl}
        markets={markets}
        selectedIdx={baseMarket}
        onClick={(idx) => {
          setBaseMarket(idx);
          setBaseAnchorEl(null);

          if (idx === compareMarket)
            setCompareMarket(idx === markets.length - 1 ? 0 : idx + 1);
        }}
        onClose={() => setBaseAnchorEl(null)}
      />
      <AnimatedClick
        animation="flipOutY"
        onClick={() => {
          setBaseAnchorEl(null);
          setCompareAnchorEl(null);
          setBaseMarket(compareMarket);
          setCompareMarket(baseMarket);
        }}
        containerStyle={{
          zIndex: baseAnchorEl || compareAnchorEl ? 1500 : null,
        }}
      >
        <SyncAltIcon
          color="secondary"
          fontSize="small"
          sx={{ cursor: 'pointer' }}
        />
      </AnimatedClick>
      <Button
        onClick={(e) => {
          setCompareAnchorEl(e.currentTarget);
          setBaseAnchorEl(null);
        }}
        size="large"
        variant="outlined"
        startIcon={
          <SvgIcon>
            <CompareIcon />
          </SvgIcon>
        }
        sx={{
          alignSelf: 'stretch',
          justifyContent: 'start',
          flex: 1.5,
          px: 2,
          zIndex: baseAnchorEl ? 10001 : null,
        }}
      >
        {markets[compareMarket]?.label}
      </Button>
      <MarketMenu
        anchorEl={compareAnchorEl}
        markets={markets}
        disabledIdx={baseMarket}
        selectedIdx={compareMarket}
        onClick={(idx) => {
          setCompareMarket(idx);
          setCompareAnchorEl(null);
        }}
        onClose={() => setCompareAnchorEl(null)}
      />
    </Stack>
  );
}

function MarketMenu({
  anchorEl,
  markets,
  disabledIdx,
  selectedIdx,
  onClick,
  onClose,
}) {
  return (
    <Menu anchorEl={anchorEl} open={!!anchorEl} onClose={onClose}>
      {markets.map((item, idx) => (
        <MenuItem
          key={item.value}
          disabled={isNumber(disabledIdx) && idx === disabledIdx}
          selected={idx === selectedIdx}
          onClick={() => onClick(idx)}
        >
          <ListItemIcon>
            <SvgIcon>
              <item.icon />
            </SvgIcon>
          </ListItemIcon>
          <ListItemText>{item.label}</ListItemText>
        </MenuItem>
      ))}
    </Menu>
  );
}

export default React.memo(MarketExchangeSelector);
