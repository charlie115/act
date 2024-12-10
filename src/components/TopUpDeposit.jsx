import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import LinearProgress from '@mui/material/LinearProgress';
import OutlinedInput from '@mui/material/OutlinedInput';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Stepper from '@mui/material/Stepper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import Countdown from 'react-countdown';

import { useLazyGetDepositBalanceQuery } from 'redux/api/drf/user';

import {
  useGetWalletAddressQuery,
  usePostWalletTransactionMutation,
} from 'redux/api/drf/wallet';

import QRCode from 'react-qr-code';

import { DateTime } from 'luxon';
import copy from 'copy-to-clipboard';

import { useTranslation } from 'react-i18next';
import i18n from 'configs/i18n';

import useCookie from 'hooks/useCookie';
import useGlobalSnackbar from 'hooks/useGlobalSnackbar';

import formatIntlNumber from 'utils/formatIntlNumber';

const STEPS = [
  {
    key: 'walletAddress',
    getLabel: () => i18n.t('Send cryptocurrency to our wallet'),
  },
  { key: 'CheckTransactions', getLabel: () => i18n.t('Check Transactions') },
  {
    key: 'balance',
    getLabel: () => i18n.t('Top-up complete!'),
  },
];

const COUNTDOWN_IN_SECONDS = 5;

export default function TopUpDeposit() {
  const { t } = useTranslation();
  const { user } = useSelector((state) => state.auth);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { openSnackbar } = useGlobalSnackbar();

  const { getCookie: getWalletAddress, setCookie: setWalletAddress } =
    useCookie('dpaddr');

  const { getCookie: getCountdown, setCookie: setCountdown } =
    useCookie('dpcntdwn');

  const [activeStep, setActiveStep] = useState(0);

  const [address, setAddress] = useState(getWalletAddress());
  const [amount, setAmount] = useState();
  const [balance, setBalance] = useState();

  const [message, setMessage] = useState();
  const [countdownDate, setCountdownDate] = useState();

  const [postDepositAmount, depositAmount] = usePostWalletTransactionMutation();
  const [getDepositBalance, depositBalance] = useLazyGetDepositBalanceQuery();

  const { data: depositAddress } = useGetWalletAddressQuery(
    user.uuid,
    { skip: activeStep !== 0 || !!address || !user?.uuid }
  );

  useEffect(() => {
    if (depositAddress?.address) {
      const cookieOptions = {};
      const expires = DateTime.now()
        .plus({ seconds: COUNTDOWN_IN_SECONDS })
        .toJSDate();
      cookieOptions.expires = expires;
      setWalletAddress(depositAddress.address, cookieOptions);
      setAddress(depositAddress.address);
    }
  }, [depositAddress]);

  useEffect(() => {
    if (depositBalance.isSuccess)
      setBalance(depositBalance.data?.results?.[0]?.balance);
  }, [depositBalance]);

  useEffect(() => {
    if (activeStep === 1 && getCountdown())
      setCountdownDate(DateTime.fromMillis(getCountdown()).toJSDate());

    setMessage();
  }, [activeStep]);

  return (
    <Box
      sx={{
        mx: 'auto',
        mt: { xs: 4, md: 0 },
        width: { xs: '100%', md: '50%' },
      }}
    >
      <Typography variant="h6" sx={{ mb: 4, textAlign: 'center' }}>
        {t('Top-up Deposit')}
      </Typography>
      <Stepper
        activeStep={activeStep}
        orientation={isMobile ? 'vertical' : 'horizontal'}
      >
        {STEPS.map((item) => (
          <Step key={item.key} completed={activeStep === 2}>
            <StepLabel>{item.getLabel()}</StepLabel>
          </Step>
        ))}
      </Stepper>
      <Box sx={{ p: 4 }}>
        {activeStep === 0 &&
          (address ? (
            <Grid container spacing={4}>
              <Grid item xs={12} md={7}>
                <Typography gutterBottom>
                  {t(
                    'Copy our wallet address in your exchange and make a crypto deposit. You should transact via TRC-20(TRX)!'
                  )}
                </Typography>
                <OutlinedInput
                  fullWidth
                  readOnly
                  size="small"
                  value={address}
                  endAdornment={
                    <InputAdornment position="end">
                      <IconButton
                        color="info"
                        edge="end"
                        onClick={() => {
                          copy(address);
                          openSnackbar(
                            t(
                              'The wallet address has been copied to clipboard.'
                            ),
                            {
                              alertProps: { severity: 'info' },
                              snackbarProps: { autoHideDuration: 1500 },
                            }
                          );
                        }}
                      >
                        <ContentCopyIcon />
                      </IconButton>
                    </InputAdornment>
                  }
                  sx={{ color: 'info.main' }}
                />
                {/* <Typography sx={{ mt: 4 }}>
                  {t('Or scan the QR code from your phone.')}
                </Typography> */}
              </Grid>
              <Grid item md display="flex" justifyContent="center">
                <Box
                  sx={{ bgcolor: 'white.main', maxWidth: 180, pt: 1, px: 1 }}
                >
                  <QRCode
                    value={address}
                    size={256}
                    style={{
                      height: 'auto',
                      maxWidth: '100%',
                      width: '100%',
                    }}
                    viewBox="0 0 256 256"
                  />
                </Box>
              </Grid>
            </Grid>
          ) : (
            <LinearProgress />
          ))}
        {activeStep === 1 && (
          <Box>
            <Typography sx={{ mb: 2 }}>
              {t(
                'Please click the button below to confirm your deposit after sending the cryptocurrency to our wallet'
              )}
            </Typography>
            {message && (
              <Typography sx={{ color: 'error.main', mt: 2 }}>
                {message}
              </Typography>
            )}
          </Box>
        )}
        {activeStep === 2 && (
          <Box display="flex" flexDirection="column" alignItems="center">
            <Typography sx={{ mb: 2 }}>{t('Deposit Complete!')}</Typography>
            <Box
              component={Paper}
              sx={{
                bgcolor: 'white.main',
                color: 'dark.main',
                p: 2,
              }}
            >
              <Typography
                gutterBottom
                sx={{
                  fontFamily: 'Monospace',
                  fontSize: 10,
                  fontWeight: 700,
                  mb: 2,
                  textAlign: 'center',
                }}
              >
                {/* {transactionId} */}
              </Typography>
              <Table
                sx={{
                  borderCollapse: 'collapse',
                  td: { border: 0, color: 'dark.main', py: 0 },
                }}
              >
                <TableBody>
                  <TableRow>
                    <TableCell>{t('Amount deposited')}</TableCell>
                    <TableCell>{formatIntlNumber(amount, 2, 2)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>{t('New balance')}</TableCell>
                    <TableCell>{formatIntlNumber(balance, 2, 2)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </Box>
          </Box>
        )}
        <Divider sx={{ my: 4 }} />
        {depositAmount.isLoading && <LinearProgress sx={{ mb: 4 }} />}
        <Stack
          direction="row"
          justifyContent={activeStep < 2 ? 'space-between' : 'flex-end'}
          spacing={1}
        >
          {activeStep < 2 && (
            <Button
              disabled={activeStep === 0}
              variant="outlined"
              onClick={() =>
                setActiveStep((prevActiveStep) => prevActiveStep - 1)
              }
            >
              {t('Back')}
            </Button>
          )}
          <Button
            disabled={
              (activeStep === 0 && !address) ||
              (activeStep === 1 &&
                // (!transactionId || depositAmount.isLoading)) ||
                (depositAmount.isLoading)) ||
              (activeStep > 0 && !!countdownDate)
            }
            size="large"
            variant="contained"
            color={activeStep === 2 ? 'success' : undefined}
            endIcon={activeStep === 2 ? <AddIcon /> : undefined}
            onClick={async () => {
              if (activeStep === 0) setActiveStep(1);
              if (activeStep === 1) {
                const cookieOptions = {};
                const expires = DateTime.now()
                  .plus({ seconds: COUNTDOWN_IN_SECONDS })
                  .toJSDate();
                const countdownDateTime = DateTime.now().plus({
                  seconds: COUNTDOWN_IN_SECONDS,
                });
                cookieOptions.expires = expires;
                try {
                  const result = await postDepositAmount({
                    user: user.uuid,
                    asset: "USDT",
                  }).unwrap();
                  if (result?.result) {
                    if (result.result.total_deposit_amount !== 0) {
                      setAmount(result.result.total_deposit_amount);
                      getDepositBalance();
                      setActiveStep(2);
                    }
                    else {
                      setMessage(t('The deposit has not yet been confirmed. Please check back later.'));
                    }
                  }

                  setCountdown(countdownDateTime.toMillis(), cookieOptions);
                  setCountdownDate(countdownDateTime.toJSDate());
                } catch (err) {
                  setCountdown(countdownDateTime.toMillis(), cookieOptions);
                  setCountdownDate(countdownDateTime.toJSDate());

                  if (
                    err?.data?.txid?.[0] ===
                    'This TXID has already been deposited.'
                  )
                    setMessage(t('This TXID has already been deposited.'));
                  else
                    setMessage(
                      t(
                        'The deposit for this TXID has not yet been confirmed. Depending on the network, it may take up to 5 minutes or more for your deposit to be reflected. Please check back later.'
                      )
                    );
                }
              }
              if (activeStep === 2) {
                setActiveStep(0);
                setMessage();

                setAmount();
                setBalance();
              }
            }}
          >
            {activeStep === 0 && t('Next')}
            {activeStep >= 1 &&
              (countdownDate ? (
                <Countdown
                  date={countdownDate}
                  intervalDelay={1000}
                  renderer={({ seconds }) =>
                    `${
                      activeStep === 2 ? t('New Deposit') : t('Check Deposit')
                    } (${seconds})`
                  }
                  onComplete={() => setCountdownDate()}
                />
              ) : (
                [activeStep === 2 ? t('New Deposit') : t('Check Deposit')]
              ))}
          </Button>
        </Stack>
      </Box>
    </Box>
  );
}
