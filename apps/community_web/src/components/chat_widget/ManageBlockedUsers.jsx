import React, { forwardRef, useImperativeHandle, useState } from 'react';

import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';

import { useDispatch, useSelector } from 'react-redux';
import { unblockUser } from 'redux/reducers/chat';

import { useTranslation } from 'react-i18next';

const ManageBlockedUsers = forwardRef((_, ref) => {
  const dispatch = useDispatch();

  const { t } = useTranslation();

  const { blocklist } = useSelector((state) => state.chat);

  const [open, setOpen] = useState(false);

  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  useImperativeHandle(
    ref,
    () => ({
      open: handleOpen,
    }),
    []
  );

  return (
    <Dialog fullWidth maxWidth="xs" open={open} onClose={handleClose}>
      <DialogTitle>{t('Manage Blocked Users')}</DialogTitle>
      <List sx={{ pt: 0, pb: 1 }}>
        {blocklist.map((blockedUser) => (
          <ListItem
            key={blockedUser}
            secondaryAction={
              <Button onClick={() => dispatch(unblockUser(blockedUser))}>
                {t('Unblock')}
              </Button>
            }
          >
            <ListItemText
              disableTypography
              sx={{ fontStyle: 'italic', fontWeight: 'bold' }}
            >
              @{blockedUser}
            </ListItemText>
          </ListItem>
        ))}
        {blocklist.length === 0 && (
          <ListItem sx={{ color: 'secondary.main', textAlign: 'center' }}>
            <ListItemText>{t('You have not blocked any user.')}</ListItemText>
          </ListItem>
        )}
      </List>
    </Dialog>
  );
});

export default ManageBlockedUsers;
