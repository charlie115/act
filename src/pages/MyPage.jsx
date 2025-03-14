import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  Avatar,
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  Typography,
  Button,
  TextField,
  Stack,
  Container,
  Popover
} from '@mui/material';

import { useTheme } from '@mui/material/styles';
import { useSelector, useDispatch } from 'react-redux';
import { DateTime } from 'luxon';
import { Trans, useTranslation } from 'react-i18next';

import PersonIcon from '@mui/icons-material/Person';
import GoogleIcon from '@mui/icons-material/Google';
import DomainVerificationIcon from '@mui/icons-material/DomainVerification';
import TelegramIcon from '@mui/icons-material/Telegram';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import PercentIcon from '@mui/icons-material/Percent';
import LinkOffIcon from '@mui/icons-material/LinkOff';

import { useGetReferralsQuery, usePostReferralMutation } from 'redux/api/drf/referral';
import { useUnbindTelegramMutation } from 'redux/api/drf/user';
import TelegramLoginButton from 'components/TelegramLoginButton';
import DepositBalance from 'components/DepositBalance';
import useGlobalSnackbar from 'hooks/useGlobalSnackbar';
import { useGetUserFeeLevelQuery } from 'redux/api/drf/fee';

export default function MyPage() {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const { user, telegramBot } = useSelector((state) => state.auth);
  const { openSnackbar } = useGlobalSnackbar();

  // Fetch the user's referral data
  const { data: referrals = [], refetch: refetchReferrals } = useGetReferralsQuery();
  const [postReferral, { isLoading: postingReferral }] = usePostReferralMutation();

  // Fetch the user's fee level data
  const { data: feeLevelData, isLoading: feeLevelLoading } = useGetUserFeeLevelQuery();
  const feeLevel = feeLevelData?.results?.[0];

  // Unbind Telegram mutation
  const [unbindTelegram, { isLoading: isUnbinding }] = useUnbindTelegramMutation();

  const [referralCodeInput, setReferralCodeInput] = useState('');

  // For fee level popover
  const [feeLevelAnchorEl, setFeeLevelAnchorEl] = useState(null);
  const handleFeeLevelClick = (event) => {
    setFeeLevelAnchorEl(event.currentTarget);
  };
  const handleFeeLevelClose = () => {
    setFeeLevelAnchorEl(null);
  };
  const feeLevelPopoverOpen = Boolean(feeLevelAnchorEl);

  const handleReferralSubmit = async () => {
    try {
      await postReferral({ referral_code: referralCodeInput }).unwrap();
      openSnackbar(t('Referral code registered successfully!'), { variant: 'success' });
      setReferralCodeInput('');
      refetchReferrals();
    } catch (error) {
      const errorMessage = error.data?.message || t('Failed to register referral code.');
      openSnackbar(errorMessage, { variant: 'error' });
    }
  };

  // Handle unbind Telegram
  const handleUnbindTelegram = async () => {
    try {
      await unbindTelegram().unwrap();
      // Update auth state to reflect the change
      dispatch({ type: 'auth/updateUser', payload: { ...user, telegram_chat_id: null } });
      openSnackbar(t('Telegram connection removed successfully'), { variant: 'success' });
    } catch (error) {
      const errorMessage = error.data?.message || t('Failed to remove Telegram connection.');
      openSnackbar(errorMessage, { variant: 'error' });
    }
  };

  // Check if user already has a referral
  const hasReferral = referrals.length > 0;
  const referralInfo = hasReferral ? referrals[0] : null;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" sx={{ mb: 4, textAlign: 'center' }}>
        {t('My Page')}
      </Typography>

      <Grid container spacing={4} justifyContent="center">
        {/* Main Card containing all info */}
        <Grid item xs={12} md={8}>
          <Card elevation={3} sx={{ borderRadius: 2 }}>
            <CardHeader
              avatar={
                <Avatar
                  src={user?.profile?.picture}
                  alt={t('userFullName', {
                    firstName: user?.first_name,
                    lastName: user?.last_name,
                  })}
                  sx={{
                    bgcolor: user ? 'primary.main' : null,
                  }}
                />
              }
              titleTypographyProps={{ variant: 'h6', fontWeight: 'bold' }}
              title={t('userFullName', {
                firstName: user?.first_name,
                lastName: user?.last_name,
              })}
            />
            <Divider />
            <CardContent>
              {/* Register Referral Code Section */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
                  {t('Register Referral Code')}
                </Typography>
                {hasReferral ? (
                  <Typography variant="body1">
                    {t('You have been referred with code')}:{' '}
                    <strong>{referralInfo.referral_code}</strong>
                  </Typography>
                ) : (
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems="center">
                    <TextField
                      variant="outlined"
                      size="small"
                      fullWidth
                      placeholder={t('Enter referral code')}
                      value={referralCodeInput}
                      onChange={(e) => setReferralCodeInput(e.target.value)}
                    />
                    <Button
                      variant="contained"
                      color="primary"
                      disabled={!referralCodeInput || postingReferral}
                      onClick={handleReferralSubmit}
                    >
                      {t('Register')}
                    </Button>
                  </Stack>
                )}
              </Box>

              {/* Username */}
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PersonIcon sx={{ mr: 1 }} />
                <Typography variant="body1" sx={{ mr: 1, fontWeight: 600 }}>
                  {t('Username')}:
                </Typography>
                <Typography variant="body1">{user?.username}</Typography>
              </Box>

              {/* Email */}
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <GoogleIcon sx={{ mr: 1 }} />
                <Typography variant="body1" sx={{ mr: 1, fontWeight: 600 }}>
                  {t('E-mail')}:
                </Typography>
                <Typography variant="body1">{user?.email}</Typography>
              </Box>

              {/* Registration Date */}
              {user?.date_joined && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <DomainVerificationIcon sx={{ mr: 1 }} />
                  <Typography variant="body1" sx={{ mr: 1, fontWeight: 600 }}>
                    {t('Registration Date')}:
                  </Typography>
                  <Typography variant="body1">
                    {DateTime.fromISO(user.date_joined).toFormat('DDDD')}
                  </Typography>
                </Box>
              )}

              {/* Deposit Balance */}
              <Box
                onClick={() => navigate('/bot/deposit')}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  mb: 2,
                  cursor: 'pointer',
                  ':hover': { textDecoration: 'underline' },
                }}
              >
                <AccountBalanceWalletIcon sx={{ mr: 1 }} />
                <Typography variant="body1" sx={{ mr: 1, fontWeight: 600 }}>
                  {t('Deposit Balance')}:
                </Typography>
                <DepositBalance />
              </Box>

              {/* Fee level */}
              <Box 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  mb: 2,
                  cursor: 'pointer',
                  ':hover': { bgcolor: 'action.hover', borderRadius: 1 },
                }}
                onClick={handleFeeLevelClick}
              >
                <PercentIcon sx={{ mr: 1 }} />
                <Typography variant="body1" sx={{ mr: 1, fontWeight: 600 }}>
                  {t('Fee Level')}:
                </Typography>
                {feeLevelLoading ? (
                  <Typography variant="body1">{t('Loading...')}</Typography>
                ) : (
                  <Typography variant="body1">
                    {feeLevel ? `${feeLevel.fee_level} (${(feeLevel.fee_rate * 100).toFixed(1)}%)` : user?.fee_level || t('N/A')}
                  </Typography>
                )}
              </Box>
              
              {/* Fee Level Popover */}
              <Popover
                open={feeLevelPopoverOpen}
                anchorEl={feeLevelAnchorEl}
                onClose={handleFeeLevelClose}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'left',
                }}
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'left',
                }}
              >
                {feeLevel ? (
                  <Box sx={{ p: 2, maxWidth: 300 }}>
                    <Typography variant="h6" sx={{ mb: 1 }}>{t('Fee Level Details')}</Typography>
                    <Divider sx={{ mb: 2 }} />
                    
                    <Stack spacing={1.5}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">{t('Fee Level')}</Typography>
                        <Typography variant="body1" fontWeight="medium">{feeLevel.fee_level}</Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" color="text.secondary">{t('Fee Rate')}</Typography>
                        <Typography variant="body1" fontWeight="medium">{(feeLevel.fee_rate * 100).toFixed(1)}%</Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" color="text.secondary">{t('Realtime Total Paid Fee')}</Typography>
                        <Typography variant="body1" fontWeight="medium">{feeLevel.realtime_total_paid_fee.toFixed(2)} USDT</Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" color="text.secondary">{t('Required Fee to Next Level')}</Typography>
                        <Typography variant="body1" fontWeight="medium">{feeLevel.required_paid_fee_to_next_level.toFixed(2)} USDT</Typography>
                      </Box>

                    </Stack>
                  </Box>
                ) : (
                  <Box sx={{ p: 2 }}>
                    <Typography variant="body1">{t('No fee level data available')}</Typography>
                  </Box>
                )}
              </Popover>
            </CardContent>

            {telegramBot && (
              <>
                <Divider />
                <CardContent>
                  <Stack spacing={2} alignItems="center">
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <TelegramIcon sx={{ mr: 1, color: theme.palette.telegram.main }} />
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {user?.telegram_chat_id 
                          ? <Trans>
                              Connected to{' '}
                              <span
                                style={{
                                  color: theme.palette.telegram.main,
                                  fontWeight: 700,
                                }}
                              >
                                {{ telegramBot }}
                              </span>
                            </Trans>
                          : t('Telegram Integration')}
                      </Typography>
                    </Box>
                    
                    {/* Show login button if not connected, or unbind button if connected */}
                    {user?.telegram_chat_id ? (
                      <Button
                        variant="outlined"
                        color="error"
                        startIcon={<LinkOffIcon />}
                        onClick={handleUnbindTelegram}
                        disabled={isUnbinding}
                      >
                        {isUnbinding ? t('Disconnecting...') : t('Disconnect Telegram')}
                      </Button>
                    ) : (
                      <TelegramLoginButton buttonId="telegram-mypage-button" />
                    )}
                  </Stack>
                </CardContent>
              </>
            )}

          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}