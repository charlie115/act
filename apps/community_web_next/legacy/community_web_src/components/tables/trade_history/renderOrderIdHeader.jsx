import React from 'react';

import Box from '@mui/material/Box';

import i18n from 'configs/i18n';

import { MARKET_CODE_LIST } from 'constants/lists';

export default function renderOrderIdHeader({ column, table }) {
  const { marketCodes } = table.options.meta;
  const marketCode = MARKET_CODE_LIST.find(
    (o) =>
      o.value ===
      (column.id === 'target_order_id'
        ? marketCodes?.targetMarketCode
        : marketCodes?.originMarketCode)
  );
  return (
    <>
      <Box
        component="img"
        src={marketCode.icon}
        alt={marketCode.label}
        sx={{
          height: { xs: 8, sm: 10, md: 12 },
          width: { xs: 8, sm: 10, md: 12 },
        }}
      />{' '}
      {i18n.t('Order ID')}
    </>
  );
}
