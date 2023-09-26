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
import { validate, v4 } from 'uuid';

import { createLogger } from 'redux-logger';

import drfApi from './api/drf';
import websocketApi from './api/websocket';

import app from './reducers/app';
import auth from './reducers/auth';
import home from './reducers/home';
import websocket from './reducers/websocket';

let secretKey;
const uid = localStorage.getItem('uid');
if (validate(uid)) secretKey = uid;
else {
  localStorage.clear();

  const newUid = v4();
  localStorage.setItem('uid', newUid);
  secretKey = newUid;
}

const authPersistConfig = {
  key: 'auth',
  storage,
  whitelist: ['id', 'loggedin'],
  transforms: [
    encryptTransform({
      secretKey,
      onError() {
        // Handle the error.
      },
    }),
  ],
};

const homePersistConfig = {
  key: 'home',
  storage,
  whitelist: ['favoriteAssets'],
};

const rootPersistConfig = {
  key: 'root',
  storage,
  whitelist: ['app'],
};

const reducers = combineReducers({
  app,
  websocket,
  auth: persistReducer(authPersistConfig, auth),
  home: persistReducer(homePersistConfig, home),
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
