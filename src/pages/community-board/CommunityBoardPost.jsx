import React, { useEffect, useMemo, useRef, useState } from 'react';

import { useNavigate, useParams } from 'react-router-dom';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import Collapse from '@mui/material/Collapse';
import Divider from '@mui/material/Divider';
import FilledInput from '@mui/material/FilledInput';
import FormControl from '@mui/material/FormControl';
import FormHelperText from '@mui/material/FormHelperText';
import LinearProgress from '@mui/material/LinearProgress';
import LoadingButton from '@mui/lab/LoadingButton';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CloseIcon from '@mui/icons-material/Close';
import CommentIcon from '@mui/icons-material/Comment';
import FavoriteIcon from '@mui/icons-material/Favorite';
import PersonIcon from '@mui/icons-material/Person';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import VisibilityIcon from '@mui/icons-material/Visibility';

import ShowMoreText from 'react-show-more-text';

import { Controller, useForm } from 'react-hook-form';

import { useSelector } from 'react-redux';

import {
  useGetBoardCommentsQuery,
  useGetBoardPostByIdQuery,
  usePostBoardCommentMutation,
  usePostBoardPostLikesMutation,
  usePostBoardPostViewsMutation,
} from 'redux/api/drf/board';

import { useTranslation } from 'react-i18next';

import { DateTime } from 'luxon';

import isNumber from 'lodash/isNumber';

import formatIntlNumber from 'utils/formatIntlNumber';

import CommunityBoardReply, {
  CommunityBoardReplyForm,
} from 'components/CommunityBoardReply';
import RichTextEditor from 'components/RichTextEditor';

function countReplies(comment) {
  let count = comment?.replies?.length || 0;
  comment?.replies?.forEach((reply) => {
    count += countReplies(reply);
  });

  return count;
}

export default function CommunityBoardPost() {
  const commentInputRef = useRef();
  const quillRef = useRef();

  const navigate = useNavigate();
  const params = useParams();

  const { user } = useSelector((state) => state.auth);

  const { t } = useTranslation();

  const [addComment, setAddComment] = useState(false);

  const { control, formState, handleSubmit, reset } = useForm({
    defaultValues: { content: '' },
    mode: 'all',
  });
  const { isDirty, isValid } = formState;

  const { data: comments } = useGetBoardCommentsQuery(
    { post: params?.postId },
    {
      skip: !params?.postId,
    }
  );
  const { data: post } = useGetBoardPostByIdQuery(params?.postId, {
    skip: !params?.postId,
  });
  const [postLikes] = usePostBoardPostLikesMutation();
  const [postViews] = usePostBoardPostViewsMutation();

  const [createComment, { isLoading, isSuccess }] =
    usePostBoardCommentMutation();

  const [expandReplies, setExpandReplies] = useState({});

  const onSubmit = (data) => {
    createComment({ user: user.uuid, post: params?.postId, ...data });
  };

  const postComments = useMemo(
    () =>
      comments?.map((comment) => {
        const noOfReplies = countReplies(comment);
        return { ...comment, noOfReplies };
      }),
    [comments]
  );

  useEffect(() => {
    if (isNumber(post?.id) && !post?.viewed)
      postViews({ post: post.id, user: user.uuid });
  }, [post?.id, user]);

  useEffect(() => {
    if (post?.content) {
      quillRef.current?.clipboard.dangerouslyPasteHTML(post.content, 'api');
    }
  }, [post?.content]);

  useEffect(() => {
    if (addComment) commentInputRef.current?.focus();
    else reset();
  }, [commentInputRef, addComment]);

  useEffect(() => {
    if (isSuccess) setAddComment(false);
  }, [isSuccess]);

  if (!post) return <LinearProgress />;

  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      <Button
        color="info"
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate(-1)}
      >
        {t('Back')}
      </Button>
      <Box sx={{ my: 2, p: { sm: 2, md: 4 } }}>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
          {post?.title}
        </Typography>
        <Stack
          alignItems="flex-end"
          direction="row"
          justifyContent="space-between"
        >
          <Box>
            <Stack alignItems="center" direction="row" spacing={0.5}>
              <PersonIcon fontSize="small" />
              <Box>{post?.user_profile?.username}</Box>
            </Stack>
            <Box component="small" sx={{ color: 'secondary.main' }}>
              {DateTime.fromISO(post?.date_created).toLocaleString(
                DateTime.DATETIME_MED
              )}
            </Box>
          </Box>
          <Button
            color="error"
            variant="contained"
            disabled={!post?.id || post?.liked}
            endIcon={<FavoriteIcon />}
            onClick={() => postLikes({ post: post?.id, user: user.uuid })}
            sx={{ px: 4 }}
          >
            {post?.liked ? t('Liked') : t('Like')}
          </Button>
          <Stack alignItems="center" direction="row" spacing={1}>
            <Box>
              <ThumbUpIcon sx={{ fontSize: 11.5 }} />{' '}
              {formatIntlNumber(post.likes)}
            </Box>
            <Divider orientation="vertical" flexItem />
            <Box>
              <CommentIcon sx={{ fontSize: 11.5 }} />{' '}
              {formatIntlNumber(post.comments)}
            </Box>
            <Divider orientation="vertical" flexItem />
            <Box>
              <VisibilityIcon sx={{ fontSize: 11.5 }} />{' '}
              {formatIntlNumber(post.views)}
            </Box>
          </Stack>
        </Stack>
        <Card sx={{ clear: 'both', my: 2, p: { sm: 2, md: 4 } }}>
          <RichTextEditor readOnly ref={quillRef} />
        </Card>
        <Divider sx={{ my: 2 }} />
        <Typography variant="h6">
          {t('Comments')} ({formatIntlNumber(post.comments)})
          <Button
            disableRipple
            color="info"
            size="small"
            variant={addComment ? 'contained' : 'outlined'}
            endIcon={addComment ? <CloseIcon /> : <AddIcon />}
            sx={{ mx: 2, p: 0.25 }}
            onClick={() => setAddComment((state) => !state)}
          >
            {t('Add')}
          </Button>
        </Typography>
        <Collapse in={addComment}>
          <Box
            component="form"
            autoComplete="off"
            onSubmit={handleSubmit(onSubmit)}
            sx={{ mb: 3 }}
          >
            <Controller
              name="content"
              control={control}
              rules={{ required: true }}
              render={({ field, fieldState }) => (
                <FormControl fullWidth error={!!fieldState.error} size="large">
                  <FilledInput
                    autoFocus
                    multiline
                    inputRef={commentInputRef}
                    rows={2}
                    size="large"
                    // readOnly={isLoading}
                    sx={{ my: 2, py: 2 }}
                    {...field}
                  />
                  <FormHelperText>{fieldState.error?.message}</FormHelperText>
                </FormControl>
              )}
            />
            <LoadingButton
              type="submit"
              variant="contained"
              disabled={!isDirty || !isValid}
              loading={isLoading}
            >
              {t('Leave Comment')}
            </LoadingButton>
          </Box>
        </Collapse>
        {postComments?.map((comment) => (
          <Card key={comment.id} sx={{ mt: 2 }}>
            <Stack
              alignItems="center"
              direction="row"
              spacing={1}
              sx={{ p: 1 }}
            >
              <PersonIcon sx={{ fontSize: 14 }} />
              <Box component="small" sx={{ fontWeight: 700 }}>
                {comment.user_profile?.username}
              </Box>
              <Divider orientation="vertical" flexItem />
              <Tooltip
                placement="top"
                title={DateTime.fromISO(comment.date_created).toLocaleString(
                  DateTime.DATETIME_MED
                )}
              >
                <Box
                  component="small"
                  sx={{ color: 'secondary.main', cursor: 'pointer' }}
                >
                  {DateTime.fromISO(comment.date_created).toRelativeCalendar()}
                </Box>
              </Tooltip>
            </Stack>
            <Divider />
            <Box sx={{ p: 2 }}>
              <ShowMoreText
                lines={3}
                more={t('Show more')}
                less={t('Show less')}
                anchorClass="show-more-or-less"
              >
                <Typography gutterBottom>{comment.content}</Typography>
              </ShowMoreText>
              <CommunityBoardReplyForm
                parent={comment}
                post={post}
                user={user}
                onExpandReplies={() =>
                  setExpandReplies((state) => ({
                    ...state,
                    [comment.id]: state[comment.id] ? undefined : true,
                  }))
                }
                onSuccess={() =>
                  setExpandReplies((state) => ({
                    ...state,
                    [comment.id]: true,
                  }))
                }
              />
              {expandReplies[comment.id] &&
                comment.replies?.map((reply) => (
                  <CommunityBoardReply
                    key={reply.id}
                    post={post}
                    reply={reply}
                    user={user}
                  />
                ))}
            </Box>
          </Card>
        ))}
      </Box>
    </Paper>
  );
}
