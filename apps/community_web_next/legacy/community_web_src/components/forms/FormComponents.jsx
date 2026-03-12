import React, { forwardRef } from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import FormHelperText from '@mui/material/FormHelperText';
import InputAdornment from '@mui/material/InputAdornment';
import IconButton from '@mui/material/IconButton';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import RadioGroup from '@mui/material/RadioGroup';
import Radio from '@mui/material/Radio';
import Slider from '@mui/material/Slider';
import Chip from '@mui/material/Chip';
import { styled, alpha } from '@mui/material/styles';

// Enhanced text field with modern styling
export const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: theme.shape.borderRadius,
    transition: theme.transitions.create(['border-color', 'box-shadow', 'background-color'], {
      duration: theme.transitions.duration.short,
    }),
    '&:hover': {
      backgroundColor: alpha(theme.palette.primary.main, 0.02),
    },
    '&.Mui-focused': {
      backgroundColor: alpha(theme.palette.primary.main, 0.02),
      '& .MuiOutlinedInput-notchedOutline': {
        borderWidth: 2,
      },
    },
  },
  '& .MuiInputLabel-root': {
    fontSize: theme.typography.body2.fontSize,
    '&.Mui-focused': {
      color: theme.palette.primary.main,
    },
  },
  '& .MuiOutlinedInput-input': {
    padding: theme.spacing(1.75, 2),
    fontSize: theme.typography.body1.fontSize,
  },
  '& .MuiFormHelperText-root': {
    marginLeft: theme.spacing(0.5),
    fontSize: theme.typography.caption.fontSize,
  },
}));

// Enhanced select component
export const StyledSelect = styled(Select)(({ theme }) => ({
  borderRadius: theme.shape.borderRadius,
  '& .MuiOutlinedInput-notchedOutline': {
    borderColor: theme.palette.divider,
  },
  '&:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: theme.palette.inputBorderColorHover,
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: theme.palette.primary.main,
    borderWidth: 2,
  },
  '& .MuiSelect-select': {
    padding: theme.spacing(1.75, 2),
    fontSize: theme.typography.body1.fontSize,
  },
}));

// Enhanced form control wrapper
export const StyledFormControl = styled(FormControl)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  '& .MuiFormLabel-root': {
    fontSize: theme.typography.body2.fontSize,
    fontWeight: theme.typography.fontWeightMedium,
    color: theme.palette.text.primary,
    marginBottom: theme.spacing(1),
    '&.Mui-focused': {
      color: theme.palette.primary.main,
    },
  },
}));

// Modern switch component
export const StyledSwitch = styled(Switch)(({ theme }) => ({
  width: 48,
  height: 26,
  padding: 0,
  '& .MuiSwitch-switchBase': {
    padding: 0,
    margin: 2,
    transitionDuration: '300ms',
    '&.Mui-checked': {
      transform: 'translateX(22px)',
      color: '#fff',
      '& + .MuiSwitch-track': {
        backgroundColor: theme.palette.primary.main,
        opacity: 1,
        border: 0,
      },
    },
  },
  '& .MuiSwitch-thumb': {
    boxSizing: 'border-box',
    width: 22,
    height: 22,
  },
  '& .MuiSwitch-track': {
    borderRadius: 26 / 2,
    backgroundColor: theme.palette.mode === 'light' ? '#E9E9EA' : '#39393D',
    opacity: 1,
    transition: theme.transitions.create(['background-color'], {
      duration: 500,
    }),
  },
}));

// Enhanced checkbox
export const StyledCheckbox = styled(Checkbox)(({ theme }) => ({
  color: theme.palette.text.secondary,
  '&.Mui-checked': {
    color: theme.palette.primary.main,
  },
  '& .MuiSvgIcon-root': {
    fontSize: 20,
  },
}));

// Enhanced radio button
export const StyledRadio = styled(Radio)(({ theme }) => ({
  color: theme.palette.text.secondary,
  '&.Mui-checked': {
    color: theme.palette.primary.main,
  },
  '& .MuiSvgIcon-root': {
    fontSize: 20,
  },
}));

// Modern slider component
export const StyledSlider = styled(Slider)(({ theme }) => ({
  color: theme.palette.primary.main,
  height: 6,
  '& .MuiSlider-track': {
    border: 'none',
  },
  '& .MuiSlider-thumb': {
    height: 20,
    width: 20,
    backgroundColor: '#fff',
    border: '2px solid currentColor',
    '&:focus, &:hover, &.Mui-active, &.Mui-focusVisible': {
      boxShadow: 'inherit',
    },
    '&::before': {
      display: 'none',
    },
  },
  '& .MuiSlider-valueLabel': {
    lineHeight: 1.2,
    fontSize: 12,
    background: 'unset',
    padding: 0,
    width: 32,
    height: 32,
    borderRadius: '50% 50% 50% 0',
    backgroundColor: theme.palette.primary.main,
    transformOrigin: 'bottom left',
    transform: 'translate(50%, -100%) rotate(-45deg) scale(0)',
    '&::before': { display: 'none' },
    '&.MuiSlider-valueLabelOpen': {
      transform: 'translate(50%, -100%) rotate(-45deg) scale(1)',
    },
    '& > *': {
      transform: 'rotate(45deg)',
    },
  },
}));

// Form section component
export function FormSection({ title, subtitle, children, ...props }) {
  return <Box sx={{ mb: 4 }} {...props}>
    {title && (
      <Box sx={{ mb: 3 }}>
        <Box component="h3" sx={{ 
          fontSize: '1.125rem', 
          fontWeight: 600,
          color: 'text.primary',
          mb: subtitle ? 0.5 : 0,
        }}>
          {title}
        </Box>
        {subtitle && (
          <Box sx={{ 
            fontSize: '0.875rem', 
            color: 'text.secondary',
          }}>
            {subtitle}
          </Box>
        )}
      </Box>
    )}
    {children}
  </Box>
}

// Input with icon
export const IconTextField = forwardRef(({ icon, iconPosition = 'start', onIconClick, ...props }, ref) => (
  <StyledTextField
    ref={ref}
    slotProps={{
      input: {
        [iconPosition === 'start' ? 'startAdornment' : 'endAdornment']: (
          <InputAdornment position={iconPosition}>
            {onIconClick ? (
              <IconButton onClick={onIconClick} edge={iconPosition}>
                {icon}
              </IconButton>
            ) : (
              icon
            )}
          </InputAdornment>
        ),
      },
    }}
    {...props}
  />
));

// Multi-select with chips
export function ChipSelect({ value = [], onChange, options, ...props }) {
  return <StyledSelect
    multiple
    value={value}
    onChange={onChange}
    renderValue={(selected) => (
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {selected.map((val) => (
          <Chip 
            key={val} 
            label={options.find(opt => opt.value === val)?.label || val}
            size="small"
            sx={{ height: 24 }}
          />
        ))}
      </Box>
    )}
    {...props}
  >
    {options.map((option) => (
      <MenuItem key={option.value} value={option.value}>
        <Checkbox checked={value.includes(option.value)} />
        {option.label}
      </MenuItem>
    ))}
  </StyledSelect>
}

// Form group with label
export function FormGroup({ label, required, error, helperText, children, ...props }) {
  return <StyledFormControl fullWidth error={error} {...props}>
    {label && (
      <FormLabel required={required}>
        {label}
      </FormLabel>
    )}
    {children}
    {helperText && (
      <FormHelperText>{helperText}</FormHelperText>
    )}
  </StyledFormControl>
}

// Enhanced radio group
export function StyledRadioGroup({ label, options, ...props }) {
  return <FormGroup label={label}>
    <RadioGroup {...props}>
      {options.map((option) => (
        <FormControlLabel
          key={option.value}
          value={option.value}
          control={<StyledRadio />}
          label={option.label}
          disabled={option.disabled}
        />
      ))}
    </RadioGroup>
  </FormGroup>
}