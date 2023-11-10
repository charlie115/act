import React, { useCallback, useState } from 'react';

import Switch from '@mui/material/Switch';

import { styled } from '@mui/material/styles';

import { useDispatch, useSelector } from 'react-redux';
import { toggleTheme } from 'redux/reducers/app';

import debounce from 'lodash/debounce';

import MoonSvg from 'assets/svg/moon.svg';
import SunSvg from 'assets/svg/sun.svg';

export default function ThemeSelector() {
  const dispatch = useDispatch();
  const currentTheme = useSelector((state) => state.app.theme);

  const [theme, setTheme] = useState(currentTheme);

  const changeTheme = (value) => dispatch(toggleTheme(value));
  const debouncedChangeTheme = useCallback(
    debounce(changeTheme, 1500, {
      leading: true,
      trailing: true,
    }),
    []
  );

  const onChange = (e) => {
    const value = e.target.checked ? 'dark' : 'light';
    setTheme(value);
    debouncedChangeTheme(value);
  };

  return (
    <ThemeToggle
      checked={theme === 'dark'}
      isChecked={theme === 'dark'}
      onChange={onChange}
      sx={{
        width: { xs: 46, sm: 62 },
        height: { xs: 25, sm: 34 },
        '& .MuiSwitch-thumb': {
          width: { xs: 22, sm: 32 },
          height: { xs: 22, sm: 32 },
        },
      }}
    />
  );
}

const ThemeToggle = styled(Switch, {
  shouldForwardProp: (prop) => prop !== 'isChecked',
})(({ isChecked, theme }) => ({
  padding: 7,
  '& .MuiSwitch-switchBase': {
    margin: 1,
    padding: 0,
    transform: 'translateX(6px)',
    '&.Mui-checked': {
      color: '#fff',
      transform: 'translateX(22px)',
      '& .MuiSwitch-thumb:before': {
        backgroundImage: `url(${MoonSvg})`,
      },
      '& + .MuiSwitch-track': {
        opacity: 1,
        backgroundColor: theme.palette.secondary.main,
      },
    },
  },
  '& .MuiSwitch-thumb': {
    backgroundColor: isChecked
      ? theme.palette.background.default
      : 'theme.palette.white.main',
    '&:before': {
      content: "''",
      position: 'absolute',
      width: '100%',
      height: '100%',
      left: 0,
      top: 0,
      backgroundRepeat: 'no-repeat',
      backgroundPosition: 'center',
      backgroundImage: `url(${SunSvg})`,
    },
  },
  '& .MuiSwitch-track': {
    opacity: 1,
    backgroundColor: theme.palette.secondary.main,
    borderRadius: 20 / 2,
  },
}));
