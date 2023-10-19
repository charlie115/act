import React, { forwardRef, useImperativeHandle, useState } from 'react';

import Avatar from '@mui/material/Avatar';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import Divider from '@mui/material/Divider';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import MenuItem from '@mui/material/MenuItem';
import PersonIcon from '@mui/icons-material/Person';
import AddIcon from '@mui/icons-material/Add';
import Typography from '@mui/material/Typography';
import { blue } from '@mui/material/colors';

import { useDispatch, useSelector } from 'react-redux';
import { unblockUser } from 'redux/reducers/chat';

import { useTranslation } from 'react-i18next';

const ManageBlockedUsers = forwardRef(({ onClick, TriggerElement }, ref) => {
  const dispatch = useDispatch();

  const { t } = useTranslation();

  const { blocklist } = useSelector((state) => state.chat);

  const [open, setOpen] = useState(false);
  const [unblockedUser, setUnblockedUser] = useState(null);

  const handleOpen = () => {
    setOpen(true);
    // onClick();
  };
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
