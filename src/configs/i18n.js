import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: { translations: require('assets/translations/en.json') },
  ko: { translations: require('assets/translations/ko.json') },
  zh: { translations: require('assets/translations/zh.json') },
};

i18next.use(initReactI18next).init({
  resources,
  fallbackLng: 'en',
  lng: 'ko',
  defaultNS: 'translations',
  ns: ['translations'],
  interpolation: {
    escapeValue: false, // react already safes from xss
  },
  returnEmptyString: false,
  // debug: process.env.NODE_ENV !== 'production',
});

export default i18next;
