import React, { forwardRef } from 'react';

import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';

import useGlobalSnackbar from 'hooks/useGlobalSnackbar';

const SnackbarAlert = forwardRef((props, ref) => (
  <Alert ref={ref} elevation={6} {...props} />
));

export default function SnackbarUI() {
  const { open, message, alertProps, snackbarProps, closeSnackbar } =
    useGlobalSnackbar();

  // const handleClose = () => closeSnackbar(onClose);

  return (
    <Snackbar
      open={open}
      autoHideDuration={6000}
      // open={false}
      onClose={closeSnackbar}
      anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      {...snackbarProps}
    >
      <SnackbarAlert
        onClose={closeSnackbar}
        severity="info"
        sx={{ width: '100%' }}
        {...alertProps}
      >
        {message}
      </SnackbarAlert>
    </Snackbar>
  );
}
