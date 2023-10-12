import { createApi } from '@reduxjs/toolkit/query/react';

const api = createApi({
  reducerPath: 'websocketApi',
  endpoints: () => ({}),
});

export default api;
