import React, { useEffect, useRef, useState } from 'react';

import { Navigate, useLocation, useNavigate } from 'react-router-dom';

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
import { useTheme, useMediaQuery } from '@mui/material';

import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CircleIcon from '@mui/icons-material/Circle';

import { Controller, useForm } from 'react-hook-form';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';
import { usePostBoardPostMutation } from 'redux/api/drf/board';

import mime from 'mime';

import useGlobalSnackbar from 'hooks/useGlobalSnackbar';

import RichTextEditor from 'components/RichTextEditor';

import { USER_ROLE } from 'constants';
import { POST_CATEGORY_LIST } from 'constants/lists';

export default function CommunityBoardPostNew() {
  const quillRef = useRef();

  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const { t } = useTranslation();

  const { loggedin, user } = useSelector((state) => state.auth);

  const { openSnackbar } = useGlobalSnackbar();

  const [categories, setCategories] = useState([]);

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
    const images = attachedImages
      ? await Promise.all(
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
        )
      : [];

    const formData = new FormData();
    formData.append('author', user.uuid);
    formData.append('title', data.title);
    formData.append('category', data.category);
    formData.append('content', newContent);

    images.forEach((image) => {
      formData.append('image', image);
    });

    createBoardPost(formData);
  };

  useEffect(() => {
    // Only admins and internal can post Announcement and User Guid
    // If user is not admin or internal, filter out these categories
    const allowedCategories =
      user.role === USER_ROLE.admin || user.role === USER_ROLE.internal
        ? POST_CATEGORY_LIST
        : POST_CATEGORY_LIST.filter(
            (category) =>
              category.value !== 'Announcement' && category.value !== 'User Guide'
          );

    setCategories(allowedCategories);
  }, [user]);

  useEffect(() => {
    if (isSuccess && boardPost) navigate(`/community-board/post/${boardPost.id}`);
  }, [boardPost, isSuccess, navigate]);

  useEffect(() => {
    if (isError)
      openSnackbar(t('An error occurred. Please try again.'), {
        alertProps: { severity: 'error' },
      });
  }, [isError, openSnackbar, t]);

  if (!loggedin)
    return <Navigate replace to="/login" state={{ from: location }} />;

  return (
    <Paper elevation={2} sx={{ p: { xs: 1.5, sm: 2 } }}>
      {isLoading && <LinearProgress />}
      <Button
        color="info"
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/community-board')}
        size={isMobile ? "small" : "medium"}
        sx={{ mb: { xs: 1, sm: 2 } }}
      >
        {t('Back')}
      </Button>
      <Box
        component="form"
        autoComplete="off"
        onSubmit={handleSubmit(onSubmit)}
        sx={{ p: { xs: 1, sm: 2 } }}
      >
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'flex-end',
          mb: { xs: 2, sm: 3 }
        }}>
          <Button
            type="submit"
            variant="contained"
            disabled={!isDirty || !isValid || isLoading}
            size={isMobile ? "small" : "medium"}
          >
            {t('Complete')}
          </Button>
        </Box>
        <Grid container spacing={isMobile ? 1 : 2}>
          <Grid item xs={12} md={8}>
            <Controller
              name="title"
              control={control}
              rules={{
                required: true,
                maxLength: { value: 150, message: t('Too many characters') },
              }}
              render={({ field, fieldState }) => (
                <FormControl
                  fullWidth
                  error={!!fieldState.error}
                  size={isMobile ? "small" : "large"}
                  sx={{ mb: { xs: 1.5, sm: 3 } }}
                >
                  <FormLabel>{t('Title')}</FormLabel>
                  <FilledInput
                    autoFocus
                    size={isMobile ? "small" : "large"}
                    readOnly={isLoading}
                    {...field}
                  />
                  <FormHelperText>{fieldState.error?.message}</FormHelperText>
                </FormControl>
              )}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Controller
              name="category"
              control={control}
              rules={{ required: true }}
              render={({ field, fieldState }) => (
                <FormControl
                  fullWidth
                  error={!!fieldState.error}
                  size={isMobile ? "small" : "large"}
                  sx={{ mb: { xs: 1.5, sm: 3 } }}
                  variant="filled"
                >
                  <FormLabel>{t('Category')}</FormLabel>
                  <Select
                    displayEmpty
                    disabled={isLoading}
                    inputProps={{ 'aria-label': 'Category' }}
                    size={isMobile ? "small" : "medium"}
                    {...field}
                  >
                    <MenuItem value="">
                      <em>{t('Please select a category')}</em>
                    </MenuItem>
                    {categories.map((category) => (
                      <MenuItem key={category.value} value={category.value}>
                        <CircleIcon
                          sx={{ color: category.color, fontSize: 12, mr: 1 }}
                        />
                        {category.getLabel()}
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
            <FormControl fullWidth error={!!fieldState.error} size={isMobile ? "small" : "large"}>
              <FormLabel sx={{ mb: 0.5 }}>{t('Content')}</FormLabel>
              <Paper sx={{ 
                minHeight: { xs: '200px', sm: '300px' },
                '& .ql-editor': {
                  minHeight: { xs: '150px', sm: '250px' }
                }
              }}>
                <RichTextEditor
                  showToolbar
                  ref={quillRef}
                  readOnly={isLoading}
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