import React from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

import { useTranslation } from 'react-i18next';

import AlarmSupportBotSettings from 'components/AlarmSupportBotSettings';
import TradeSupportBotSettings from 'components/TradeSupportBotSettings';

export default function BotSettings({
  marketCodeSelectorRef,
  marketCodeCombination,
}) {
  const { t } = useTranslation();

  if (!marketCodeCombination || marketCodeCombination.value === 'ALL')
    return (
      <Box display="flex" alignItems="center" justifyContent="center">
        <Button
          color="secondary"
          onClick={() => marketCodeSelectorRef.current.toggle()}
          sx={{ borderBottom: 1, borderRadius: 0, textAlign: 'center' }}
        >
          {t('Please select a specific market combination')}
        </Button>
      </Box>
    );

  if (marketCodeCombination?.tradeSupport)
    return (
      <TradeSupportBotSettings
        marketCodeSelectorRef={marketCodeSelectorRef}
        marketCodeCombination={marketCodeCombination}
      />
    );
  return (
    <AlarmSupportBotSettings
      marketCodeSelectorRef={marketCodeSelectorRef}
      marketCodeCombination={marketCodeCombination}
    />
  );
}
