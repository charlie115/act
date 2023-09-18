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
import MuiAlert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import SvgIcon from '@mui/material/SvgIcon';

import LogoutIcon from '@mui/icons-material/Logout';
import SettingsIcon from '@mui/icons-material/Settings';

import { useSelector } from 'react-redux';
import { useAuthLogoutMutation } from 'redux/api/drf';

import { useTranslation } from 'react-i18next';

import { ReactComponent as RobotSvg } from 'assets/icons/font-awesome/robot.svg';

const Alert = React.forwardRef((props, ref) => (
  <MuiAlert ref={ref} elevation={6} {...props} />
));

export default function HeaderUserMenu({ iconStyle }) {
  const navigate = useNavigate();

  const { t } = useTranslation();

  const { isAuthorized, user } = useSelector((state) => state.auth);

  const [logout, { isLoading, isSuccess, reset }] = useAuthLogoutMutation();

  const [anchorEl, setAnchorEl] = useState(null);

  const handleClick = (event) => {
    if (isAuthorized) setAnchorEl(event.currentTarget);
    else navigate('/login');
  };
  const handleClose = () => setAnchorEl(null);

  useEffect(() => {
    if (isSuccess) handleClose();
  }, [isSuccess]);

  return (
    <>
      <IconButton onClick={handleClick} sx={{ p: 0, ...iconStyle }}>
        <Avatar
          src={user?.profile?.picture}
          alt={`${user?.first_name} ${user?.last_name}`}
          sx={{ bgcolor: user ? 'primary.main' : null }}
        />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        id="user-menu"
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
      <Snackbar
        open={isSuccess}
        autoHideDuration={1000}
        onClose={reset}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={reset} severity="info" sx={{ width: '100%' }}>
          {t('You have been logged out!')}
        </Alert>
      </Snackbar>
    </>
  );
}
