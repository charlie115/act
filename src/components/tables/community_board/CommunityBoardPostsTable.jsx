import React, { useEffect, useMemo, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Pagination from '@mui/material/Pagination';

import { alpha, useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import { useGetBoardPostsQuery } from 'redux/api/drf/board';

import { usePrevious } from '@uidotdev/usehooks';

import ReactTableUI from 'components/ReactTableUI';

import renderAuthorCell from './renderAuthorCell';
import renderCategoryCell from './renderCategoryCell';
import renderDateCreatedCell from './renderDateCreatedCell';
import renderStatsCell from './renderStatsCell';
import renderViewedCell from './renderViewedCell';

export default function CommunityBoardPostsTable() {
  const location = useLocation();
  const navigate = useNavigate();

  const theme = useTheme();

  const [noOfPages, setNoOfPages] = useState();
  const [page, setPage] = useState(1);

  const { loggedin, user } = useSelector((state) => state.auth);

  const {
    data: results,
    isError,
    isFetching,
  } = useGetBoardPostsQuery({ page });

  const columns = useMemo(
    () => [
      ...(loggedin
        ? [{ accessorKey: 'user_view', maxSize: 40, cell: renderViewedCell }]
        : []),
      {
        accessorKey: 'title',
        maxSize: 120,
        props: { sx: { fontWeight: 700 } },
      },
      { accessorKey: 'author', maxSize: 100, cell: renderAuthorCell },
      { accessorKey: 'category', maxSize: 80, cell: renderCategoryCell },
      { accessorKey: 'stats', maxSize: 125, cell: renderStatsCell },
      { accessorKey: 'date_created', maxSize: 80, cell: renderDateCreatedCell },
    ],
    [loggedin]
  );

  const posts = results?.results || [];
  const data = useMemo(
    () =>
      posts?.map((post) => ({
        ...post,
        author: post.author_profile?.username,
        loggedInUser: user?.username,
      })) || [],
    [posts, user]
  );

  useEffect(() => {
    if (results)
      setNoOfPages((state) => {
        if (state) return state;
        return Math.ceil(results.count / results.results.length);
      });
  }, [results]);

  const previousPage = usePrevious(page);
  useEffect(() => {
    if (isError)
      if (previousPage && page !== previousPage) setPage(previousPage);
  }, [isError]);

  return (
    <Box sx={{ textAlign: 'center' }}>
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
            ':hover': { bgcolor: alpha(theme.palette.info.main, 0.2) },
          },
        })}
        getTableProps={() => ({
          sx: { borderTop: 0.5, borderColor: 'grey.600', fontSize: '1.15em' },
        })}
      />
      {noOfPages > 1 && (
        <Pagination
          color="info"
          count={noOfPages}
          page={page}
          shape="rounded"
          onChange={(e, value) => {
            setPage(value);
          }}
          sx={{ float: 'right', my: 2 }}
        />
      )}
    </Box>
  );
}
