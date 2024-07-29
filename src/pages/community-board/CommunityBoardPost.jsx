import React, { useEffect, useRef, useState } from 'react';

import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';

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
import MUILink from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';

import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CommentIcon from '@mui/icons-material/Comment';
import PersonIcon from '@mui/icons-material/Person';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import VisibilityIcon from '@mui/icons-material/Visibility';

import { Controller, useForm } from 'react-hook-form';

import { useSelector } from 'react-redux';

import {
  useGetBoardCommentsQuery,
  useGetBoardPostByIdQuery,
  useDeleteBoardPostReactionsMutation,
  usePostBoardCommentMutation,
  usePatchBoardPostReactionsMutation,
  usePostBoardPostReactionsMutation,
  usePostBoardPostViewsMutation,
} from 'redux/api/drf/board';

import { useTranslation } from 'react-i18next';

import { DateTime } from 'luxon';

import isNumber from 'lodash/isNumber';

import formatIntlNumber from 'utils/formatIntlNumber';

import CommunityBoardComment from 'components/CommunityBoardComment';
import RichTextEditor from 'components/RichTextEditor';

import { POST_REACTION_TYPE } from 'constants';

export default function CommunityBoardPost() {
  const commentInputRef = useRef();
  const quillRef = useRef();

  const location = useLocation();
  const navigate = useNavigate();
  const params = useParams();

  const { loggedin, user } = useSelector((state) => state.auth);

  const { t } = useTranslation();

  const [addComment, setAddComment] = useState(false);

  const [reaction, setReaction] = useState();

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

  const [deleteReactions] = useDeleteBoardPostReactionsMutation();
  const [patchReactions] = usePatchBoardPostReactionsMutation();
  const [postReactions] = usePostBoardPostReactionsMutation();
  const [postViews] = usePostBoardPostViewsMutation();

  const [createComment, { isLoading, isSuccess }] =
    usePostBoardCommentMutation();

  const onPostReaction = (e, newReaction) => {
    if (post.user_reaction) {
      if (newReaction)
        patchReactions({ id: post.user_reaction.id, reaction: newReaction });
      else deleteReactions(post.user_reaction.id);
    } else
      postReactions({ post: post.id, user: user.uuid, reaction: newReaction });
  };

  const onSubmit = (data) => {
    createComment({ author: user?.uuid, post: params?.postId, ...data });
  };

  useEffect(() => {
    if (user && isNumber(post?.id)) {
      if (post.user_view) {
        const lastView = DateTime.fromISO(post.user_view).setZone('Asia/Seoul');
        if (lastView < DateTime.now().setZone('Asia/Seoul').startOf('day'))
          postViews({ post: post.id, user: user.uuid });
      } else postViews({ post: post.id, user: user.uuid });
    }
  }, [post?.id, user]);

  useEffect(() => {
    if (post?.user_reaction)
      setReaction(POST_REACTION_TYPE[post.user_reaction.reaction].value);
    else setReaction();
  }, [post?.user_reaction]);

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
        onClick={() => navigate('/community-board')}
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
              <Box>{post?.author_profile?.username}</Box>
            </Stack>
            <Box component="small" sx={{ color: 'secondary.main' }}>
              {DateTime.fromISO(post?.date_created).toLocaleString(
                DateTime.DATETIME_MED
              )}
            </Box>
          </Box>
          <Stack alignItems="center" direction="row" spacing={1}>
            <Box>
              <CommentIcon sx={{ fontSize: 11.5 }} />{' '}
              {formatIntlNumber(post.comments)}
            </Box>
            <Divider orientation="vertical" flexItem />
            <Box>
              <VisibilityIcon sx={{ fontSize: 11.5 }} />{' '}
              {formatIntlNumber(post.views)}
            </Box>
            <Divider orientation="vertical" flexItem />
            <Box>
              <ThumbUpIcon sx={{ fontSize: 11.5 }} />{' '}
              {formatIntlNumber(post.likes)}
            </Box>
            <Box>
              <ThumbDownIcon sx={{ fontSize: 11.5 }} />{' '}
              {formatIntlNumber(post.dislikes)}
            </Box>
            {loggedin && (
              <ToggleButtonGroup
                exclusive
                color="secondary"
                size="small"
                value={reaction}
                onChange={onPostReaction}
                sx={{ margin: '0 0 0 24px!important' }}
              >
                {['LIKE', 'DISLIKE'].map((value) => {
                  const { icon: Icon } = POST_REACTION_TYPE[value];
                  return (
                    <ToggleButton key={value} value={value} aria-label={value}>
                      <Icon
                        color={value === reaction ? 'primary' : undefined}
                        sx={{ fontSize: 16 }}
                      />
                    </ToggleButton>
                  );
                })}
              </ToggleButtonGroup>
            )}
          </Stack>
        </Stack>
        <Card sx={{ clear: 'both', my: 2, p: { sm: 2, md: 4 } }}>
          <RichTextEditor readOnly ref={quillRef} />
        </Card>
        <Divider sx={{ my: 2 }} />
        <Typography variant="h6" sx={{ display: 'inline', mr: 1 }}>
          {t('Comments')} ({formatIntlNumber(post.comments)})
        </Typography>
        {loggedin ? (
          !addComment && (
            <Button
              disableRipple
              color="info"
              size="small"
              variant="outlined"
              endIcon={<AddIcon />}
              sx={{ p: 0.25 }}
              onClick={() => setAddComment(true)}
            >
              {t('Add')}
            </Button>
          )
        ) : (
          <MUILink
            component={Link}
            to="/login"
            state={{ from: location }}
            sx={{ fontStyle: 'italic' }}
          >
            {t('Login to leave a comment')}
          </MUILink>
        )}
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
                    rows={3}
                    size="large"
                    readOnly={isLoading}
                    sx={{ my: 2, py: 0 }}
                    {...field}
                  />
                  <FormHelperText>{fieldState.error?.message}</FormHelperText>
                </FormControl>
              )}
            />
            <Button onClick={() => setAddComment(false)} sx={{ mr: 2 }}>
              {t('Cancel')}
            </Button>
            <LoadingButton
              type="submit"
              variant="contained"
              disabled={!isDirty || !isValid}
              loading={isLoading}
            >
              {t('Add Comment')}
            </LoadingButton>
          </Box>
        </Collapse>
        {comments?.map((comment) => (
          <Card key={comment.id} sx={{ mt: 2 }}>
            <CommunityBoardComment
              isParentComment
              post={post}
              comment={comment}
              user={user}
            />
          </Card>
        ))}
      </Box>
    </Paper>
  );
}
