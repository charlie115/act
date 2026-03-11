import drfApi from 'redux/api/drf';

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
        results: response?.results,
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
        results: response?.results,
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
        results: response?.results,
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
