import React from 'react';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';

import { DateTime } from 'luxon';

import Countdown from 'react-countdown';

import formatIntlNumber from 'utils/formatIntlNumber';
import i18n from 'configs/i18n';

function FundingRate({ diff, fundingTime, value, decimal = 3, isMobile, fundingIntervalHours, sx }) {
  // Map funding interval hours to colors
  const getBadgeColor = (hours) => {
    switch (hours) {
      case 1:
        return 'success.main'; // Green for 1h (most frequent)
      case 2:
        return 'info.main'; // Blue for 2h
      case 4:
        return 'warning.main'; // Orange for 4h
      case 8:
        return 'secondary.main'; // Purple for 8h (least frequent)
      default:
        return 'primary.main'; // Default blue for any other value
    }
  };

  return (
    <>
      <Stack direction="row" spacing={0.5} alignItems="center">
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
        {fundingIntervalHours != null && (
          <Box
            component="span"
            sx={{
              fontSize: { xs: 7, sm: 9 },
              fontWeight: 700,
              color: 'white',
              bgcolor: getBadgeColor(fundingIntervalHours),
              borderRadius: '4px',
              px: 0.5,
              py: 0.25,
              lineHeight: 1,
              opacity: 0.85,
            }}
          >
            {fundingIntervalHours}h
          </Box>
        )}
      </Stack>
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
