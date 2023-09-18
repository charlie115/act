import { combineReducers, configureStore } from '@reduxjs/toolkit';

import storage from 'redux-persist/lib/storage';
// import storageSession from 'redux-persist/lib/storage/session';
import {
  persistReducer,
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER,
} from 'redux-persist';

import { encryptTransform } from 'redux-persist-transform-encrypt';

import { createLogger } from 'redux-logger';

import drfApi from './api/drf';
import websocketApi from './api/websocket';

import app from './reducers/app';
import auth from './reducers/auth';
import websocket from './reducers/websocket';

const rootPersistConfig = {
  key: 'root',
  storage,
  whitelist: ['app', 'auth'],
  transforms: [
    encryptTransform({
      secretKey: 'my-super-secret-key',
      onError(error) {
        console.log('error: ', error);
        // Handle the error.
      },
    }),
  ],
};

const reducers = combineReducers({
  app,
  auth,
  websocket,
  [drfApi.reducerPath]: drfApi.reducer,
  [websocketApi.reducerPath]: websocketApi.reducer,
});

const persistedReducer = persistReducer(rootPersistConfig, reducers);

const loggerMiddleware = createLogger({
  predicate: (getState, action) =>
    action.type !== 'websocketApi/queries/queryResultPatched',
});

export default configureStore({
  reducer: persistedReducer,
  devTools: process.env.NODE_ENV !== 'production',
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        ignoredPaths: ['websocketApi.queries'],
      },
    }).concat(drfApi.middleware, websocketApi.middleware, loggerMiddleware),
});
