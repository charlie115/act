module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: ['airbnb', 'prettier'],
  overrides: [
    {
      env: {
        node: true,
      },
      files: ['.eslintrc.{js,cjs}'],
      parserOptions: {
        sourceType: 'script',
      },
    },
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    'no-param-reassign': 'off',
    'no-unused-vars': [
      'warn',
      {
        vars: 'all',
        args: 'after-used',
        argsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        ignoreRestSiblings: false,
      },
    ],
    'react/prop-types': 'off',
  },
  settings: {
    'import/resolver': {
      'eslint-import-resolver-custom-alias': {
        // prettier-ignore
        alias: {
          'src': './src',
          'assets': './src/assets',
          'components': './src/components',
          'configs': './src/configs',
          'pages': './src/pages',
          'store': './src/store',
        },
        extensions: ['.js', '.jsx', '.scss'],
      },
    },
  },
};
