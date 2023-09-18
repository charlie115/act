import React, { useEffect } from 'react';

import { Navigate } from 'react-router-dom';

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Collapse from '@mui/material/Collapse';
import FormControl from '@mui/material/FormControl';
import FormHelperText from '@mui/material/FormHelperText';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import OutlinedInput from '@mui/material/OutlinedInput';
import Typography from '@mui/material/Typography';

import AlternateEmailIcon from '@mui/icons-material/AlternateEmail';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import CloseIcon from '@mui/icons-material/Close';

import { useTheme } from '@mui/material/styles';

import { Controller, useForm, useWatch } from 'react-hook-form';

import { Trans, useTranslation } from 'react-i18next';
import { useSelector } from 'react-redux';

import { useAuthUserRegisterMutation } from 'redux/api/drf';

import BrandLogo from 'components/BrandLogo';

export default function Register() {
  const theme = useTheme();

  const { t } = useTranslation();

  const isAuthorized = useSelector((state) => state.auth.isAuthorized);

  const user = useSelector((state) => state.auth.user);

  const [register, { isError, isLoading, reset }] =
    useAuthUserRegisterMutation();

  const { control, handleSubmit, formState } = useForm({
    defaultValues: { username: '' },
    mode: 'all',
  });

  const username = useWatch({
    control,
    name: 'username',
  });

  const { isValid } = formState;

  useEffect(() => {
    if (isError) reset();
  }, [username]);

  const onSubmit = (data) => {
    if (isValid) register({ username: data?.username?.toLowerCase() });
  };

  if (isAuthorized) return <Navigate replace to="/" />;

  if (!user) return <Navigate replace to="/login" />;

  return (
    <Box sx={{ m: 'auto', textAlign: 'center', width: 300 }}>
      <BrandLogo iconSize={30} titleVariant="h4" sx={{ mb: 5 }} />
      <Typography gutterBottom variant="h5">
        <Trans>
          Welcome,{' '}
          <span style={{ color: theme.palette.info.main, fontWeight: 700 }}>
            {{ firstName: user?.first_name || '_' }}{' '}
            {{ lastName: user?.last_name || '_' }}
          </span>
          !
        </Trans>
      </Typography>
      <Typography paragraph>
        {t('To continue, please provide a username:')}
      </Typography>
      <Box
        component="form"
        autoComplete="off"
        onSubmit={handleSubmit(onSubmit)}
      >
        <Controller
          name="username"
          control={control}
          rules={{
            required: t('Please enter a username'),
            minLength: {
              value: 6,
              message: t('Username must have {{min}}~{{max}} characters', {
                min: 6,
                max: 25,
              }),
            },
            maxLength: {
              value: 25,
              message: t('Username must have {{min}}~{{max}} characters', {
                min: 6,
                max: 25,
              }),
            },
            validate: {
              matchPattern: (value) => {
                if (!/^[a-z]/i.test(value))
                  return t('Username must start with a letter');
                if (!/^[a-z0-9_.]+$/i.test(value))
                  return t(
                    'Username must only include letters (a-z), numbers (0-9), underscores (_), and periods (.)'
                  );
                return true;
              },
            },
          }}
          render={({ field, fieldState }) => (
            <FormControl
              fullWidth
              error={!!fieldState.error}
              size="large"
              sx={{ mb: 3 }}
              {...field}
            >
              <OutlinedInput
                placeholder={t('Enter username')}
                startAdornment={
                  <InputAdornment position="start">
                    <AlternateEmailIcon />
                  </InputAdornment>
                }
              />
              <FormHelperText>{fieldState?.error?.message}</FormHelperText>
            </FormControl>
          )}
        />
        <Button
          fullWidth
          type="submit"
          disabled={!isValid || isLoading}
          endIcon={
            isLoading ? (
              <CircularProgress color="inherit" size={15} />
            ) : (
              <ArrowForwardIcon />
            )
          }
        >
          {t('Continue')}
        </Button>
      </Box>
      <Collapse unmountOnExit in={isError}>
        <hr />
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
          {t('Username is not available. Please try again.')}
        </Alert>
      </Collapse>
    </Box>
  );
}
