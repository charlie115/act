import React, { useEffect, useState } from 'react';

import Stack from '@mui/material/Stack';
import SvgIcon from '@mui/material/SvgIcon';

import SyncAltIcon from '@mui/icons-material/SyncAlt';

import { useTranslation } from 'react-i18next';

import AnimatedClick from 'components/AnimatedClick';
import DropdownMenu from 'components/DropdownMenu';

import { MARKET_EXCHANGES } from 'constants/lists';

function MarketExchangeSelector({ onChange }) {
  const { i18n, t } = useTranslation();

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
      MARKET_EXCHANGES.map((market, index) => ({
        ...market,
        index,
        label: market.getLabel(),
        icon: (
          <SvgIcon>
            <market.icon />
          </SvgIcon>
        ),
      }))
    );
  }, [i18n.language]);

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
      <DropdownMenu
        options={markets}
        value={markets[baseMarket]}
        tooltipTitle={t('Base Exchange')}
        onSelectItem={(item) => {
          setBaseMarket(item.index);
          if (item.index === compareMarket)
            setCompareMarket(
              item.index === markets.length - 1 ? 0 : item.index + 1
            );
        }}
        buttonStyle={{ justifyContent: 'start', px: 2 }}
        containerStyle={{ alignSelf: 'stretch', flex: 1.5 }}
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
      <DropdownMenu
        options={markets}
        value={markets[compareMarket]}
        disabledValue={markets[baseMarket]}
        onSelectItem={(item) => setCompareMarket(item.index)}
        buttonStyle={{ justifyContent: 'start', px: 2 }}
        containerStyle={{ alignSelf: 'stretch', flex: 1.5 }}
      />
    </Stack>
  );
}

export default React.memo(MarketExchangeSelector);
