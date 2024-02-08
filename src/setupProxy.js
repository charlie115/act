// eslint-disable-next-line import/no-extraneous-dependencies
const { createProxyMiddleware } = require('http-proxy-middleware');

// eslint-disable-next-line func-names
module.exports = function (app) {
  app.use(
    '/api/',
    createProxyMiddleware({
      target: 'https://acw-test.orbitholdings.org',
      changeOrigin: true,
      secure: false,
      pathRewrite: {
        '^/api/': '/api/', // rewrite path
      },
    })
  );
};
