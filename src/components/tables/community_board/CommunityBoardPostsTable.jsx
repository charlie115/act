import React, { useEffect, useMemo, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Pagination from '@mui/material/Pagination';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import Chip from '@mui/material/Chip';

import { alpha, useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import { useGetBoardPostsQuery } from 'redux/api/drf/board';

import { usePrevious } from '@uidotdev/usehooks';

import CommentIcon from '@mui/icons-material/Comment';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import VisibilityIcon from '@mui/icons-material/Visibility';
import PersonIcon from '@mui/icons-material/Person';
import AccessTimeIcon from '@mui/icons-material/AccessTime';

import { DateTime } from 'luxon';
import formatIntlNumber from 'utils/formatIntlNumber';
import { POST_CATEGORY_LIST } from 'constants/lists';

export default function CommunityBoardPostsTable({ filters }) {
  const location = useLocation();
  const navigate = useNavigate();

  const theme = useTheme();
  const [noOfPages, setNoOfPages] = useState();
  const [page, setPage] = useState(1);

  const { user } = useSelector((state) => state.auth);

  const {
    data: results,
    isError,
    isFetching,
  } = useGetBoardPostsQuery({ page });

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

  // Custom post renderer for both mobile and desktop
  const renderPost = (post) => {
    const category = POST_CATEGORY_LIST.find((o) => o.value === post.category);
    
    return (
      <Box 
        key={post.id}
        sx={{
          p: 1,  // Reduced padding
          mb: 1,  // Reduced margin
          borderRadius: 1,
          cursor: 'pointer',
          backgroundColor: alpha(category?.color || theme.palette.grey[300], 0.04),
          borderLeft: `4px solid ${category?.color || theme.palette.grey[300]}`,
          '&:hover': { 
            backgroundColor: alpha(theme.palette.info.main, 0.15) 
          }
        }}
        onClick={() => {
          navigate(`/community-board/post/${post.id}`, {
            state: { from: location },
          });
        }}
      >
        {/* First line: Title and Comments */}
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>  {/* Reduced margin */}
          <Typography 
            variant="body2"  // Smaller text
            sx={{ 
              fontWeight: 600,
              flexGrow: 1,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}
          >
            {post.title}
          </Typography>
          
          <Stack direction="row" alignItems="center" spacing={0.5} sx={{ minWidth: 'fit-content' }}>
            <CommentIcon sx={{ fontSize: 14 }} />
            <Typography variant="body2" color="text.secondary">
              {formatIntlNumber(post.comments)}
            </Typography>
          </Stack>
        </Stack>
        
        {/* Second line: Category, Author, Date, Views, Likes, Dislikes */}
        <Stack 
          direction="row" 
          spacing={1} 
          alignItems="center" 
          sx={{ 
            color: 'text.secondary',
            fontSize: '0.75rem'
          }}
        >
          <Chip 
            label={category?.getLabel()} 
            size="small"
            sx={{ 
              height: 18,  // Smaller height
              fontSize: '0.65rem',  // Smaller font
              backgroundColor: alpha(category?.color || theme.palette.grey[300], 0.2)
            }}
          />
          
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <PersonIcon sx={{ fontSize: 12 }} />
            <Typography variant="caption" noWrap>
              {post.author}
            </Typography>
          </Stack>
          
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <AccessTimeIcon sx={{ fontSize: 12 }} />
            <Typography variant="caption" noWrap>
              {DateTime.fromISO(post.date_created).toFormat('MM/dd HH:mm')}
            </Typography>
          </Stack>
          
          <Stack direction="row" spacing={1} sx={{ ml: 'auto' }}>
            <Stack direction="row" alignItems="center" spacing={0.5}>
              <VisibilityIcon sx={{ fontSize: 12 }} />
              <Typography variant="caption">
                {formatIntlNumber(post.views)}
              </Typography>
            </Stack>
            
            <Stack direction="row" alignItems="center" spacing={0.5}>
              <ThumbUpIcon sx={{ fontSize: 12 }} />
              <Typography variant="caption">
                {formatIntlNumber(post.likes)}
              </Typography>
            </Stack>
            
            <Stack direction="row" alignItems="center" spacing={0.5}>
              <ThumbDownIcon sx={{ fontSize: 12 }} />
              <Typography variant="caption">
                {formatIntlNumber(post.dislikes)}
              </Typography>
            </Stack>
          </Stack>
        </Stack>
      </Box>
    );
  };

  return (
    <>
      {isFetching && data.length === 0 ? (
        // Loading state with static keys
        [
          'skeleton-header',
          'skeleton-content-1',
          'skeleton-content-2',
          'skeleton-content-3',
          'skeleton-footer'
        ].map((skeletonKey) => (
          <Box 
            key={skeletonKey}
            sx={{
              p: 1,
              mb: 1,
              borderRadius: 1,
              backgroundColor: alpha(theme.palette.grey[300], 0.1),
              height: 60,
              animation: 'pulse 1.5s infinite ease-in-out',
              '@keyframes pulse': {
                '0%': { opacity: 0.6 },
                '50%': { opacity: 0.3 },
                '100%': { opacity: 0.6 },
              }
            }}
          />
        ))
      ) : (
        data.map(renderPost)
      )}
      
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
    </>
  );
}
