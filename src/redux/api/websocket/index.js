import { createApi } from '@reduxjs/toolkit/query/react';

const api = createApi({
  reducerPath: 'websocketApi',
  endpoints: () => ({}),
  refetchOnFocus: false,
  refetchOnMountOrArgChange: false,
  refetchOnReconnect: false,
});

export default api;
