import React, { useState } from 'react';

import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import OutlinedInput from '@mui/material/OutlinedInput';
import Paper from '@mui/material/Paper';
import Tooltip from '@mui/material/Tooltip';

import AddIcon from '@mui/icons-material/Add';
import CircleIcon from '@mui/icons-material/Circle';
import CloseIcon from '@mui/icons-material/Close';
import FilterListIcon from '@mui/icons-material/FilterList';
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

  const [categoryFilter, setCategoryFilter] = useState();

  const [searchValue, setSearchValue] = useState('');
  const globalFilter = useDebounce(searchValue, 300);

  const [anchorEl, setAnchorEl] = React.useState(null);
  const open = Boolean(anchorEl);

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleSelectCategoryFilter = (value) => {
    setCategoryFilter(value);
    setAnchorEl(null);
  };

  if (location.pathname.includes('post'))
    return (
      <Box sx={{ flex: 1, p: 2 }}>
        <Outlet />
      </Box>
    );

  return (
    <Box sx={{ flex: 1, p: 2 }}>
      <Paper elevation={2} sx={{ minHeight: '100%', p: 2 }}>
        <Grid container>
          <Grid item md>
            {loggedin && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() =>
                  navigate('/community-board/post/new', {
                    state: { from: location },
                  })
                }
                sx={{ mb: 4 }}
              >
                {t('New')}
              </Button>
            )}
          </Grid>
          <Grid
            item
            md
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'flex-end',
            }}
          >
            <Tooltip title={t('Filter by category')}>
              <IconButton
                id="board-category-button"
                aria-controls={open ? 'board-category-menu' : undefined}
                aria-haspopup="true"
                aria-expanded={open ? 'true' : undefined}
                onClick={handleMenuClick}
                sx={{ mr: 2 }}
              >
                <Badge
                  color="transparent"
                  variant="dot"
                  invisible={!categoryFilter}
                  anchorOrigin={{ vertical: 'top', horizontal: 'left' }}
                  sx={{
                    '& .MuiBadge-badge': { bgcolor: categoryFilter?.color },
                  }}
                >
                  <FilterListIcon />
                </Badge>
              </IconButton>
            </Tooltip>
            <Menu
              id="board-category-menu"
              anchorEl={anchorEl}
              anchorOrigin={{ horizontal: -60, vertical: 'bottom' }}
              open={open}
              onClose={() => setAnchorEl(null)}
              MenuListProps={{
                'aria-labelledby': 'board-category-button',
              }}
            >
              {POST_CATEGORY_LIST.map((item) => (
                <MenuItem
                  key={item.value}
                  onClick={() => handleSelectCategoryFilter(item)}
                >
                  <CircleIcon sx={{ color: item.color, fontSize: 12, mr: 1 }} />
                  {item.getLabel()}
                </MenuItem>
              ))}
              <Divider />
              <MenuItem
                disabled={!categoryFilter}
                onClick={() => handleSelectCategoryFilter()}
              >
                {t('Clear')}
              </MenuItem>
            </Menu>
            <OutlinedInput
              size="small"
              placeholder={t('Search')}
              onChange={(e) => setSearchValue(e.target.value)}
              value={searchValue}
              startAdornment={
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              }
              endAdornment={
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
