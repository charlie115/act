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
  Container
} from '@mui/material';

import { useTheme } from '@mui/material/styles';
import { useSelector } from 'react-redux';
import { DateTime } from 'luxon';
import { Trans, useTranslation } from 'react-i18next';

import PersonIcon from '@mui/icons-material/Person';
import AlternateEmailIcon from '@mui/icons-material/AlternateEmail';
import GoogleIcon from '@mui/icons-material/Google';
import DomainVerificationIcon from '@mui/icons-material/DomainVerification';
import TelegramIcon from '@mui/icons-material/Telegram';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';

import { useGetReferralsQuery, usePostReferralMutation } from 'redux/api/drf/referral';
import TelegramLoginButton from 'components/TelegramLoginButton';
import DepositBalance from 'components/DepositBalance';
import useGlobalSnackbar from 'hooks/useGlobalSnackbar';

export default function MyPage() {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigate = useNavigate();

  const { user, telegramBot } = useSelector((state) => state.auth);
  const { openSnackbar } = useGlobalSnackbar();

  // Fetch the user's referral data
  const { data: referrals = [], refetch: refetchReferrals } = useGetReferralsQuery();
  const [postReferral, { isLoading: postingReferral }] = usePostReferralMutation();

  const [referralCodeInput, setReferralCodeInput] = useState('');

  const handleReferralSubmit = async () => {
    try {
      await postReferral({ referral_code: referralCodeInput }).unwrap();
      openSnackbar(t('Referral code registered successfully!'), { variant: 'success' });
      setReferralCodeInput('');
      refetchReferrals();
    } catch (error) {
      console.error('Failed to register referral code', error);
      const errorMessage = error.data?.message || t('Failed to register referral code.');
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
              subheader={t('Name')}
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
            </CardContent>

            {telegramBot && (
              <>
                <Divider />
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <TelegramIcon sx={{ mr: 1, color: theme.palette.telegram.main }} />
                    <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {t('Telegram Integration')}
                    </Typography>
                  </Box>
                  <Stack spacing={2}>
                    <TelegramLoginButton buttonId="telegram-mypage-button" />
                    {!(telegramBot && !user?.telegram_chat_id) && (
                      <Typography variant="body1">
                        <Trans>
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
                      </Typography>
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