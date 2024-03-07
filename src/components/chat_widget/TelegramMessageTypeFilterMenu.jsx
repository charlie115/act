import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import { tooltipClasses } from '@mui/material/Tooltip';

import CheckBoxIcon from '@mui/icons-material/CheckBox';
import ErrorIcon from '@mui/icons-material/Error';
import FilterListIcon from '@mui/icons-material/FilterList';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';

import { useTranslation } from 'react-i18next';

import { StyledTooltip } from './StyledChatComponents';

export default function TelegramMessageTypeFilterMenu({ display, onChange }) {
  const { i18n, t } = useTranslation();

  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const [options, setOptions] = useState([]);
  const [selected, setSelected] = useState(null);

  const handleClick = (event) => setAnchorEl(event.currentTarget);
  const handleClose = () => setAnchorEl(null);
  const handleSelect = (value) => setSelected(value);

  useEffect(() => {
    if (selected) onChange(selected.value);
  }, [selected]);

  useEffect(() => {
    const messageTypes = [
      {
        label: t('All'),
        value: 'ALL',
        icon: <CheckBoxIcon color="secondary" fontSize="small" />,
        color: 'secondary',
      },
      {
        label: t('Warning'),
        value: 'warning',
        icon: <WarningIcon color="warning" fontSize="small" />,
        color: 'warning',
      },
      {
        label: t('Info'),
        value: 'info',
        icon: <InfoIcon color="info" fontSize="small" />,
        color: 'info',
      },
      {
        label: t('Error'),
        value: 'error',
        icon: <ErrorIcon color="error" fontSize="small" />,
        color: 'error',
      },
    ];
    setOptions(messageTypes);
    setSelected((state) => state || messageTypes[0]);
  }, [i18n.language]);

  return (
    <>
      <Box sx={{ position: 'absolute', top: 0, right: 5, zIndex: 1 }}>
        <StyledTooltip
          arrow
          title={selected?.label}
          open={display && selected?.value !== 'ALL'}
          slotProps={{
            popper: {
              modifiers: [
                {
                  name: 'offset',
                  options: { offset: [0, -14] },
                },
              ],
            },
          }}
          sx={{
            [`& .${tooltipClasses.tooltip}`]: {
              color: `${selected?.color}.main`,
            },
          }}
        >
          <IconButton
            color={selected?.color || 'secondary'}
            size="small"
            onClick={handleClick}
            aria-controls={open ? 'telegram-filter-menu' : undefined}
            aria-expanded={open ? 'true' : undefined}
            aria-haspopup="true"
          >
            <FilterListIcon />
          </IconButton>
        </StyledTooltip>
      </Box>
      <Menu
        anchorEl={anchorEl}
        id="account-menu"
        open={open}
        onClose={handleClose}
        onClick={handleClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            '& li': { textTransform: 'uppercase' },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        {options.map((option) => (
          <MenuItem
            key={option.value}
            onClick={() => {
              handleSelect(option);
              handleClose();
            }}
            selected={selected?.value === option.value}
          >
            <ListItemIcon>{option.icon}</ListItemIcon>
            {option.label}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}
