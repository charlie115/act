import React from 'react';

import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';

import { useSelector } from 'react-redux';

import useScript from 'hooks/useScript';

import { TRADING_VIEW_TICKER_SYMBOLS } from 'constants/lists';

const TICKER_CONFIG = {
  isTransparent: true,
  showSymbolLogo: true,
  autosize: true,
};

export default function TickerWidget({ isVisible }) {
  const currentLanguage = useSelector((state) => state.app.language);
  const currentTheme = useSelector((state) => state.app.theme);

  useScript(
    // 'https://s3.tradingview.com/external-embedding/embed-widget-tickers.js',
    'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js',
    {
      nodeId: 'tv-ticker-widget',
      attributes: {
        innerHTML: JSON.stringify({
          ...TICKER_CONFIG,
          symbols: TRADING_VIEW_TICKER_SYMBOLS,
          colorTheme: currentTheme,
          locale: currentLanguage,
        }),
      },
    },
    [currentLanguage, currentTheme]
  );

  return (
    <Box
      component={Paper}
      sx={{ 
        display: isVisible ? 'block' : 'none', 
        mb: 1,
        '& .tradingview-widget-container': {
          display: 'flex',
          flexWrap: 'wrap',
          flexDirection: 'row',
          justifyContent: 'flex-start',
          overflowX: 'auto',
          width: '100%',
          // For mobile: force each ticker item to use 50% width so at least 2 items are visible.
          '& > div': {
            flex: { xs: '0 0 50%', sm: 'auto' },
            maxWidth: { xs: '50%', sm: 'none' },
          }
        }
      }}
    >
      <div id="tv-ticker-widget" className="tradingview-widget-container" />
      <div className="tradingview-widget-copyright" />
    </Box>
  );
}
