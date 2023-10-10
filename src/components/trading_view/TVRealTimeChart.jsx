/* eslint-disable new-cap */
/* eslint-disable no-new */
import React from 'react';

import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';

import { useSelector } from 'react-redux';

import useExternalScript from 'hooks/useExternalScript';

export default function TVRealTimeChart({
  containerId = 'tv-realtime-chart',
  symbol,
  widgetOptions = {},
}) {
  const currentLanguage = useSelector((state) => state.app.language);
  const currentTheme = useSelector((state) => state.app.theme);

  useExternalScript(
    'https://s3.tradingview.com/tv.js',
    {
      attachToHeader: true,
      id: 'trading-view-chart',
      onLoad: () => {
        if (window.TradingView) {
          new window.TradingView.widget({
            width: '100%',
            height: 400,
            interval: '1',
            timezone: 'Asia/Seoul',
            // timezone: 'Etc/UTC',
            style: '1',
            locale: currentLanguage === 'ko' ? 'kr' : currentLanguage,
            enable_publishing: false,
            hide_side_toolbar: false,
            allow_symbol_change: false,
            ...widgetOptions,
            container_id: containerId,
            symbol,
            theme: currentTheme,
          });
        }
      },
    },
    [currentLanguage, currentTheme, symbol]
  );

  return (
    <Box component={Paper} sx={{ mb: 1 }}>
      <div className="tradingview-widget-container">
        <div id={containerId} />
        <div className="tradingview-widget-copyright" />
      </div>
    </Box>
  );
}
