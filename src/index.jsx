// eslint-disable-next-line import/no-unresolved
import 'polyfills';

import React from 'react';
import ReactDOM from 'react-dom/client';

import { Provider } from 'react-redux';
import { persistStore } from 'redux-persist';
import { PersistGate } from 'redux-persist/integration/react';

import store from 'redux/store';

import FullScreenLoading from 'components/FullScreenLoading';

import App from './App';
import reportWebVitals from './reportWebVitals';

import 'configs/i18n';
import 'chartjs-adapter-luxon';

const persistor = persistStore(store);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  // <React.StrictMode>
  <Provider store={store}>
    <PersistGate loading={<FullScreenLoading />} persistor={persistor}>
      <App />
    </PersistGate>
  </Provider>
  // </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
