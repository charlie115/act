import React, { useRef, useState } from 'react';

import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Switch from '@mui/material/Switch';

import MarkChatUnreadIcon from '@mui/icons-material/MarkChatUnread';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import PersonOffIcon from '@mui/icons-material/PersonOff';

import { useDispatch, useSelector } from 'react-redux';
import { toggleNotification } from 'redux/reducers/chat';

import { useTranslation } from 'react-i18next';

import ManageBlockedUsers from './ManageBlockedUsers';

export default function ChatMenu() {
  const dispatch = useDispatch();

  const manageBlockedUsersRef = useRef();

  const { t } = useTranslation();

  const { enableNotification } = useSelector((state) => state.chat);

  const [anchorEl, setAnchorEl] = useState(null);
  const [open, setOpen] = useState(false);

  const handleClose = () => {
    setOpen(false);
    setAnchorEl(null);
  };

  return (
    <>
      <IconButton
        aria-label="close-chat"
        color="white"
        onClick={(event) => {
          setAnchorEl(event.currentTarget);
          setOpen((state) => !state);
        }}
      >
        <MoreVertIcon />
      </IconButton>
      <Menu
        id="chat-menu"
        aria-controls={open ? 'chat-menu' : undefined}
        aria-expanded={open ? 'true' : undefined}
        aria-haspopup="true"
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <MenuItem
          onClick={() => {
            manageBlockedUsersRef.current.open();
            handleClose();
          }}
        >
          <ListItemIcon>
            <PersonOffIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>{t('Manage Blocked Users')}</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem sx={{ ':hover': { backgroundColor: 'unset' } }}>
          <ListItemIcon>
            <MarkChatUnreadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText id="switch-label-notification">
            {enableNotification
              ? t('Disable Notification')
              : t('Enable Notification')}
          </ListItemText>
          <Switch
            edge="end"
            checked={enableNotification}
            onChange={(e) => {
              dispatch(toggleNotification(e.target.checked));
              handleClose();
            }}
            inputProps={{
              'aria-labelledby': 'switch-label-notification',
            }}
          />
        </MenuItem>
      </Menu>
      <ManageBlockedUsers
        ref={manageBlockedUsersRef}
        onClick={handleClose}
        TriggerElement={MenuItem}
      />
    </>
  );
}
