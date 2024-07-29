import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    // deleteBoardPostLikes: builder.mutation({
    //   invalidatesTags: ['CommunityBoardPost', 'CommunityBoardPosts'],
    //   query: ({ id, ...params }) => ({
    //     url: `/board/post-likes/${id}/`,
    //     method: 'DELETE',
    //     params,
    //   }),
    // }),
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
      query: (params) => ({ url: '/board/posts/', params }),
      transformResponse: (response) => ({
        nextPage: response?.next
          ? new URL(response.next).searchParams?.get('page')
          : null,
        previousPage: response?.previous
          ? new URL(response.next).searchParams?.get('page')
          : null,
        count: response?.count,
        results: response?.results,
      }),
    }),
    deleteBoardPostReactions: builder.mutation({
      invalidatesTags: ['CommunityBoardPost', 'CommunityBoardPosts'],
      query: (id) => ({
        url: `/board/post-reactions/${id}/`,
        method: 'DELETE',
      }),
    }),
    deleteBoardCommentReactions: builder.mutation({
      invalidatesTags: ['CommunityBoardComments', 'CommunityBoardPosts'],
      query: (id) => ({
        url: `/board/comment-reactions/${id}/`,
        method: 'DELETE',
      }),
    }),
    patchBoardPostReactions: builder.mutation({
      invalidatesTags: ['CommunityBoardPost', 'CommunityBoardPosts'],
      query: ({ id, ...body }) => ({
        url: `/board/post-reactions/${id}/`,
        method: 'PATCH',
        body,
      }),
    }),
    patchBoardCommentReactions: builder.mutation({
      invalidatesTags: ['CommunityBoardComments', 'CommunityBoardPosts'],
      query: ({ id, ...body }) => ({
        url: `/board/comment-reactions/${id}/`,
        method: 'PATCH',
        body,
      }),
    }),
    postBoardComment: builder.mutation({
      invalidatesTags: ['CommunityBoardComments', 'CommunityBoardPost'],
      query: (body) => ({ url: '/board/comments/', method: 'POST', body }),
      transformResponse: (response) => response?.results || [],
    }),
    postBoardCommentReactions: builder.mutation({
      invalidatesTags: ['CommunityBoardComments', 'CommunityBoardPosts'],
      query: (body) => ({
        url: '/board/comment-reactions/',
        method: 'POST',
        body,
      }),
    }),
    postBoardPost: builder.mutation({
      invalidatesTags: ['CommunityBoardPosts'],
      query: (body) => ({ url: '/board/posts/', method: 'POST', body }),
    }),
    postBoardPostReactions: builder.mutation({
      invalidatesTags: ['CommunityBoardPost', 'CommunityBoardPosts'],
      query: (body) => ({
        url: '/board/post-reactions/',
        method: 'POST',
        body,
      }),
    }),
    postBoardPostViews: builder.mutation({
      invalidatesTags: ['CommunityBoardPost', 'CommunityBoardPosts'],
      query: (body) => ({ url: '/board/post-views/', method: 'POST', body }),
    }),
  }),
});

export default api;
export const {
  useGetBoardPostByIdQuery,
  useGetBoardPostCategoryQuery,
  useGetBoardPostsQuery,
  useGetBoardCommentsQuery,
  useDeleteBoardCommentReactionsMutation,
  usePatchBoardCommentReactionsMutation,
  useDeleteBoardPostReactionsMutation,
  usePatchBoardPostReactionsMutation,
  usePostBoardCommentMutation,
  usePostBoardCommentReactionsMutation,
  usePostBoardPostMutation,
  usePostBoardPostReactionsMutation,
  usePostBoardPostViewsMutation,
} = api;
