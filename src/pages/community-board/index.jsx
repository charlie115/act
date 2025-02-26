import React, { useState, useEffect } from 'react';

import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import MenuItem from '@mui/material/MenuItem';
import OutlinedInput from '@mui/material/OutlinedInput';
import Paper from '@mui/material/Paper';
import FormControl from '@mui/material/FormControl';
import Select from '@mui/material/Select';
import InputLabel from '@mui/material/InputLabel';
import Typography from '@mui/material/Typography';
import { useTheme, useMediaQuery } from '@mui/material';

import AddIcon from '@mui/icons-material/Add';
import CircleIcon from '@mui/icons-material/Circle';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';

import { useTranslation } from 'react-i18next';
import { useSelector } from 'react-redux';
import { useDebounce } from '@uidotdev/usehooks';

import CommunityBoardPostsTable from 'components/tables/community_board/CommunityBoardPostsTable';
import { POST_CATEGORY_LIST } from 'constants/lists';

export default function CommunityBoard() {
  const location = useLocation();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { loggedin } = useSelector((state) => state.auth);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [categoryFilter, setCategoryFilter] = useState();
  const [searchValue, setSearchValue] = useState('');
  const globalFilter = useDebounce(searchValue, 300);

  useEffect(() => {
    if (location.state?.category) {
      const selected = POST_CATEGORY_LIST.find(
        (item) => item.value === location.state.category
      );
      if (selected) {
        setCategoryFilter(selected);
      }
    }
  }, [location.state]);

  if (location.pathname.includes('post'))
    return (
      <Box sx={{ flex: 1, p: { xs: 1, sm: 2 } }}>
        <Outlet />
      </Box>
    );

  return (
    <Box sx={{ flex: 1, p: { xs: 1, sm: 2 } }}>
      <Paper elevation={3} sx={{ p: { xs: 1.5, sm: 3 } }}>
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={12} display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h5" component="h1" sx={{ 
              fontSize: { xs: '1.25rem', sm: '1.5rem' },
              fontWeight: 600 
            }}>
              {t('Community Board')}
            </Typography>
            
            {loggedin && (
              <Button
                variant="contained"
                color="primary"
                size={isMobile ? "small" : "medium"}
                startIcon={<AddIcon />}
                onClick={() => navigate('post/new')}
                sx={{ 
                  whiteSpace: 'nowrap',
                  fontSize: { xs: '0.75rem', sm: '0.875rem' }
                }}
              >
                {t('New Post')}
              </Button>
            )}
          </Grid>
          
          <Grid 
            item 
            xs={12} 
            sx={{ 
              display: 'flex', 
              flexDirection: { xs: 'column', sm: 'row' },
              gap: { xs: 1.5, sm: 2 }
            }}
          >
            <FormControl 
              variant="outlined" 
              size="small" 
              sx={{ 
                width: { xs: '100%', sm: 180 },
                minWidth: { xs: '100%', sm: 180 }
              }}
            >
              <InputLabel>{t('Category')}</InputLabel>
              <Select
                label={t('Category')}
                value={categoryFilter?.value || ''}
                onChange={(e) => {
                  const selected = POST_CATEGORY_LIST.find(item => item.value === e.target.value);
                  setCategoryFilter(selected || undefined);
                }}
              >
                <MenuItem value="">
                  {t('All')}
                </MenuItem>
                {POST_CATEGORY_LIST.map((item) => (
                  <MenuItem key={item.value} value={item.value}>
                    <CircleIcon sx={{ color: item.color, fontSize: 12, mr: 1 }} />
                    {item.getLabel()}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <OutlinedInput
              size="small"
              placeholder={t('Search')}
              onChange={(e) => setSearchValue(e.target.value)}
              value={searchValue}
              fullWidth
              sx={{
                height: { xs: '40px', sm: '40px' },
                fontSize: { xs: '0.875rem', sm: '1rem' }
              }}
              startAdornment={
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              }
              endAdornment={
                searchValue ? (
                  <InputAdornment position="end">
                    <IconButton
                      edge="end"
                      onClick={() => {
                        setSearchValue('');
                      }}
                    >
                      <CloseIcon />
                    </IconButton>
                  </InputAdornment>
                ) : null
              }
            />
          </Grid>
        </Grid>

        <CommunityBoardPostsTable
          filters={{ search: globalFilter, categoryFilter }}
        />
      </Paper>
    </Box>
  );
}