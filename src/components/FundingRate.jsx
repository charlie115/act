import React from 'react';

import Box from '@mui/material/Box';

import { DateTime } from 'luxon';

import Countdown from 'react-countdown';

import formatIntlNumber from 'utils/formatIntlNumber';
import i18n from 'configs/i18n';

function FundingRate({ diff, fundingTime, value, decimal = 3, isMobile, sx }) {
  return (
    <>
      <Box
        component="span"
        sx={{
          color: value < 0 ? 'error.main' : undefined,
          fontSize: { xs: 9, sm: 12 },
          ...sx,
        }}
      >
        {formatIntlNumber(value, decimal, 1)}
      </Box>
      {diff && (
        <Box sx={{ color: 'secondary.main', fontStyle: 'italic' }}>
          <Countdown
            date={DateTime.fromISO(fundingTime).toJSDate()}
            renderer={({ hours, minutes, seconds }) => (
              <Box sx={{ fontSize: isMobile ? '0.65em' : '0.75em' }}>
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
