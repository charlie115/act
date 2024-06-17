import { createApi } from '@reduxjs/toolkit/query/react';

const api = createApi({
  reducerPath: 'websocketApi',
  endpoints: () => ({}),
  refetchOnFocus: true,
  refetchOnMountOrArgChange: true,
  refetchOnReconnect: true,
});

export default api;
