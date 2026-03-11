import { useState } from 'react';
import jsCookie from 'js-cookie';

import castString from 'utils/castString';

export default (cookieName) => {
  const getCookie = () => castString(jsCookie.get(cookieName));

  const [cookieValue, setCookieValue] = useState(getCookie());

  const clearCookie = () => {
    jsCookie.remove(cookieName);
    setCookieValue(null);
  };

  const setCookie = (value, options = {}) => {
    jsCookie.set(cookieName, value, options);
    setCookieValue(value);
  };

  return {
    clearCookie,
    getCookie,
    setCookie,
    cookie: cookieValue,
  };
};
