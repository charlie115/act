import React, { useMemo, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import Avatar from '@mui/material/Avatar';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ConfirmationNumberIcon from '@mui/icons-material/ConfirmationNumber';
import AppRegistrationIcon from '@mui/icons-material/AppRegistration';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import LogoutIcon from '@mui/icons-material/Logout';
import Badge from '@mui/material/Badge';

import { useSelector } from 'react-redux';
import { useLogoutMutation } from 'redux/api/drf/auth';
import { useGetCouponsQuery, useGetCouponRedemptionsQuery } from 'redux/api/drf/coupon';

import { useTranslation } from 'react-i18next';
import useGlobalSnackbar from 'hooks/useGlobalSnackbar';

export default function HeaderUserMenu({ iconStyle }) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { openSnackbar } = useGlobalSnackbar();
  const { loggedin, user } = useSelector((state) => state.auth);

  const [logout, { isLoading, isSuccess, reset }] = useLogoutMutation();

  // Fetch coupons and redemptions
  const { data: coupons = [] } = useGetCouponsQuery();
  const { data: redemptions = [] } = useGetCouponRedemptionsQuery();

  const [anchorEl, setAnchorEl] = useState(null);

  const handleClick = (event) => {
    if (loggedin) setAnchorEl(event.currentTarget);
    else navigate('/login');
  };
  const handleClose = () => setAnchorEl(null);

  useEffect(() => {
    if (isSuccess) {
      openSnackbar(t('You have been logged out!'), {
        onClose: reset,
        snackbarProps: { autoHideDuration: 1500 },
      });
      handleClose();
    }
  }, [isSuccess, openSnackbar, reset, t]);

  const hasAffiliate = !!user?.affiliate; // Checks if the user has affiliate data

  // Compute unused coupons
  // redeemedCouponNames: set of coupon names that are redeemed
  const redeemedCouponNames = useMemo(() => new Set(redemptions.map(r => r.coupon)), [redemptions]);
  const unusedCount = useMemo(() => {
    if (!coupons.length) return 0;
    return coupons.filter(coupon => !redeemedCouponNames.has(coupon.name)).length;
  }, [coupons, redeemedCouponNames]);

  return (
    <>
      <IconButton
        id="user-menu-btn"
        onClick={handleClick}
        sx={{ p: 0, ...iconStyle }}
      >
        <Avatar
          src={user?.profile?.picture}
          alt={t('userFullName', {
            firstName: user?.first_name,
            lastName: user?.last_name,
          })}
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
            minWidth: 150,
            mt: 1.5,
            '& .MuiAvatar-root': {
              width: 24,
              height: 24,
              ml: -0.5,
              mr: 2,
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
            navigate('/my-page');
            handleClose();
          }}
        >
          <Avatar />
          {t('My Page')}
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            navigate('/coupon-dashboard');
            handleClose();
          }}
        >
          <ListItemIcon>
            {/* Display badge only if unusedCount > 0 */}
            <Badge 
              badgeContent={unusedCount} 
              color="error" 
              overlap="rectangular"
              invisible={unusedCount === 0}
              sx={{
                '& .MuiBadge-badge': {
                  fontSize: '0.75rem',
                  height: '15px',
                  minWidth: '15px',
                  padding: '0 4px'
                }
              }}
            >
              <ConfirmationNumberIcon />
            </Badge>
          </ListItemIcon>
          {t('Coupon Dashboard')}
        </MenuItem>
        <Divider />
        {hasAffiliate ? (
          <MenuItem
            onClick={() => {
              navigate('/affiliate');
              handleClose();
            }}
          >
            <ListItemIcon>
              <DashboardIcon />
            </ListItemIcon>
            <ListItemText>
              {t('Affiliate Dashboard')}
            </ListItemText>
          </MenuItem>
        ) : (
          <MenuItem
            onClick={() => {
              navigate('/request-affiliate');
              handleClose();
            }}
          >
            <ListItemIcon>
              <AppRegistrationIcon />
            </ListItemIcon>
            <ListItemText>
              {t('Apply for Affiliate Program')}
            </ListItemText>
          </MenuItem>
        )}
        <Divider />
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