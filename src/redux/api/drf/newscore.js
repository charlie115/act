import drfApi from 'redux/api/drf';

import { DateTime } from 'luxon';

import orderBy from 'lodash/orderBy';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getAnnouncements: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/newscore/announcements/',
        params,
      }),
      transformResponse: (response) => ({
        nextPage: response?.next
          ? new URL(response.next).searchParams?.get('page')
          : null,
        results: orderBy(
          response?.results || [],
          (o) => DateTime.fromISO(o.datetime).toMillis(),
          'desc'
        ),
      }),
    }),
    getNews: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/newscore/news/',
        params,
      }),
      transformResponse: (response) => ({
        nextPage: response?.next
          ? new URL(response.next).searchParams?.get('page')
          : null,
        results: orderBy(
          response?.results || [],
          (o) => DateTime.fromISO(o.datetime).toMillis(),
          'desc'
        ),
      }),
    }),
    getSocialMediaPosts: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/newscore/posts/',
        params,
      }),
      transformResponse: (response) => ({
        nextPage: response?.next
          ? new URL(response.next).searchParams?.get('page')
          : null,
        results: orderBy(
          response?.results || [],
          (o) => DateTime.fromISO(o.datetime).toMillis(),
          'desc'
        ),
      }),
    }),
  }),
});

export default api;
export const {
  useGetAnnouncementsQuery,
  useGetNewsQuery,
  useGetSocialMediaPostsQuery,
} = api;
