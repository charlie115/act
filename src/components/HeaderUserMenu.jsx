import React, { useEffect, useState } from 'react';

import { useNavigate } from 'react-router-dom';

import Avatar from '@mui/material/Avatar';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import SvgIcon from '@mui/material/SvgIcon';

import LogoutIcon from '@mui/icons-material/Logout';
import SettingsIcon from '@mui/icons-material/Settings';

import { useDispatch, useSelector } from 'react-redux';
import { useLogoutMutation } from 'redux/api/drf/auth';
import { setSnackbar } from 'redux/reducers/app';

import { useTranslation } from 'react-i18next';

import { ReactComponent as RobotSvg } from 'assets/icons/font-awesome/robot.svg';

export default function HeaderUserMenu({ iconStyle }) {
  const dispatch = useDispatch();

  const navigate = useNavigate();

  const { t } = useTranslation();

  const { loggedin, user } = useSelector((state) => state.auth);

  const [logout, { isLoading, isSuccess, reset }] = useLogoutMutation();

  const [anchorEl, setAnchorEl] = useState(null);

  const handleClick = (event) => {
    if (loggedin) setAnchorEl(event.currentTarget);
    else navigate('/login');
  };
  const handleClose = () => setAnchorEl(null);

  useEffect(() => {
    if (isSuccess) {
      dispatch(
        setSnackbar({
          message: t('You have been logged out!'),
          closeCallback: reset,
          snackbarProps: {
            autoHideDuration: 1500,
            open: true,
          },
        })
      );
      handleClose();
    }
  }, [isSuccess]);

  return (
    <>
      <IconButton
        id="user-menu-btn"
        onClick={handleClick}
        sx={{ p: 0, ...iconStyle }}
      >
        <Avatar
          src={user?.profile?.picture}
          alt={`${user?.first_name} ${user?.last_name}`}
          sx={{ bgcolor: user ? 'primary.main' : null }}
        />
      </IconButton>
      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        open={!!anchorEl}
        onClose={handleClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
            '&:before': {
              content: '""',
              display: 'block',
              position: 'absolute',
              top: 0,
              right: 14,
              width: 10,
              height: 10,
              bgcolor: 'background.paper',
              transform: 'translateY(-50%) rotate(45deg)',
              zIndex: 0,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem
          onClick={() => {
            navigate('/account');
            handleClose();
          }}
        >
          <Avatar />
          {t('Account')}
        </MenuItem>
        <MenuItem onClick={handleClose}>
          <Avatar>
            <SvgIcon>
              <RobotSvg />
            </SvgIcon>
          </Avatar>
          {t('Ar-Bot Settings')}
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleClose}>
          <ListItemIcon>
            <SettingsIcon />
          </ListItemIcon>
          {t('Settings')}
        </MenuItem>
        <MenuItem onClick={logout}>
          <ListItemIcon>
            <LogoutIcon />
          </ListItemIcon>
          <ListItemText>{t('Logout')}</ListItemText>
          {isLoading && <CircularProgress size={16} />}
        </MenuItem>
      </Menu>
    </>
  );
}
