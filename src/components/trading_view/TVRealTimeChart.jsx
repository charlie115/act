/* eslint-disable new-cap */
/* eslint-disable no-new */
import React, { useEffect } from 'react';
import Box from '@mui/material/Box';

import { useSelector } from 'react-redux';

import useExternalScript from 'hooks/useExternalScript';

export default function TVRealTimeChart({
  containerId,
  symbol,
  widgetOptions = {},
}) {
  const currentTheme = useSelector((state) => state.app.theme);

  const TradingView = useExternalScript(
    'https://s3.tradingview.com/tv.js',
    {
      name: 'TradingView',
      id: 'trading-view-chart',
    },
    [symbol]
  );

  useEffect(() => {
    if (TradingView) {
      new TradingView.widget({
        width: '100%',
        height: 400,
        interval: '1',
        timezone: 'Etc/UTC',
        style: '1',
        locale: 'kr',
        enable_publishing: false,
        hide_side_toolbar: false,
        allow_symbol_change: false,
        ...widgetOptions,
        container_id: containerId,
        symbol,
        theme: currentTheme,
      });
    }
  }, [currentTheme, symbol, TradingView]);

  return (
    <Box>
      <div className="tradingview-widget-container">
        <div id={containerId} />
        <div className="tradingview-widget-copyright" />
      </div>
    </Box>
  );
}
