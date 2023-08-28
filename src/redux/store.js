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

import { createLogger } from 'redux-logger';

import websocketApi from './api/websocket';

import app from './reducers/app';
import auth from './reducers/auth';
import websocket from './reducers/websocket';

const rootPersistConfig = {
  key: 'root',
  storage,
  whitelist: ['app', 'auth'],
};

const reducers = combineReducers({
  app,
  auth,
  websocket,
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
        ignoredActionPaths: ['payload'],
        ignoredPaths: ['websocketApi.queries'],
      },
    }).concat(websocketApi.middleware, loggerMiddleware),
});
