import { createEntityAdapter, createSlice, current } from '@reduxjs/toolkit';

export const websocketSlice = createSlice({
  name: 'websocket',
  initialState: {}, // coinsAdapter.getInitialState(),
  reducers: {},
  extraReducers: (builder) => {
    // builder.addMatcher(
    //   websocketApi.internalActions.queryResultPatched,
    //   (state, action) => {
    //     console.log('action: ', action);
    //   }
    // );
  },
});

export default websocketSlice.reducer;

// export const { selectAll } = coinsAdapter.getSelectors(
//   (state) => state.websocket
// );
