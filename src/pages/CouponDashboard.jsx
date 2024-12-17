import React, { useMemo } from 'react';
import {
  Box,
  CircularProgress,
  Container,
  Typography,
  Button,
  Paper,
  Stack
} from '@mui/material';

import { useTranslation } from 'react-i18next';
import { useSelector } from 'react-redux';
import { useGetCouponsQuery, useGetCouponRedemptionsQuery, useRedeemCouponMutation } from 'redux/api/drf/coupon';
import useGlobalSnackbar from 'hooks/useGlobalSnackbar';

export default function CouponDashboard() {
  const { t } = useTranslation();
  const { user } = useSelector((state) => state.auth);
  const { openSnackbar } = useGlobalSnackbar();

  const { data: coupons = [], isLoading: couponsLoading } = useGetCouponsQuery();
  const { data: redemptions = [], isLoading: redemptionsLoading, refetch: refetchRedemptions } = useGetCouponRedemptionsQuery();
  const [redeemCoupon, { isLoading: redeeming }] = useRedeemCouponMutation();

  // Create a set of redeemed coupon names for quick lookup
  const redeemedCouponNames = useMemo(
    () => new Set(redemptions.map((r) => r.coupon)),
    [redemptions]
  );

  const handleRedeem = async (couponName) => {
    try {
      await redeemCoupon({ name: couponName }).unwrap();
      await refetchRedemptions();
      openSnackbar(t('Coupon redeemed successfully!'), { variant: 'success' });
    } catch (error) {
      console.error('Failed to redeem coupon:', error);
      openSnackbar(t('Failed to redeem coupon'), { variant: 'error' });
    }
  };

  if (couponsLoading || redemptionsLoading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" sx={{ mb: 2 }}>
        {t('Coupon Dashboard')}
      </Typography>

      <Stack spacing={2}>
        {coupons.map((coupon) => {
          const isRedeemed = redeemedCouponNames.has(coupon.name);

          return (
            <Paper
              key={coupon.id}
              elevation={3}
              sx={{
                p: 2,
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
                opacity: isRedeemed ? 0.5 : 1,
                position: 'relative',
                borderRadius: '8px',
                '&::before, &::after': {
                  content: '""',
                  position: 'absolute',
                  top: '50%',
                  width: '20px',
                  height: '20px',
                  backgroundColor: 'white',
                  borderRadius: '50%',
                  transform: 'translateY(-50%)',
                  boxShadow: '0 0 0 1px rgba(0,0,0,0.1) inset',
                },
                '&::before': {
                  left: '-10px',
                },
                '&::after': {
                  right: '-10px',
                }
              }}
            >
              <Box>
                <Typography variant="h6">
                  {coupon.name} - {Number(coupon.amount).toFixed(0)}USDT
                </Typography> 
                {coupon.expires_at && (
                  <Typography variant="body2" color="text.secondary">
                    {t('Expires at')}: {new Date(coupon.expires_at).toLocaleString()}
                  </Typography>
                )}
              </Box>
              <Box>
                {isRedeemed ? (
                  <Button variant="contained" disabled>
                    {t('Used')}
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => handleRedeem(coupon.name)}
                    disabled={redeeming}
                  >
                    {t('Redeem')}
                  </Button>
                )}
              </Box>
            </Paper>
          );
        })}
      </Stack>
    </Container>
  );
}