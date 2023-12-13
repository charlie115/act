// eslint-disable-next-line import/no-extraneous-dependencies
const { createProxyMiddleware } = require('http-proxy-middleware');

// eslint-disable-next-line func-names
module.exports = function (app) {
  app.use(
    '/api/',
    createProxyMiddleware({
      target: 'https://arbicrypto.net',
      changeOrigin: true,
      pathRewrite: {
        '^/api/': '/api/', // rewrite path
      },
    })
  );
};
