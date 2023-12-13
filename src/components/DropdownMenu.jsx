import React, { useEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import Grow from '@mui/material/Grow';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import MenuItem from '@mui/material/MenuItem';
import MenuList from '@mui/material/MenuList';
import Paper from '@mui/material/Paper';
import Popper from '@mui/material/Popper';
import Tooltip from '@mui/material/Tooltip';

import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { usePrevious } from '@uidotdev/usehooks';

function DropdownMenu({
  options = [],
  value,
  onSelectItem,
  tooltipTitle,
  buttonStyle,
  containerStyle,
}) {
  const anchorRef = useRef();

  const theme = useTheme();

  const [open, setOpen] = useState(false);

  const prevOpen = usePrevious(open);

  const handleToggle = () => setOpen((state) => !state);

  const handleClose = (e) => {
    if (anchorRef.current && anchorRef.current.contains(e.target)) return;

    setOpen(false);
  };

  const handleListKeyDown = (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      setOpen(false);
    } else if (e.key === 'Escape') setOpen(false);
  };

  const handleSelect = (e, item) => {
    if (onSelectItem) onSelectItem(item);
    handleClose(e);
  };

  useEffect(() => {
    if (prevOpen === true && open === false) anchorRef.current.focus();
  }, [open]);

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return (
    <Box sx={{ ...containerStyle }}>
      <Tooltip title={tooltipTitle}>
        <Button
          ref={anchorRef}
          aria-controls={open ? 'dropdown-menu' : undefined}
          aria-expanded={open ? 'true' : undefined}
          aria-haspopup="true"
          size={isMobile ? 'medium' : 'large'}
          variant="outlined"
          endIcon={<ArrowDropDownIcon fontSize="small" />}
          startIcon={value?.icon}
          onClick={handleToggle}
          sx={{
            alignSelf: 'stretch',
            fontSize: {
              xs: '0.7rem',
              md: '0.8rem',
              lg: '0.85rem',
            },
            height: '100%',
            '& .MuiButton-startIcon>*:nth-of-type(1)': {
              fontSize: {
                xs: '0.65rem',
                sm: '0.75rem',
                md: '0.65rem',
                lg: '0.95rem',
              },
            },
            minWidth: isMobile ? 120 : 215,
            ...buttonStyle,
          }}
        >
          <Box sx={{ mr: 'auto' }}>{value?.label}</Box>
        </Button>
      </Tooltip>
      <Popper
        transition
        anchorEl={anchorRef.current}
        open={open}
        role={undefined}
        placement="bottom-start"
        popperOptions={{ strategy: 'fixed' }}
        sx={{ zIndex: 100 }}
      >
        {({ TransitionProps, placement }) => (
          <Grow
            {...TransitionProps}
            sx={{
              transformOrigin:
                placement === 'bottom-start' ? 'left top' : 'left bottom',
            }}
          >
            <Box component={Paper}>
              <ClickAwayListener onClickAway={handleClose}>
                <MenuList
                  aria-labelledby="dropdown-button"
                  autoFocusItem={open}
                  onKeyDown={handleListKeyDown}
                  sx={{ minWidth: 150 }}
                >
                  {options.map((item) => (
                    <MenuItem
                      key={item.value}
                      disabled={item.disabled}
                      selected={item.value === value.value}
                      onClick={(e) => handleSelect(e, item)}
                    >
                      {item.icon && <ListItemIcon>{item.icon}</ListItemIcon>}
                      <ListItemText>{item.label}</ListItemText>
                      {item.secondaryIcon && item.secondaryIcon}
                    </MenuItem>
                  ))}
                </MenuList>
              </ClickAwayListener>
            </Box>
          </Grow>
        )}
      </Popper>
    </Box>
  );
}

export default React.memo(DropdownMenu);
