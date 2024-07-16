import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getBoardComments: builder.query({
      providesTags: ['CommunityBoardComments'],
      query: (params) => ({ url: '/board/comments/', params }),
      transformResponse: (response) => response?.results || [],
    }),
    getBoardPostById: builder.query({
      providesTags: (result, error, id) => [
        { type: 'CommunityBoardPost', id },
        'CommunityBoardPost',
      ],
      query: (id) => `/board/posts/${id}/`,
    }),
    getBoardPostCategory: builder.query({
      providesTags: ['CommunityBoardPostCategory'],
      query: () => '/board/post-category/',
      transformResponse: (response) => response?.results || [],
    }),
    getBoardPosts: builder.query({
      providesTags: ['CommunityBoardPosts'],
      query: () => '/board/posts/',
      transformResponse: (response) => response?.results || [],
    }),
    postBoardComment: builder.mutation({
      invalidatesTags: ['CommunityBoardComments', 'CommunityBoardPost'],
      query: (body) => ({ url: '/board/comments/', method: 'POST', body }),
      transformResponse: (response) => response?.results || [],
    }),
    postBoardPost: builder.mutation({
      invalidatesTags: ['CommunityBoardPosts'],
      query: (body) => ({ url: '/board/posts/', method: 'POST', body }),
    }),
    postBoardPostLikes: builder.mutation({
      invalidatesTags: ['CommunityBoardPost', 'CommunityBoardPosts'],
      query: (body) => ({ url: '/board/post-likes/', method: 'POST', body }),
    }),
    postBoardPostViews: builder.mutation({
      invalidatesTags: ['CommunityBoardPost', 'CommunityBoardPosts'],
      query: (body) => ({ url: '/board/post-views/', method: 'POST', body }),
    }),
  }),
});

export default api;
export const {
  useGetBoardCommentsQuery,
  useGetBoardPostByIdQuery,
  useGetBoardPostCategoryQuery,
  useGetBoardPostsQuery,
  usePostBoardCommentMutation,
  usePostBoardPostMutation,
  usePostBoardPostLikesMutation,
  usePostBoardPostViewsMutation,
} = api;
