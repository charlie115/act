import React, { useEffect } from 'react';

import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';

import { useTranslation } from 'react-i18next';

import { useDispatch, useSelector } from 'react-redux';
import { changeLanguage } from 'redux/reducers/app';

const LANGUAGES = [
  {
    label: '🇰🇷 KR',
    value: 'ko',
  },
  {
    label: '🇬🇧 EN',
    value: 'en',
  },
  {
    label: '🇨🇳 CH',
    value: 'zh',
  },
];

export default function LanguageSelector(props) {
  const dispatch = useDispatch();
  const language = useSelector((state) => state.app.language);

  const { i18n } = useTranslation();

  useEffect(() => {
    i18n.changeLanguage(language).then();
  }, [language]);

  const handleChange = async (e) => {
    dispatch(changeLanguage(e.target.value));
  };

  return (
    <Select
      id="language-selector"
      // label="Language"
      value={language}
      onChange={handleChange}
      size="small"
      variant="standard"
      {...props}
    >
      {LANGUAGES.map((lang) => (
        <MenuItem key={lang.value} value={lang.value}>
          {lang.label}
        </MenuItem>
      ))}
    </Select>
  );
}
