import { createApi } from '@reduxjs/toolkit/query/react';

import baseQueryWithReAuth from 'utils/baseQueryWithReAuth';

const api = createApi({
  reducerPath: 'drfApi',
  baseQuery: baseQueryWithReAuth,
  endpoints: () => ({}),
});

export default api;
