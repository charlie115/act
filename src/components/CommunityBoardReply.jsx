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

import { useTheme } from '@mui/material/styles';

import ShowMoreText from 'react-show-more-text';

import { Controller, useForm } from 'react-hook-form';

import { usePostBoardCommentMutation } from 'redux/api/drf/board';

import { useTranslation } from 'react-i18next';

import { DateTime } from 'luxon';

export default function CommunityBoardReply({ post, reply, user }) {
  const theme = useTheme();

  const { t } = useTranslation();

  const [expandReplies, setExpandReplies] = useState({});

  return (
    <Box
      sx={{
        borderLeft: 1,
        borderColor: theme.palette.divider,
        borderRadius: 2,
        ml: 2,
        pl: 2,
      }}
    >
      <Box sx={{ p: 0 }}>
        <Stack alignItems="center" direction="row" spacing={1} sx={{ mb: 1 }}>
          <Box component="small" sx={{ fontWeight: 700 }}>
            {reply.user_profile.username}
          </Box>
          <Divider orientation="vertical" flexItem />
          <Tooltip
            placement="top"
            title={DateTime.fromISO(reply.date_created).toLocaleString(
              DateTime.DATETIME_MED
            )}
            sx={{ bgcolor: 'red', width: '50%' }}
          >
            <Box
              component="small"
              sx={{ color: 'secondary.main', cursor: 'pointer' }}
            >
              {DateTime.fromISO(reply.date_created).toRelativeCalendar()}
            </Box>
          </Tooltip>
        </Stack>
        <ShowMoreText
          lines={3}
          more={t('Show more')}
          less={t('Show less')}
          anchorClass="show-more-or-less"
        >
          <Typography>{reply.content}</Typography>
        </ShowMoreText>
        <CommunityBoardReplyForm
          parent={{ ...reply, noOfReplies: reply.replies?.length }}
          post={post}
          user={user}
          onExpandReplies={() => {
            setExpandReplies((state) => ({
              ...state,
              [reply.id]: state[reply.id] ? undefined : true,
            }));
          }}
          onSuccess={() =>
            setExpandReplies((state) => ({
              ...state,
              [reply.id]: true,
            }))
          }
        />
      </Box>
      {expandReplies[reply.id] &&
        reply.replies?.length > 0 &&
        reply.replies.map((item) => (
          <CommunityBoardReply
            key={item.id}
            post={post}
            reply={item}
            user={user}
          />
        ))}
    </Box>
  );
}

export function CommunityBoardReplyForm({
  parent,
  post,
  user,
  onExpandReplies,
  onSuccess,
}) {
  const inputRef = useRef();

  const { t } = useTranslation();

  const [open, setOpen] = useState(false);

  const [createComment, { isLoading, isSuccess }] =
    usePostBoardCommentMutation();

  const { control, formState, handleSubmit, reset } = useForm({
    defaultValues: { content: '' },
    mode: 'all',
  });
  const { isDirty, isValid } = formState;

  const onSubmit = (data) => {
    createComment({
      user: user.uuid,
      parent: parent.id,
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
    <Box sx={{ mb: 2, mt: 1 }}>
      <Stack alignItems="center" direction="row" spacing={1}>
        <Typography
          gutterBottom
          onClick={() => onExpandReplies(true)}
          sx={{
            color: 'secondary.main',
            cursor: parent.noOfReplies > 0 ? 'pointer' : undefined,
            fontSize: 12,
            opacity: parent.noOfReplies === 0 ? 0.5 : undefined,
          }}
        >
          {t('{{count, number}} replies', {
            count: parent.noOfReplies,
          })}
        </Typography>
        <Link
          component="button"
          underline="hover"
          onClick={() => setOpen((state) => !state)}
          sx={{ color: open ? 'error.light' : 'info.main', fontSize: 12 }}
        >
          {t('Reply')} {open && `(${t('Cancel')})`}
        </Link>
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
                  rows={1}
                  size="large"
                  readOnly={isLoading}
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
            {t('Add Reply')}
          </LoadingButton>
        </Box>
      </Collapse>
    </Box>
  );
}
