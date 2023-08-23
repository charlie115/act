/* eslint-disable new-cap */
/* eslint-disable no-new */
import React, { useEffect, useRef } from 'react';
import Box from '@mui/material/Box';

import { useSelector } from 'react-redux';

import useExternalScript from 'hooks/useExternalScript';

const TICKER_CONFIG = {
  symbols: [
    {
      description: '달러환율',
      proName: 'FX_IDC:USDKRW',
    },
    {
      description: '나스닥',
      proName: 'FOREXCOM:NSXUSD',
    },
    {
      description: 'S&P 500',
      proName: 'FOREXCOM:SPXUSD',
    },
    {
      description: 'BTC도미넌스',
      proName: 'CRYPTOCAP:BTC.D',
    },
    {
      description: '코스피',
      proName: 'KRX:KOSPI',
    },
    {
      // description: '코스닥',
      proName: 'KRX:KOSDAQ',
    },
  ],
  isTransparent: false,
  showSymbolLogo: true,
};

export default function TickerWidget() {
  const tickerRef = useRef();

  const currentLanguage = useSelector((state) => state.app.language);
  const currentTheme = useSelector((state) => state.app.theme);

  useExternalScript(
    'https://s3.tradingview.com/external-embedding/embed-widget-tickers.js',
    {
      attachToHeader: false,
      containerRef: tickerRef,
      scriptAttributes: {
        innerHTML: JSON.stringify({
          ...TICKER_CONFIG,
          colorTheme: currentTheme,
          locale: currentLanguage,
        }),
      },
    },
    [currentLanguage, currentTheme]
  );

  useEffect(() => {}, []);

  return (
    <Box sx={{ my: 1 }}>
      <div ref={tickerRef} className="tradingview-widget-container">
        <div className="tradingview-widget-container__widget" />
        <div className="tradingview-widget-copyright" />
      </div>
    </Box>
  );
}
