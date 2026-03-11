import React from 'react';

import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import LinearProgress from '@mui/material/LinearProgress';

import { Trans, useTranslation } from 'react-i18next';

export default function DeleteAlert({
  loading,
  open,
  onCancel,
  onClose,
  onDelete,
  title,
}) {
  const { t } = useTranslation();

  return (
    <Dialog
      aria-labelledby="delete-alert-title"
      aria-describedby="delete-alert-description"
      open={open}
      onClose={onClose}
    >
      {loading && <LinearProgress />}
      <DialogTitle id="delete-alert-title">{title}</DialogTitle>
      <DialogContent>
        <DialogContentText id="delete-alert-description">
          <Trans>
            This action is{' '}
            <strong style={{ textTransform: 'underline' }}>irreversible</strong>
            !
          </Trans>{' '}
          {t('Do you wish to continue?')}
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button
          autoFocus
          color="secondary"
          disabled={loading}
          onClick={onCancel}
        >
          {t('Cancel')}
        </Button>
        <Button
          color="error"
          variant="contained"
          disabled={loading}
          onClick={onDelete}
        >
          {t('Delete')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
