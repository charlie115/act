import React, { useEffect, useRef } from 'react';

import { useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FilledInput from '@mui/material/FilledInput';
import FormControl from '@mui/material/FormControl';
import FormHelperText from '@mui/material/FormHelperText';
import FormLabel from '@mui/material/FormLabel';
import Grid from '@mui/material/Grid';
import LinearProgress from '@mui/material/LinearProgress';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Select from '@mui/material/Select';

import ArrowBackIcon from '@mui/icons-material/ArrowBack';

import { Controller, useForm } from 'react-hook-form';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';
import {
  useGetBoardPostCategoryQuery,
  usePostBoardPostMutation,
} from 'redux/api/drf/board';

import mime from 'mime';

import useGlobalSnackbar from 'hooks/useGlobalSnackbar';

import RichTextEditor from 'components/RichTextEditor';

export default function CommunityBoardPostNew() {
  const quillRef = useRef();

  const navigate = useNavigate();

  const { t } = useTranslation();

  const { user } = useSelector((state) => state.auth);

  const { openSnackbar } = useGlobalSnackbar();

  const { data: categories, isFetching } = useGetBoardPostCategoryQuery();

  const [createBoardPost, { data: boardPost, isError, isLoading, isSuccess }] =
    usePostBoardPostMutation();

  const { control, formState, handleSubmit } = useForm({
    defaultValues: { title: '', category: '', content: '' },
    mode: 'all',
  });
  const { isDirty, isValid } = formState;

  const onSubmit = async (data) => {
    const attachedImages = quillRef?.current
      ?.getContents()
      ?.filter((op) => op.insert?.image);

    let newContent = data.content;
    const images = await Promise.all(
      attachedImages.map(async (item) => {
        const image = await fetch(item.insert.image);
        const mimeType = image.headers.get('content-type');
        const fileName = item.insert.image.split('/').pop();
        const fileExtension = mime.getExtension(mimeType);

        newContent = newContent.replace(
          item.insert.image,
          `${fileName}.${fileExtension}`
        );

        const blob = await image.blob();
        return new File([blob], `${fileName}.${fileExtension}`, {
          type: blob.type,
        });
      })
    );

    const formData = new FormData();
    formData.append('user', user.uuid);
    formData.append('title', data.title);
    formData.append('category', data.category);
    formData.append('content', newContent);

    images.forEach((image) => {
      formData.append('images', image);
    });

    createBoardPost(formData);
  };

  useEffect(() => {
    if (isSuccess && boardPost)
      navigate(`/community-board/post/${boardPost.id}`);
  }, [boardPost, isSuccess]);

  useEffect(() => {
    if (isError)
      openSnackbar(t('An error occurred. Please try again.'), {
        alertProps: { severity: 'error' },
      });
  }, [isError]);

  const loading = isFetching || isLoading;

  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      {loading && <LinearProgress />}
      <Button
        color="info"
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/community-board')}
      >
        {t('Back')}
      </Button>
      <Box
        component="form"
        autoComplete="off"
        onSubmit={handleSubmit(onSubmit)}
        sx={{ p: 2 }}
      >
        <Button
          type="submit"
          variant="contained"
          disabled={!isDirty || !isValid || loading}
          sx={{ float: 'right', mb: 3 }}
        >
          {t('Post')}
        </Button>
        <Grid container spacing={2}>
          <Grid item md={8} sm={12}>
            <Controller
              name="title"
              control={control}
              rules={{ required: true }}
              render={({ field, fieldState }) => (
                <FormControl
                  fullWidth
                  error={!!fieldState.error}
                  size="large"
                  sx={{ mb: 3 }}
                >
                  <FormLabel>{t('Title')}</FormLabel>
                  <FilledInput
                    autoFocus
                    size="large"
                    readOnly={loading}
                    {...field}
                  />
                  <FormHelperText>{fieldState.error?.message}</FormHelperText>
                </FormControl>
              )}
            />
          </Grid>
          <Grid item md={4} sm={12}>
            <Controller
              name="category"
              control={control}
              rules={{ required: true }}
              render={({ field, fieldState }) => (
                <FormControl
                  fullWidth
                  error={!!fieldState.error}
                  size="large"
                  sx={{ mb: 3 }}
                  variant="filled"
                >
                  <FormLabel>{t('Category')}</FormLabel>
                  <Select
                    displayEmpty
                    disabled={loading}
                    inputProps={{ 'aria-label': 'Category' }}
                    {...field}
                  >
                    <MenuItem value="">
                      <em>{t('Please select a category')}</em>
                    </MenuItem>
                    {categories?.map((category) => (
                      <MenuItem key={category.code} value={category.name}>
                        {category.name}
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>{fieldState.error?.message}</FormHelperText>
                </FormControl>
              )}
            />
          </Grid>
        </Grid>
        <Controller
          name="content"
          control={control}
          rules={{ required: true }}
          render={({ field, fieldState }) => (
            <FormControl fullWidth error={!!fieldState.error} size="large">
              <FormLabel sx={{ mb: 0.5 }}>{t('Content')}</FormLabel>
              <Paper>
                <RichTextEditor
                  showToolbar
                  ref={quillRef}
                  readOnly={loading}
                  onTextChange={(change) => {
                    if (change?.ops?.[0]?.delete) field.onChange('');
                    else field.onChange(quillRef?.current?.getSemanticHTML());
                  }}
                />
              </Paper>
              <FormHelperText>{fieldState.error?.message}</FormHelperText>
            </FormControl>
          )}
        />
      </Box>
    </Paper>
  );
}
