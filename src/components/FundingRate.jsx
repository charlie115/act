import React from 'react';

import Box from '@mui/material/Box';

import { DateTime } from 'luxon';

import formatIntlNumber from 'utils/formatIntlNumber';

import Countdown from 'react-countdown';

import i18n from 'configs/i18n';

function FundingRate({ diff, fundingRate, value, isMobile }) {
  return (
    <>
      <Box
        component="span"
        sx={{
          color: value < 0 ? 'error.main' : undefined,
          fontSize: { xs: 11, sm: 12 },
        }}
      >
        {formatIntlNumber(value, 3, 1)} <small>%</small>
      </Box>
      {diff && (
        <Box sx={{ color: 'secondary.main', fontStyle: 'italic' }}>
          <Countdown
            date={DateTime.fromISO(fundingRate.funding_time).toJSDate()}
            renderer={({ hours, minutes, seconds }) => (
              <Box component="small">
                {isMobile
                  ? `${hours.toString().padStart(2, '0')}:${minutes
                      .toString()
                      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
                  : i18n.t('{{hours}}h {{minutes}}m {{seconds}}s left', {
                      hours,
                      minutes: `${minutes}`.padStart(2, '0'),
                      seconds: `${seconds}`.padStart(2, '0'),
                    })}
              </Box>
            )}
          />
        </Box>
      )}
    </>
  );
}

export default React.memo(FundingRate);
