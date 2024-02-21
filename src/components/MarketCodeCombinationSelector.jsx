import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from 'react';

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
import Stack from '@mui/material/Stack';

import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { usePrevious } from '@uidotdev/usehooks';

const MarketCodeCombinationSelector = forwardRef(
  ({ options = [], value, onSelectItem, buttonStyle }, ref) => {
    const anchorRef = useRef();

    const theme = useTheme();

    const [open, setOpen] = useState(false);

    const prevOpen = usePrevious(open);

    const handleToggle = () => setOpen((state) => !state);

    const handleClose = (e) => {
      if (anchorRef.current && anchorRef.current.contains(e.target)) return;

      setOpen(false);
    };

    useImperativeHandle(
      ref,
      () => ({
        toggle: handleToggle,
      }),
      []
    );

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
      <Box sx={{ px: { xs: 0, md: 2 } }}>
        <Button
          ref={anchorRef}
          aria-controls={open ? 'dropdown-menu' : undefined}
          aria-expanded={open ? 'true' : undefined}
          aria-haspopup="true"
          size={isMobile ? 'medium' : 'large'}
          variant="outlined"
          endIcon={<ArrowDropDownIcon fontSize="small" />}
          startIcon={value?.target && value?.origin ? null : value?.icon}
          onClick={handleToggle}
          sx={{
            alignSelf: 'stretch',
            fontSize: {
              xs: '0.7rem',
              md: '0.8rem',
              lg: '0.85rem',
            },
            // height: '100%',
            '& .MuiButton-startIcon>*:nth-of-type(1)': {
              fontSize: {
                xs: '0.65rem',
                sm: '0.75rem',
                md: '0.65rem',
                lg: '0.95rem',
              },
            },
            minWidth: isMobile ? 240 : 320,
            ...buttonStyle,
          }}
        >
          <Box sx={{ mr: 'auto' }}>
            {value?.target && value?.origin ? (
              <Stack alignItems="center" direction="row" spacing={1}>
                {value.target.icon} <Box>{value.target.label}</Box>
                <SyncAltIcon color="accent" fontSize="small" />
                {value.origin.icon}
                <Box>{value.origin.label}</Box>
              </Stack>
            ) : (
              value?.label
            )}
          </Box>
        </Button>
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
                        dense
                        key={item.value}
                        disabled={item.disabled}
                        selected={item.value === value.value}
                        onClick={(e) => handleSelect(e, item)}
                      >
                        {item.target && item.origin ? (
                          <>
                            {item.target.icon && (
                              <ListItemIcon>{item.target.icon}</ListItemIcon>
                            )}
                            <ListItemText sx={{}}>
                              {item.target.label}
                            </ListItemText>
                            <SyncAltIcon
                              color="accent"
                              fontSize="small"
                              sx={{ mx: 2 }}
                            />
                            {item.origin.icon && (
                              <ListItemIcon>{item.origin.icon}</ListItemIcon>
                            )}
                            <ListItemText>{item.origin.label}</ListItemText>
                          </>
                        ) : (
                          <>
                            {item.icon && (
                              <ListItemIcon>{item.icon}</ListItemIcon>
                            )}
                            <ListItemText>{item.label}</ListItemText>
                            {item.secondaryIcon && item.secondaryIcon}
                          </>
                        )}
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
);

export default MarketCodeCombinationSelector;
