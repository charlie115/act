import React, { useState } from 'react';
import { useSelector } from 'react-redux';

import {
  Box,
  Button,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormHelperText,
  InputLabel,
  OutlinedInput,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  IconButton,
  Slider
} from '@mui/material';

import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';

import { useTranslation } from 'react-i18next';
import { Controller, useForm } from 'react-hook-form';

import { 
  useGetReferralCodesQuery, 
  usePostReferralCodeMutation, 
  useDeleteReferralCodeMutation,
  useGetAffiliateTierQuery,
  useGetSubAffiliatesQuery as useSubGetAffiliatesQuery, // <-- New hook for fetching affiliates
} from 'redux/api/drf/referral';

import useGlobalSnackbar from 'hooks/useGlobalSnackbar';

export default function Dashboard() {
  const { t } = useTranslation();
  const { openSnackbar } = useGlobalSnackbar();
  const { user } = useSelector((state) => state.auth);

  const [openModal, setOpenModal] = useState(false);

  const affiliate = user?.affiliate;
  
  const { data: tierData, isLoading: tierLoading } = useGetAffiliateTierQuery();
  const [postReferralCode, { isLoading: creatingCode }] = usePostReferralCodeMutation();
  const [deleteReferralCode] = useDeleteReferralCodeMutation();
  
  const { data: referralCodesData, isLoading: codesLoading, refetch: refetchCodes } = useGetReferralCodesQuery();
  
  // Fetch all affiliates
  const { data: subAffiliatesData, isLoading: affiliatesLoading } = useSubGetAffiliatesQuery();

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isValid },
    watch,
  } = useForm({
    defaultValues: {
      code: '',
      user_discount_rate: 0.05, // Default 5%
    },
    mode: 'onChange'
  });

  // Find the user's tier
  const userTier = tierData?.find((tier) => tier.id === affiliate?.tier) || null;

  // Filter affiliates whose parent_affiliate matches current affiliate's id
  const subAffiliates = subAffiliatesData;

  const onSubmitCode = async (data) => {
    try {
      await postReferralCode(data).unwrap();
      openSnackbar(t('Referral code created successfully!'), { variant: 'success' });
      setOpenModal(false);
      reset({ code: '', user_discount_rate: 0.05 });
      refetchCodes();
    } catch (error) {
      if (error.data?.code?.[0]?.includes("referral code")) {
        openSnackbar(t('Referral code already exists'), { variant: 'error' });
      } else {
        openSnackbar(t('Failed to create referral code'), { variant: 'error' });
      }
    }
  };

  const handleDeleteCode = async (id) => {
    try {
      await deleteReferralCode(id).unwrap();
      openSnackbar(t('Referral code deleted'), { variant: 'success' });
      refetchCodes();
    } catch (error) {
      openSnackbar(t('Failed to delete referral code'), { variant: 'error' });
    }
  };

  const baseCommissionRatePercent = userTier 
    ? (parseFloat(userTier.base_commission_rate) * 100).toFixed(2) 
    : null;
  const parentCommissionRate = userTier ? parseFloat(userTier.parent_commission_rate) : 0;

  let content;
  if (tierLoading) {
    content = <CircularProgress />;
  } else if (affiliate && userTier) {
    content = (
      <Stack spacing={2}>
        <Typography variant="body1">
          {t('Tier Level')}: <strong>{userTier.name}</strong>
        </Typography>
        <Typography variant="body1">
          {t('Base Commission Rate')}: <strong>{baseCommissionRatePercent}%</strong> {t('from the paid fee of the users')}
        </Typography>
        {parentCommissionRate > 0 && (
          <>
            <Typography variant="body1">
              {t('Parent Commission Rate')}: <strong>{(parentCommissionRate * 100).toFixed(2)}%</strong> {t("from the child affilates' commission")}
            </Typography>
            <Typography variant="body1">
              {t('Affiliate Code')}: <strong>{affiliate.affiliate_code}</strong>
            </Typography>
            <Typography variant="body1">
              {t('Total Forwarded Commission')}: <strong>{affiliate.total_forwarded_commission}</strong>
            </Typography>
          </>
        )}
        <Typography variant="body1">
              {t('Direct Commission')}: <strong>{affiliate.total_direct_commission}</strong>
        </Typography>
        <Typography variant="body1">
              {t('Total Earned Commission')}: <strong>{affiliate.total_earned_commission}</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('Joined on')} {new Date(affiliate.created_at).toLocaleString()}
        </Typography>
      </Stack>
    );
  } else {
    content = (
      <Typography variant="body1" color="text.secondary">
        {t('You are not an affiliate or data is not loaded yet.')}
      </Typography>
    );
  }

  const userDiscountRate = watch('user_discount_rate');
  const selfCommissionRate = (1 - userDiscountRate);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 2 }}>
          {t('Affiliate Dashboard')}
        </Typography>
        {content}
      </Paper>

      {/* Sub-Affiliates Section */}
      {parentCommissionRate > 0 && (
        <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
          <Typography variant="h5" sx={{ mb: 2 }}>
            {t('Your Sub-Affiliates')}
          </Typography>

          {affiliatesLoading && (
            <CircularProgress />
          )}

          {!affiliatesLoading && subAffiliates.length > 0 && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('User')}</TableCell>
                    <TableCell>{t('Tier')}</TableCell>
                    <TableCell>{t('Referral Count')}</TableCell>
                    <TableCell>{t('Total Earned Commission')}</TableCell>
                    <TableCell>{t('Total Forwarding Commission')}</TableCell>
                    <TableCell>{t('Created At')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {subAffiliates.map((sub) => (
                    <TableRow key={sub.id}>
                      <TableCell>{sub.user}</TableCell>
                      <TableCell>{sub.tier}</TableCell>
                      <TableCell>{sub.referral_count}</TableCell>
                      <TableCell>{sub.total_earned_commission}</TableCell>
                      <TableCell>{sub.total_forwarding_commission}</TableCell>
                      <TableCell>{new Date(sub.created_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {!affiliatesLoading && subAffiliates.length === 0 && (
            <Typography variant="body1" color="text.secondary">
              {t('You have no sub-affiliates.')}
            </Typography>
          )}
        </Paper>
      )}

      {/* Referral Codes Section */}
      <Paper elevation={3} sx={{ p: 4 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
          <Typography variant="h5">{t('Your Referral Codes')}</Typography>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => setOpenModal(true)}
          >
            {t('Generate Referral Code')}
          </Button>
        </Stack>
        {codesLoading ? (
          <CircularProgress />
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t('Code')}</TableCell>
                  <TableCell>{t('User Discount Rate')}</TableCell>
                  <TableCell>{t('Self Commission Rate')}</TableCell>
                  <TableCell>{t('Referral Count')}</TableCell>
                  <TableCell>{t('Total Earned Commission')}</TableCell>
                  <TableCell>{t('Created At')}</TableCell>
                  <TableCell>{t('Delete')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {referralCodesData?.length > 0 ? (
                  referralCodesData.map((rc) => (
                    <TableRow key={rc.id}>
                      <TableCell>{rc.code}</TableCell>
                      <TableCell>{(rc.user_discount_rate * 100).toFixed(0)}%</TableCell>
                      <TableCell>{(rc.self_commission_rate) * 100}%</TableCell>
                      <TableCell>{rc.referral_count ? rc.referral_count : 0}</TableCell>
                      <TableCell>{rc.total_earned_commission ? rc.total_earned_commission : 0}</TableCell>
                      <TableCell>{new Date(rc.created_at).toLocaleString()}</TableCell>
                      <TableCell>
                        <IconButton color="error" onClick={() => handleDeleteCode(rc.id)}>
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7}>{t('No referral codes available')}</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Modal for creating a referral code */}
      <Dialog open={openModal} onClose={() => setOpenModal(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('Generate Referral Code')}</DialogTitle>
        <DialogContent>
          <form id="create-referral-code-form" onSubmit={handleSubmit(onSubmitCode)}>
            <Controller
              name="code"
              control={control}
              rules={{
                required: t('Code is required')
              }}
              render={({ field }) => (
                <FormControl error={!!errors.code} fullWidth variant="outlined" sx={{ mt: 2 }}>
                  <InputLabel htmlFor="code">{t('Code')}</InputLabel>
                  <OutlinedInput
                    id="code"
                    label={t('Code')}
                    {...field}
                  />
                  <FormHelperText>
                    {errors.code ? errors.code.message : t('Enter a unique referral code')}
                  </FormHelperText>
                </FormControl>
              )}
            />

            <Box sx={{ mt: 4 }}>
              <Typography variant="body1" sx={{ mb: 1 }}>
                {t('Set the user discount rate and self commission rate.')}
              </Typography>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">{(userDiscountRate * 100).toFixed(0)}%</Typography>
                <Box sx={{ flex: 1, mx: 2 }}>
                  <Controller
                    name="user_discount_rate"
                    control={control}
                    rules={{ 
                      min: 0,
                      max: 1,
                      validate: (value) => (value >= 0 && value <= 1) || t('Must be between 0 and 1')
                    }}
                    render={({ field }) => (
                      <Slider
                        {...field}
                        value={field.value}
                        onChange={(_, val) => field.onChange(val)}
                        step={0.01}
                        min={0}
                        max={1}
                      />
                    )}
                  />
                </Box>
                <Typography variant="body2">{(selfCommissionRate * 100).toFixed(0)}%</Typography>
              </Box>
              <FormHelperText>
                {t('User Discount Rate on the left, Self Commission Rate on the right. Sum = 100%.')}
              </FormHelperText>
            </Box>
          </form>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenModal(false)}>{t('Cancel')}</Button>
          <Button 
            type="submit" 
            form="create-referral-code-form" 
            variant="contained"
            disabled={!isValid || creatingCode}
          >
            {creatingCode ? <CircularProgress size={24} /> : t('Create')}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}