import React, {
  createContext,
  forwardRef,
  useContext,
  useMemo,
  useState,
} from 'react';

import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';

const GlobalSnackbarContext = createContext();
const useGlobalSnackbar = () => useContext(GlobalSnackbarContext);

const SnackbarAlert = forwardRef((props, ref) => (
  <Alert ref={ref} elevation={6} {...props} />
));

export function GlobalSnackbarProvider({ children }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState();

  const [onClose, setOnClose] = useState();

  const [alertProps, setAlertProps] = useState({});
  const [snackbarProps, setSnackbarProps] = useState({});

  const closeSnackbar = () => {
    setOpen(false);
    setMessage('');

    setAlertProps({});
    setSnackbarProps({});

    if (onClose) onClose();
  };

  const openSnackbar = (newMessage, options = {}) => {
    setOpen(true);
    setMessage(newMessage);

    setOnClose(() => () => {
      if (options.onClose) options.onClose();
    });

    setAlertProps(options.alertProps || {});
    setSnackbarProps(options.snackbarProps || {});
  };

  const value = useMemo(
    () => ({
      open,
      message,
      alertProps,
      snackbarProps,
      closeSnackbar,
      openSnackbar,
    }),
    [open, message, alertProps, snackbarProps]
  );

  return (
    <GlobalSnackbarContext.Provider value={value}>
      <Snackbar
        open={open}
        autoHideDuration={6000}
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
      {children}
    </GlobalSnackbarContext.Provider>
  );
}

export default useGlobalSnackbar;
