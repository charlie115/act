// eslint-disable-next-line import/no-extraneous-dependencies
const { createProxyMiddleware } = require('http-proxy-middleware');

// eslint-disable-next-line func-names
module.exports = function (app) {
  app.use(
    '/api/',
    createProxyMiddleware({
      target: process.env.REACT_APP_DRF_URL,
      changeOrigin: true,
      // changeOrigin: false,
      secure: false,
      pathRewrite: {
        '^/api/': '/api/', // rewrite path
        // '^/api/': '', // rewrite path
      },
    })
  );
};
