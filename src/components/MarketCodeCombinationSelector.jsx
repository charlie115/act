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
import LinearProgress from '@mui/material/LinearProgress';
import ListItem from '@mui/material/ListItem';
import ListItemSecondaryAction from '@mui/material/ListItemSecondaryAction';
import ListItemText from '@mui/material/ListItemText';
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
  ({ options = [], value, loading, onSelectItem, buttonStyle }, ref) => {
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
      if (item.disabled) return;
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
                <Box>
                  {value.target.icon} {value.target.getLabel()}
                </Box>
                <SyncAltIcon color="accent" fontSize="small" />
                <Box>
                  {value.origin.icon} {value.origin.getLabel()}
                </Box>
              </Stack>
            ) : (
              value?.getLabel()
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
                    aria-labelledby="menu-list-button"
                    autoFocusItem={open}
                    onKeyDown={handleListKeyDown}
                    sx={{ minWidth: 150 }}
                  >
                    {loading && <LinearProgress />}
                    {options.map((item) => (
                      <ListItem
                        dense
                        key={item.value}
                        selected={item.value === value.value}
                        onClick={(e) => handleSelect(e, item)}
                        sx={
                          !item.disabled
                            ? {
                                cursor: 'pointer',
                                ':hover': { bgcolor: 'divider' },
                              }
                            : {}
                        }
                      >
                        {item.target && item.origin ? (
                          <>
                            <ListItemText
                              sx={{ opacity: item.disabled ? 0.5 : 1 }}
                            >
                              {item.target?.icon} {item.target.getLabel()}
                            </ListItemText>
                            <SyncAltIcon
                              color="accent"
                              fontSize="small"
                              sx={{ mx: 2, opacity: item.disabled ? 0.5 : 1 }}
                            />
                            <ListItemText
                              sx={{ opacity: item.disabled ? 0.5 : 1 }}
                            >
                              {item.origin?.icon} {item.origin.getLabel()}
                            </ListItemText>
                            {item.secondaryIcon && (
                              <ListItemSecondaryAction>
                                {item.secondaryIcon}
                              </ListItemSecondaryAction>
                            )}
                            {/* {item.add && (
                              <ListItemSecondaryAction>
                                <IconButton
                                  color="success"
                                  edge="end"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onAddItem(item);
                                  }}
                                  sx={{ p: 0 }}
                                >
                                  <AddIcon sx={{ fontSize: 16 }} />
                                </IconButton>
                              </ListItemSecondaryAction>
                            )} */}
                          </>
                        ) : (
                          <>
                            <ListItemText>
                              {item.icon} {item.getLabel()}
                            </ListItemText>
                            {item.secondaryIcon && item.secondaryIcon}
                          </>
                        )}
                      </ListItem>
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
