import React from 'react';

import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';

import AlternateEmailIcon from '@mui/icons-material/AlternateEmail';
import DomainVerificationIcon from '@mui/icons-material/DomainVerification';
import GoogleIcon from '@mui/icons-material/Google';
import PersonIcon from '@mui/icons-material/Person';

import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';

import { DateTime } from 'luxon';

export default function MyPage() {
  const { t } = useTranslation();

  const { user } = useSelector((state) => state.auth);

  return (
    <Box sx={{ m: 'auto' }}>
      <Typography variant="h4" sx={{ mb: 2 }}>
        {t('My Page')}
      </Typography>
      <Divider sx={{ mb: 2 }} />
      <Table
        sx={{ borderCollapse: 'collapse', minWidth: 400, td: { border: 0 } }}
      >
        <TableBody>
          <TableRow sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
            <TableCell align="right" sx={{ p: 0, width: 16 }}>
              <PersonIcon />
            </TableCell>
            <TableCell sx={{ fontSize: 16 }}>{t('Name')}</TableCell>
            <TableCell sx={{ fontSize: 16 }}>
              <Stack alignItems="center" direction="row" spacing={1}>
                <Avatar
                  src={user?.profile?.picture}
                  alt={t('userFullName', {
                    firstName: user?.first_name,
                    lastName: user?.last_name,
                  })}
                  sx={{
                    bgcolor: user ? 'primary.main' : null,
                    width: 28,
                    height: 28,
                  }}
                />
                <Box>
                  {t('userFullName', {
                    firstName: user?.first_name,
                    lastName: user?.last_name,
                  })}
                </Box>
              </Stack>
            </TableCell>
          </TableRow>
          <TableRow sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
            <TableCell align="right" sx={{ p: 0 }}>
              <AlternateEmailIcon />
            </TableCell>
            <TableCell sx={{ fontSize: 16 }}>{t('Username')}</TableCell>
            <TableCell sx={{ fontSize: 16 }}>{user?.username}</TableCell>
          </TableRow>
          <TableRow sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
            <TableCell align="right" sx={{ p: 0 }}>
              <GoogleIcon />
            </TableCell>
            <TableCell sx={{ fontSize: 16 }}>{t('E-mail')}</TableCell>
            <TableCell sx={{ fontSize: 16 }}>{user?.email}</TableCell>
          </TableRow>
          {user?.date_joined && (
            <TableRow
              sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
            >
              <TableCell align="right" sx={{ p: 0 }}>
                <DomainVerificationIcon />
              </TableCell>
              <TableCell sx={{ fontSize: 16 }}>
                {t('Registration Date')}
              </TableCell>
              <TableCell sx={{ fontSize: 16 }}>
                {DateTime.fromISO(user.date_joined).toFormat('DDDD')}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Box>
  );
}
