import React, { useMemo } from 'react';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt';

import { useTranslation } from 'react-i18next';

import orderBy from 'lodash/orderBy';

export default function ExchangeWalletNetworks({
  direction,
  targetMarketCode,
  originMarketCode,
  walletNetworks,
  walletStatus,
}) {
  const { t } = useTranslation();

  const targetNetworks = useMemo(
    () =>
      direction === 'all'
        ? walletStatus?.all
        : orderBy(
            walletNetworks?.[targetMarketCode.exchange]?.[
              direction === 'right' ? 'withdraw' : 'deposit'
            ],
            (o) => walletStatus?.[direction].includes(o)
          ),
    [walletNetworks, walletStatus]
  );
  const originNetworks = useMemo(
    () =>
      direction === 'all'
        ? walletStatus?.all
        : orderBy(
            walletNetworks?.[originMarketCode.exchange]?.[
              direction === 'right' ? 'deposit' : 'withdraw'
            ],
            (o) => walletStatus?.[direction].includes(o),
            'desc'
          ),
    [walletNetworks, walletStatus]
  );

  return (
    <Stack
      useFlexGap
      alignItems="center"
      direction="row"
      flexWrap="wrap"
      spacing={{ xs: 2, md: 3 }}
      sx={{ mb: { xs: 3, md: 3 } }}
    >
      {targetMarketCode.value.includes('SPOT') && (
        <Stack alignItems="center" direction="row" spacing={1}>
          <Box
            component="img"
            src={targetMarketCode.icon}
            alt={targetMarketCode.label}
            sx={{ height: { xs: 16, md: 18 }, width: { xs: 16, md: 18 } }}
          />
          <Typography sx={{ fontWeight: 700 }}>
            {targetMarketCode.getLabel()}{' '}
            {direction !== 'all' && (
              <Typography
                component="small"
                sx={{
                  alignSelf: 'flex-end',
                  fontSize: 10,
                  textTransform: 'uppercase',
                }}
              >
                ( {direction === 'left' ? t('Deposit') : t('Withdraw')} )
              </Typography>
            )}
          </Typography>
          {targetNetworks?.map((network) => (
            <Typography
              key={network}
              sx={{
                ...(walletStatus?.[direction].includes(network) ||
                direction === 'all'
                  ? { bgcolor: 'success.main' }
                  : { bgcolor: 'secondary.main', opacity: 0.5 }),
                fontWeight: 700,
                height: 20,
                px: 0.5,
                whiteSpace: 'nowrap',
              }}
            >
              {network}
            </Typography>
          ))}
        </Stack>
      )}
      {targetMarketCode.value.includes('SPOT') &&
        originMarketCode.value.includes('SPOT') &&
        targetMarketCode.exchange !== originMarketCode.exchange && (
          <ArrowRightAltIcon
            color={walletStatus?.[direction].length ? 'success' : 'error'}
            size="large"
            sx={direction === 'left' ? { transform: 'scaleX(-1)' } : null}
          />
        )}
      {originMarketCode.value.includes('SPOT') &&
        targetMarketCode.exchange !== originMarketCode.exchange && (
          <Stack alignItems="center" direction="row" spacing={1}>
            <Box
              component="img"
              src={originMarketCode.icon}
              alt={originMarketCode.label}
              sx={{ height: { xs: 16, md: 18 }, width: { xs: 16, md: 18 } }}
            />
            <Box sx={{ fontWeight: 700, mr: 5 }}>
              {originMarketCode.getLabel()}{' '}
              {direction !== 'all' && (
                <Typography
                  component="small"
                  sx={{
                    alignSelf: 'flex-end',
                    fontSize: 10,
                    textTransform: 'uppercase',
                  }}
                >
                  ( {direction === 'right' ? t('Deposit') : t('Withdraw')} )
                </Typography>
              )}
            </Box>
            {originNetworks?.map((network) => (
              <Typography
                key={network}
                sx={{
                  ...(walletStatus?.[direction].includes(network) ||
                  direction === 'all'
                    ? { bgcolor: 'success.main' }
                    : { bgcolor: 'secondary.main', opacity: 0.5 }),
                  fontWeight: 700,
                  height: 20,
                  px: 0.5,
                  whiteSpace: 'nowrap',
                }}
              >
                {network}
              </Typography>
            ))}
          </Stack>
        )}
    </Stack>
  );
}
