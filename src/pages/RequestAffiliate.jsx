import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

import {
  Avatar,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Container,
  FormControl,
  FormControlLabel,
  FormHelperText,
  InputLabel,
  OutlinedInput,
  Paper,
  Stack,
  Typography,
} from '@mui/material';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useTranslation } from 'react-i18next';
import { Controller, useForm, useWatch } from 'react-hook-form';

import { usePostAffiliateRequestMutation } from 'redux/api/drf/referral';
import useGlobalSnackbar from 'hooks/useGlobalSnackbar';

export default function RequestAffiliate() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { openSnackbar } = useGlobalSnackbar();
  const { loggedin, user } = useSelector((state) => state.auth);

  const [postAffiliateRequest, { isLoading }] = usePostAffiliateRequestMutation();

  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch,
  } = useForm({
    defaultValues: {
      contact: '',
      url: '',
      description: '',
      noUrl: false,
    },
    mode: 'onChange',
  });

  const noUrl = watch('noUrl');

  useEffect(() => {
    if (noUrl) {
      // If noUrl is checked, clear the URL and set it to null or empty
      setValue('url', '');
    }
  }, [noUrl, setValue]);

  useEffect(() => {
    if (user?.affiliate) {
      navigate('/affiliate-dashboard');
    }
  }, [user]);

  console.log(user.affiliate);

  const onSubmit = async (data) => {
    // If noUrl is checked, we send null for url
    const payload = {
      ...data,
      url: noUrl ? null : data.url,
    };
    try {
      await postAffiliateRequest(payload).unwrap();
      openSnackbar(t('Your affiliate request has been submitted successfully. Please wait while we review your application.'), { variant: 'success' });
    } catch (error) {
      if (error?.data?.error?.[0] === "REQUEST_EXISTS") {
        openSnackbar(t('You have already submitted an application. Please wait while we review your application.'), { variant: 'error' });
      } else if (error?.data?.error?.[0] === "INVALID_PARENT_CODE") {
        openSnackbar(t('Invalid parent code. Please check the code and try again.'), { variant: 'error' });
      } else if (error?.data?.non_field_errors?.[0].includes('UUID')) {
        openSnackbar(t('Invalid parent code. Please check the code and try again.'), { variant: 'error' });
      } else {
        openSnackbar(t('Failed to submit application'), { variant: 'error' });
      }
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" sx={{ mb: 4 }}>
          {t('Apply for Affiliate Program')}
        </Typography>
        <Box component="form" onSubmit={handleSubmit(onSubmit)}>
          <Stack spacing={3}>
            {/* Contact Field */}
            <Controller
              name="contact"
              control={control}
              rules={{
                required: t('Contact is required'),
              }}
              render={({ field }) => (
                <FormControl error={!!errors.contact} fullWidth variant="outlined">
                  <InputLabel htmlFor="contact">{t('Contact')}</InputLabel>
                  <OutlinedInput
                    id="contact"
                    label={t('Contact')}
                    {...field}
                  />
                  <FormHelperText>
                    {errors.contact
                      ? errors.contact.message
                      : t('Enter your Telegram ID, ex. @username')}
                  </FormHelperText>
                </FormControl>
              )}
            />

            {/* URL Field and "없음" Checkbox */}
            <Box>
              <Controller
                name="url"
                control={control}
                rules={{
                  required: noUrl ? false : t('URL is required'),
                  pattern: noUrl
                    ? undefined
                    : {
                        value: /^https?:\/\/\S+$/,
                        message: t('Enter a valid URL'),
                      },
                }}
                render={({ field }) => (
                  <FormControl error={!!errors.url} fullWidth variant="outlined">
                    <InputLabel htmlFor="url">{t('URL')}</InputLabel>
                    <OutlinedInput
                      id="url"
                      label={t('URL')}
                      {...field}
                      disabled={noUrl}
                    />
                    <FormHelperText>
                      {errors.url
                        ? errors.url.message
                        : t('Enter the website URL for your affiliate business')}
                    </FormHelperText>
                  </FormControl>
                )}
              />
              <FormControlLabel
                control={
                  <Controller
                    name="noUrl"
                    control={control}
                    render={({ field }) => (
                      <Checkbox
                        {...field}
                        checked={field.value}
                      />
                    )}
                  />
                }
                label={t('No URL')}
                sx={{ mt: 1 }}
              />
            </Box>
            {/* Parent Affiliate Code Field */}
            <Controller
              name="parent_affiliate_code"
              control={control}
              render={({ field }) => (
                <FormControl error={!!errors.parentAffiliateCode} fullWidth variant="outlined">
                  <InputLabel htmlFor="parentAffiliateCode">{t('Parent Affiliate Code')}</InputLabel>
                  <OutlinedInput
                    id="parentAffiliateCode"
                    label={t('Parent Affiliate Code')}
                    {...field}
                  />
                  <FormHelperText>
                    {errors.parentAffiliateCode
                      ? errors.parentAffiliateCode.message
                      : t('Enter the parent affiliate code if you have one')}
                  </FormHelperText>
                </FormControl>
              )}
            />

            {/* Description Field */}
            <Controller
              name="description"
              control={control}
              rules={{
                required: t('Description is required'),
              }}
              render={({ field }) => (
                <FormControl error={!!errors.description} fullWidth variant="outlined">
                  <InputLabel htmlFor="description">{t('Description')}</InputLabel>
                  <OutlinedInput
                    id="description"
                    label={t('Description')}
                    multiline
                    rows={4}
                    {...field}
                  />
                  <FormHelperText>
                    {errors.description
                      ? errors.description.message
                      : t('Provide a brief description of your affiliate program or business.')}
                  </FormHelperText>
                </FormControl>
              )}
            />

            <Button
              variant="contained"
              type="submit"
              disabled={!isValid || isLoading}
              size="large"
              sx={{ alignSelf: 'flex-end' }}
            >
              {isLoading ? (
                <CircularProgress size={24} />
              ) : (
                t('Submit')
              )}
            </Button>
          </Stack>
        </Box>
      </Paper>
    </Container>
  );
}