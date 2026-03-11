# ArbiCrypto (community_web)

This is the project repository for [ArbiCrypto](https://arbicrypto.net/).

## Setup

- Package manager: [PNPM](https://pnpm.io/)
- Node version: [Node v18.15.0 LTS](https://nodejs.org/en/blog/release/v18.15.0)
- Bootstrapped with: [Create React App](https://github.com/facebook/create-react-app)

## Translations

The project uses [i18next](https://www.i18next.com/) and [react-i18next](https://react.i18next.com/) for translations.

- Configuration file: [configs/i18n.js](src/configs/i18n.js)
- `pnpm run scan:i18n` to extract translation keys from the code ([i18next-scanner.config.js](i18next-scanner.config.js)); the project uses [i18next-scanner](https://i18next.github.io/i18next-scanner/)
- Add translation values to the appropriate translation files:
  - [src/assets/translations/en.json](src/assets/translations/en.json)
  - [src/assets/translations/ko.json](src/assets/translations/ko.json)
  - [src/assets/translations/zh.json](src/assets/translations/zh.json)

## Environment Variables

Refer to [.env.test.example](.env.test.example) and [.env.production.example](.env.production.example).

For values, see here:

- [PROD](https://halo-soft.atlassian.net/wiki/spaces/KB/pages/295025/Server+List#Environment-Variables)
- [TEST](https://halo-soft.atlassian.net/wiki/spaces/KB/pages/295025/Server+List#Environment-Variables.1)

## Test Deployment

Run `pnpm run build:test` to create the build for test deployment.

Copy the **build** directory to the test server.

- For Unix-based operating systems, run `scp -r build <SERVER_NAME>:~/test-community-web`

  _Make sure to setup the test server configuration in .ssh/config_

## Production Deployment

Switch to **master** branch. \
Merge **development** branch to **master** and resolve conflicts.

Run `pnpm run build:production` to create the production build.

Copy the **build** directory to the production server.

- For Unix-based operating systems, run `scp -r build <SERVER_NAME>:~/prod-community-web`

  _Make sure to setup the production server configuration in .ssh/config_

## Development

Switch to **development** branch.

Run `pnpm start` to start the web app in development mode. Open [http://localhost:3000](http://localhost:3000) to view in the browser.

### Directory Structure

```
.
├── public
└── src
    ├── assets
    ├── components
    ├── configs
    ├── constants
    ├── hooks
    ├── pages
    ├── redux
    └── utils
```

### Things to note

- This project uses [ESLint](https://eslint.org/) to find problems in the code. [eslint-config-airbnb](https://www.npmjs.com/package/eslint-config-airbnb) is used as base coding style guide. Rules can be added in the configuration file ([.eslintrc.js](.eslintrc.js)).
- When creating a new directory in src, it is important to add the path in [jsconfig.json](jsconfig.json) and [.eslintrc.js](eslintrc.js) _(settings > import/resolver > eslint-import-resolver-custom-alias)_ in order to correctly resolve absolute imports.
- This project uses [http-proxy-middleware](https://www.npmjs.com/package/http-proxy-middleware) to proxy `/api/` to the test DRF domain. Configuration can be found in [setupProxy.js](src/setupProxy.js)
- Set up new **navigation** pages in [configs/navigation.js](src/configs/navigation.js)
