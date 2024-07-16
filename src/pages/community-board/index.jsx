import React from 'react';

import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';

import AddIcon from '@mui/icons-material/Add';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';

import CommunityBoardPostsTable from 'components/tables/community_board/CommunityBoardPostsTable';

export default function CommunityBoard() {
  const location = useLocation();
  const navigate = useNavigate();

  const { t } = useTranslation();

  const { loggedin } = useSelector((state) => state.auth);

  if (!loggedin)
    return <Navigate replace to="/login" state={{ from: location }} />;

  if (location.pathname.includes('post'))
    return (
      <Box sx={{ flex: 1, p: 2 }}>
        <Outlet />
      </Box>
    );

  return (
    <Box sx={{ flex: 1, p: 2 }}>
      <Paper elevation={2} sx={{ minHeight: '100%', p: 2 }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() =>
            navigate('/community-board/post/new', {
              state: { from: location },
            })
          }
          sx={{ mb: 4 }}
        >
          {t('New')}
        </Button>
        <CommunityBoardPostsTable />
      </Paper>
    </Box>
  );
}
