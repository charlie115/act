import { combineReducers, configureStore } from '@reduxjs/toolkit';

import storage from 'redux-persist/lib/storage';
import storageSession from 'redux-persist/lib/storage/session';
import {
  persistReducer,
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER,
} from 'redux-persist';

import logger from 'redux-logger';

import websocketApi from './api/websocket';

import app from './reducers/app';
import auth from './reducers/auth';

const rootPersistConfig = {
  key: 'root',
  storage,
  whitelist: ['app', 'auth'],
};

const reducers = combineReducers({
  app,
  auth,
  [websocketApi.reducerPath]: websocketApi.reducer,
});

const persistedReducer = persistReducer(rootPersistConfig, reducers);

export default configureStore({
  reducer: persistedReducer,
  devTools: process.env.NODE_ENV !== 'production',
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    }).concat(websocketApi.middleware, logger),
});
