import React from 'react';

import { Navigate } from 'react-router-dom';

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import LoadingButton from '@mui/lab/LoadingButton';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

import CloseIcon from '@mui/icons-material/Close';
import GoogleIcon from '@mui/icons-material/Google';

import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';

import { useGoogleLogin } from '@react-oauth/google';

import { useLoginMutation } from 'redux/api/drf/auth';

import BrandLogo from 'components/BrandLogo';

export default function Login() {
  const { t } = useTranslation();

  const user = useSelector((state) => state.auth.user);

  const [login, { isError, isLoading, reset }] = useLoginMutation();

  const googleLogin = useGoogleLogin({
    onSuccess: (response) => login({ access_token: response.access_token }),
  });

  if (user)
    return (
      <Navigate replace to={user?.role === 'visitor' ? '/register' : '/'} />
    );

  return (
    <Box sx={{ m: 'auto', textAlign: 'center' }}>
      <Paper elevation={2} sx={{ bgcolor: 'background.default', p: 5 }}>
        <BrandLogo iconSize={30} titleVariant="h4" sx={{ mb: 2 }} />
        <Typography gutterBottom color="secondary" variant="h6" sx={{ mb: 3 }}>
          {t('Sign in using Google to get quick access')}
        </Typography>
        <LoadingButton
          loading={isLoading}
          startIcon={<GoogleIcon />}
          size="large"
          color="primary"
          variant="contained"
          onClick={googleLogin}
          sx={{ mt: 3 }}
        >
          {t('Sign in with Google')}
        </LoadingButton>
      </Paper>
      <Collapse unmountOnExit in={isError}>
        <Alert
          severity="error"
          action={
            <IconButton
              aria-label="close"
              color="inherit"
              size="small"
              onClick={reset}
            >
              <CloseIcon fontSize="inherit" />
            </IconButton>
          }
          sx={{ mt: 2 }}
        >
          {t('Unable to authenticate the account. Please try again.')}
        </Alert>
      </Collapse>
    </Box>
  );
}
