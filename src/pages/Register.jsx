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

import { useUserRegisterMutation } from 'redux/api/drf/auth';

import BrandLogo from 'components/BrandLogo';

import { REGEX } from 'constants';

export default function Register() {
  const theme = useTheme();

  const { t } = useTranslation();

  const { loggedin, user } = useSelector((state) => state.auth);

  const [register, { isError, isLoading, reset }] = useUserRegisterMutation();

  const { control, handleSubmit, formState } = useForm({
    defaultValues: { username: '' },
    mode: 'all',
  });

  const username = useWatch({ control, name: 'username' });

  const { isValid } = formState;

  useEffect(() => {
    if (isError) reset();
  }, [username]);

  const onSubmit = (data) => {
    if (isValid) register({ username: data?.username?.toLowerCase() });
  };

  if (loggedin) return <Navigate replace to="/" />;

  if (!user) return <Navigate replace to="/login" />;

  return (
    <Box sx={{ m: 'auto', textAlign: 'center', width: 300 }}>
      <BrandLogo
        size={180}
        sx={{ bgcolor: 'dark.main', justifyContent: 'center', mb: 5, p: 1 }}
      />
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
            validate: {
              matchPattern: (value) => {
                if (!REGEX.usernameFirstCharacter.test(value))
                  return t('Username must start with a letter');
                if (!REGEX.usernameFull.test(value))
                  return t(
                    'Username must only include letters (A-Z or 한글), numbers (0-9), underscores (_), and periods (.)'
                  );
                return true;
              },
              validate: (value) => {
                if (value.match(REGEX.koreanCharacters)) {
                  if (value.length >= 2 && value.length <= 12) return true;
                  return t('Username must have {{min}}~{{max}} characters', {
                    min: 2,
                    max: 12,
                  });
                }
                if (value.length >= 6 && value.length <= 25) return true;
                return t('Username must have {{min}}~{{max}} characters', {
                  min: 6,
                  max: 25,
                });
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
                autoFocus
                placeholder={t('Enter username')}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <AlternateEmailIcon />
                      </InputAdornment>
                    ),
                  },
                }}
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
