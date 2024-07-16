import React, { useMemo } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import { useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import { useGetBoardPostsQuery } from 'redux/api/drf/board';

import ReactTableUI from 'components/ReactTableUI';

import renderDateCell from 'components/tables/common/renderDateCell';

import renderStatsCell from './renderStatsCell';
import renderUserCell from './renderUserCell';
import renderViewedCell from './renderViewedCell';

export default function CommunityBoardPostsTable() {
  const location = useLocation();
  const navigate = useNavigate();

  const theme = useTheme();

  const { user } = useSelector((state) => state.auth);

  const { data: posts, isFetching } = useGetBoardPostsQuery();

  const columns = useMemo(
    () => [
      { accessorKey: 'viewed', cell: renderViewedCell },
      { accessorKey: 'title', size: 120, props: { sx: { fontWeight: 700 } } },
      { accessorKey: 'user', size: 120, cell: renderUserCell },
      { accessorKey: 'category', size: 120 },
      { accessorKey: 'stats', size: 120, cell: renderStatsCell },
      { accessorKey: 'date_created', size: 120, cell: renderDateCell },
    ],
    []
  );
  const data = useMemo(
    () =>
      posts?.map((post) => ({
        ...post,
        user: post.user_profile?.username,
        loggedInUser: user?.username,
      })) || [],
    [posts, user]
  );

  return (
    <ReactTableUI
      hideHeader
      columns={columns}
      data={data}
      isLoading={isFetching}
      showProgressBar={isFetching}
      options={{ getRowId: (row) => row.id }}
      getCellProps={() => ({
        sx: { py: 0.5, wordWrap: 'break-word' },
      })}
      getRowProps={(row) => ({
        onClick: () => {
          navigate(`/community-board/post/${row.id}`, {
            state: { from: location },
          });
        },
        sx: {
          cursor: 'pointer',
          ':hover': { color: theme.palette.info.main },
        },
      })}
      getTableProps={() => ({
        sx: {
          borderTop: 0.5,
          borderColor: 'grey.600',
          tableLayout: 'auto',
        },
      })}
    />
  );
}
