import React, { useEffect, useMemo, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Pagination from '@mui/material/Pagination';

import useMediaQuery from '@mui/material/useMediaQuery';
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

export default function CommunityBoardPostsTable({ filters }) {
  const location = useLocation();
  const navigate = useNavigate();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

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
        ? [
            {
              accessorKey: 'user_view',
              maxSize: isMobile ? 20 : 40,
              cell: renderViewedCell,
            },
          ]
        : []),
      {
        accessorKey: 'title',
        maxSize: isMobile ? 80 : 120,
        props: { sx: { fontWeight: 700 } },
      },
      {
        accessorKey: 'author',
        maxSize: isMobile ? 75 : 100,
        cell: renderAuthorCell,
      },
      {
        accessorKey: 'category',
        maxSize: isMobile ? 50 : 80,
        cell: renderCategoryCell,
      },
      {
        accessorKey: 'stats',
        maxSize: isMobile ? 120 : 125,
        cell: renderStatsCell,
      },
      ...(isMobile
        ? []
        : [
            {
              accessorKey: 'date_created',
              maxSize: isMobile ? 40 : 80,
              cell: renderDateCreatedCell,
            },
          ]),
    ],
    [loggedin, isMobile]
  );

  const posts = results?.results || [];
  const data = useMemo(
    () =>
      posts
        ?.filter((post) =>
          filters?.categoryFilter
            ? post.category === filters.categoryFilter.value
            : true
        )
        ?.map((post) => ({
          ...post,
          author: post.author_profile?.username,
          loggedInUser: user?.username,
        })) || [],
    [posts, user, filters?.categoryFilter]
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
        options={{
          getRowId: (row) => row.id,
          state: { globalFilter: filters?.search },
        }}
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
          sx: {
            borderTop: 0.5,
            borderColor: 'grey.600',
            fontSize: { xs: '0.95em', md: '1.15em' },
          },
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
