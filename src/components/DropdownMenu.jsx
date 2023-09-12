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

import useMediaQuery from '@mui/material/useMediaQuery';

import { usePrevious } from '@uidotdev/usehooks';

function DropdownMenu({
  options = [],
  disabledValue,
  value,
  tooltipTitle,
  onSelectItem,
  buttonStyle,
  containerStyle,
}) {
  const anchorRef = useRef();

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

  const matchLargeScreen = useMediaQuery('(min-width:600px)');

  return (
    <Box sx={{ ...containerStyle }}>
      <Tooltip title={tooltipTitle}>
        <Button
          fullWidth
          ref={anchorRef}
          aria-controls={open ? 'dropdown-menu' : undefined}
          aria-expanded={open ? 'true' : undefined}
          aria-haspopup="true"
          size="large"
          variant="outlined"
          startIcon={value?.icon}
          onClick={handleToggle}
          sx={{
            alignSelf: 'stretch',
            fontSize: matchLargeScreen ? null : 10,
            ...buttonStyle,
          }}
        >
          {value?.label}
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
                >
                  {options.map((item) => (
                    <MenuItem
                      key={item.value}
                      disabled={
                        item.disabled || disabledValue?.value === item.value
                      }
                      selected={item.value === value.value}
                      onClick={(e) => handleSelect(e, item)}
                    >
                      {item.icon && <ListItemIcon>{item.icon}</ListItemIcon>}
                      <ListItemText>{item.label}</ListItemText>
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
