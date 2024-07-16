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
    'global-require': 'off',
    'import/no-dynamic-require': 'off',
    'import/no-extraneous-dependencies': [
      'error',
      {
        devDependencies: false,
        optionalDependencies: false,
        peerDependencies: false,
        packageDir: __dirname,
      },
    ],
    'import/no-unresolved': ['error', { caseSensitive: false }],
    'jsx-a11y/anchor-is-valid': 'off',
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
    'react/jsx-props-no-spreading': 'off',
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
          'constants': './src/constants',
          'configs': './src/configs',
          'hooks': './src/hooks',
          'pages': './src/pages',
          'redux': './src/redux',
          'utils': './src/utils',
        },
        extensions: ['.js', '.jsx', '.scss'],
      },
    },
  },
};
