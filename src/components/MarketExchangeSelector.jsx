import React, { useEffect, useState } from 'react';

import Stack from '@mui/material/Stack';
import SvgIcon from '@mui/material/SvgIcon';

import PushPinIcon from '@mui/icons-material/PushPin';
import PushPinOutlinedIcon from '@mui/icons-material/PushPinOutlined';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

import { useTranslation } from 'react-i18next';

import AnimatedClick from 'components/AnimatedClick';
import DropdownMenu from 'components/DropdownMenu';

import { MARKET_EXCHANGES } from 'constants/lists';

function MarketExchangeSelector({ onChange }) {
  const { i18n, t } = useTranslation();

  const [exchanges, setExchanges] = useState([]);

  const [baseExchange, setBaseExchange] = useState(0);
  const [compareExchange, setCompareExchange] = useState(5);

  const [baseAnchorEl, setBaseAnchorEl] = useState(null);
  const [compareAnchorEl, setCompareAnchorEl] = useState(null);

  useEffect(() => {
    if (onChange && exchanges.length > 0)
      onChange({
        baseExchange: exchanges[baseExchange].value,
        compareExchange: exchanges[compareExchange].value,
      });
  }, [baseExchange, compareExchange, exchanges]);

  useEffect(() => {
    setExchanges(
      MARKET_EXCHANGES.map((market, index) => ({
        ...market,
        index,
        label: market.getLabel(),
        icon: (
          <SvgIcon>
            <market.icon />
          </SvgIcon>
        ),
        secondaryIcon: (
          <PushPinIcon
            onClick={(e) => {
              e.stopPropagation();
              console.log('e: ', e);
            }}
          />
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
        options={exchanges}
        value={exchanges[baseExchange]}
        tooltipTitle={t('Base Exchange')}
        onSelectItem={(item) => {
          setBaseExchange(item.index);
          if (item.index === compareExchange)
            setCompareExchange(
              item.index === exchanges.length - 1 ? 0 : item.index + 1
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
          setBaseExchange(compareExchange);
          setCompareExchange(baseExchange);
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
        options={exchanges}
        value={exchanges[compareExchange]}
        disabledValue={exchanges[baseExchange]}
        tooltipTitle={t('Compare')}
        onSelectItem={(item) => setCompareExchange(item.index)}
        buttonStyle={{ justifyContent: 'start', px: 2 }}
        containerStyle={{ alignSelf: 'stretch', flex: 1.5 }}
      />
    </Stack>
  );
}

export default React.memo(MarketExchangeSelector);
