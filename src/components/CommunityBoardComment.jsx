import React, { useEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import Divider from '@mui/material/Divider';
import FilledInput from '@mui/material/FilledInput';
import FormControl from '@mui/material/FormControl';
import FormHelperText from '@mui/material/FormHelperText';
import Link from '@mui/material/Link';
import LoadingButton from '@mui/lab/LoadingButton';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import PersonIcon from '@mui/icons-material/Person';

import { useTheme } from '@mui/material/styles';

import ShowMoreText from 'react-show-more-text';

import { Controller, useForm } from 'react-hook-form';

import {
  useDeleteBoardCommentReactionsMutation,
  usePatchBoardCommentReactionsMutation,
  usePostBoardCommentMutation,
  usePostBoardCommentReactionsMutation,
} from 'redux/api/drf/board';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';

import { DateTime } from 'luxon';

import { POST_REACTION_TYPE } from 'constants';

export default function CommunityBoardComment({
  post,
  comment,
  user,
  isParentComment,
}) {
  const theme = useTheme();

  const { t } = useTranslation();

  const { loggedin } = useSelector((state) => state.auth);

  const [expandReplies, setExpandReplies] = useState({});

  return (
    <Box
      sx={
        isParentComment
          ? undefined
          : {
              borderLeft: 1,
              borderColor: theme.palette.divider,
              borderRadius: 2,
              mb: 1,
              ml: 2,
              pl: 2,
            }
      }
    >
      <Box sx={{ p: 0 }}>
        <Stack
          alignItems="center"
          direction="row"
          spacing={1}
          sx={isParentComment ? { p: 1 } : { px: 1 }}
        >
          <PersonIcon sx={{ fontSize: 14 }} />
          <Box component="small" sx={{ fontWeight: 700 }}>
            {comment.author_profile.username}
          </Box>
          <Divider orientation="vertical" flexItem />
          <Tooltip
            placement="right"
            title={DateTime.fromISO(comment.date_created).toLocaleString(
              DateTime.DATETIME_MED
            )}
            sx={{ width: '50%' }}
          >
            <Box
              component="small"
              sx={{ color: 'secondary.main', cursor: 'pointer' }}
            >
              {DateTime.fromISO(comment.date_created).toRelativeCalendar()}
            </Box>
          </Tooltip>
        </Stack>
        {isParentComment && <Divider />}
        <Box sx={{ p: 1 }}>
          <ShowMoreText
            keepNewLines
            lines={3}
            more={t('Show more')}
            less={t('Show less')}
            anchorClass="show-more-or-less"
          >
            {comment.content}
          </ShowMoreText>
        </Box>
        <CommunityBoardCommentBottomSection
          comment={comment}
          post={post}
          user={user}
          loggedin={loggedin}
          onExpandReplies={() => {
            setExpandReplies((state) => ({
              ...state,
              [comment.id]: state[comment.id] ? undefined : true,
            }));
          }}
          onSuccess={() =>
            setExpandReplies((state) => ({
              ...state,
              [comment.id]: true,
            }))
          }
        />
      </Box>
      {expandReplies[comment.id] &&
        comment.replies?.length > 0 &&
        comment.replies.map((item) => (
          <CommunityBoardComment
            key={item.id}
            post={post}
            comment={item}
            user={user}
          />
        ))}
    </Box>
  );
}

export function CommunityBoardCommentBottomSection({
  comment,
  post,
  user,
  loggedin,
  onExpandReplies,
  onSuccess,
}) {
  const inputRef = useRef();

  const { t } = useTranslation();

  const [open, setOpen] = useState(false);

  const [createComment, { isLoading, isSuccess }] =
    usePostBoardCommentMutation();

  const [deleteReactions] = useDeleteBoardCommentReactionsMutation();
  const [patchReactions] = usePatchBoardCommentReactionsMutation();
  const [postReactions] = usePostBoardCommentReactionsMutation();

  const { control, formState, handleSubmit, reset } = useForm({
    defaultValues: { content: '' },
    mode: 'all',
  });
  const { isDirty, isValid } = formState;

  const onReaction = (value) => {
    if (comment.user_reaction) {
      if (comment.user_reaction.reaction !== value)
        patchReactions({ id: comment.user_reaction.id, reaction: value });
      else deleteReactions(comment.user_reaction.id);
    } else
      postReactions({ comment: comment.id, user: user.uuid, reaction: value });
  };
  const onSubmit = (data) => {
    createComment({
      author: user.uuid,
      parent: comment.id,
      post: post.id,
      ...data,
    });
  };

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (isSuccess) {
      reset();
      setOpen(false);
      onSuccess();
    }
  }, [isSuccess]);

  return (
    <Box sx={{ pb: 1, px: 1 }}>
      <Stack alignItems="center" direction="row" spacing={1}>
        {['LIKE', 'DISLIKE'].map((value) => {
          const { icon: Icon } = POST_REACTION_TYPE[value];
          const isReaction = comment.user_reaction?.reaction === value;
          return (
            <Stack
              alignItems="center"
              direction="row"
              key={value}
              spacing={0.5}
            >
              <Icon
                color={isReaction ? 'info' : 'secondary'}
                onClick={() => onReaction(value)}
                sx={{
                  cursor: 'pointer',
                  fontSize: 14,
                  ':hover': { color: 'info.main', opacity: 0.75 },
                }}
              />
              <Typography sx={{ color: 'secondary.main' }}>
                {comment[`${value.toLowerCase()}s`]}
              </Typography>
            </Stack>
          );
        })}
        <Divider orientation="vertical" flexItem sx={{ opacity: 0 }} />
        <Typography
          gutterBottom
          onClick={() => onExpandReplies(true)}
          sx={{
            color: 'secondary.main',
            cursor: comment.replies?.length > 0 ? 'pointer' : undefined,
            fontSize: 12,
            opacity: comment.replies?.length === 0 ? 0.5 : undefined,
          }}
        >
          {t('{{count, number}} replies', {
            count: comment.replies?.length ?? 0,
          })}
        </Typography>
        {loggedin && (
          <Link
            component="button"
            underline="hover"
            onClick={() => setOpen((state) => !state)}
            sx={{ color: open ? 'error.light' : 'info.main', fontSize: 12 }}
          >
            {t('Reply')} {open && `(${t('Cancel')})`}
          </Link>
        )}
      </Stack>
      <Collapse in={open}>
        <Box
          component="form"
          autoComplete="off"
          onSubmit={handleSubmit(onSubmit)}
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
                  inputRef={inputRef}
                  rows={2}
                  size="large"
                  readOnly={isLoading}
                  sx={{ my: 2, py: 0 }}
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
            {t('Add Reply')}
          </LoadingButton>
        </Box>
      </Collapse>
    </Box>
  );
}
