import React, { useEffect, useRef } from 'react';

import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';

import { useSelector } from 'react-redux';

import useExternalScript from 'hooks/useExternalScript';

import { TRADING_VIEW_TICKER_SYMBOLS } from 'constants/lists';

const TICKER_CONFIG = {
  isTransparent: true,
  showSymbolLogo: true,
};

export default function TickerWidget({ isVisible }) {
  const tickerRef = useRef();

  const currentLanguage = useSelector((state) => state.app.language);
  const currentTheme = useSelector((state) => state.app.theme);

  const script = useExternalScript(
    'https://s3.tradingview.com/external-embedding/embed-widget-tickers.js',
    {
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

  useEffect(() => {
    tickerRef.current.appendChild(script.current);
    return () => {
      while (tickerRef?.current?.firstChild)
        tickerRef?.current?.removeChild(tickerRef?.current?.firstChild);
    };
  }, [currentLanguage, currentTheme]);

  return (
    <Box
      component={Paper}
      sx={{ display: isVisible ? 'block' : 'none', mb: 1 }}
    >
      <div ref={tickerRef} className="tradingview-widget-container" />
      <div className="tradingview-widget-copyright" />
    </Box>
  );
}
