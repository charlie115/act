import React, { useState } from 'react';

import Box from '@mui/material/Box';
import LoadingButton from '@mui/lab/LoadingButton';
import Typography from '@mui/material/Typography';

import GoogleIcon from '@mui/icons-material/Google';

import { useTheme } from '@mui/material/styles';

import { Trans, useTranslation } from 'react-i18next';

import {
  GoogleLogin,
  googleLogout,
  useGoogleLogin,
  useGoogleOneTapLogin,
} from '@react-oauth/google';
import jwtDecode from 'jwt-decode';

import { useLoginMutation } from 'redux/api/drf';

import BrandLogo from 'components/BrandLogo';

export default function Login() {
  const theme = useTheme();
  const { i18n, t } = useTranslation();

  const [user, setUser] = useState(null);

  const [login, { isLoading, ...rest }] = useLoginMutation();
  console.log('rest: ', rest);

  const googleLogin = useGoogleLogin({
    onSuccess: (response) => {
      console.log('response: ', response);

      login({ access_token: response.access_token });
    },
    onError: (error) => console.log('error', error),
    // flow: 'auth-code',
  });

  return (
    <Box
      sx={{
        alignItems: 'center',
        display: 'flex',
        flex: 1,
        flexDirection: 'column',
        justifyContent: 'center',
        textAlign: 'center',
      }}
    >
      <BrandLogo iconSize={40} nameVariant="h4" sx={{ mb: 1, mr: 2 }} />
      <Typography gutterBottom color="secondary" variant="h6" sx={{ mb: 5 }}>
        {t('Sign in using Google to get quick access')}
      </Typography>
      {/* <GoogleLogin
        auto_select
        cancel_on_tap_outside
        useOneTap
        locale={i18n.language}
        shape="pill"
        size="large"
        text="signin_with"
        theme="filled_blue"
        onSuccess={(response) => {
          console.log('response: ', response);
          const decoded = jwtDecode(response.credential);
          setUser({
            email: decoded.email,
            firstName: decoded.given_name,
            lastName: decoded.family_name,
            name: decoded.name,
            picture: decoded.picture,
          });
          // login({ access_token: response.credential });
        }}
        onError={(error) => {
          console.log('error: ', error);
        }}
      /> */}
      <LoadingButton
        loading={isLoading}
        startIcon={<GoogleIcon />}
        size="large"
        color="info"
        variant="contained"
        onClick={googleLogin}
      >
        {t('Sign in with Google')}
      </LoadingButton>
    </Box>
  );
}
