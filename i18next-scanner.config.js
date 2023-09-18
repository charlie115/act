/* eslint-disable import/no-extraneous-dependencies */
/* eslint-disable no-plusplus */
/* eslint-disable prefer-object-spread */

module.exports = {
  input: [
    'src/**/*.{js,jsx}',
    // Use ! to filter out files or directories
    '!src/**/*.spec.{js,jsx}',
    '!src/assets/**',
    '!src/.dummy/**',
    '!**/node_modules/**',
  ],
  output: './',
  options: {
    debug: true,
    sort: true,
    func: {
      list: ['i18next.t', 'i18n.t', 't'],
      extensions: ['.js', '.jsx'],
    },
    removeUnusedKeys: true,
    trans: {
      component: 'Trans',
      i18nKey: 'i18nKey',
      defaultsKey: 'defaults',
      extensions: ['.js', '.jsx'],
      fallbackKey(ns, value) {
        return value;
      },

      // https://react.i18next.com/latest/trans-component#usage-with-simple-html-elements-like-less-than-br-greater-than-and-others-v10.4.0
      // supportBasicHtmlNodes: true, // Enables keeping the name of simple nodes (e.g. <br/>) in translations instead of indexed keys.
      // keepBasicHtmlNodesFor: ['br', 'strong', 'i', 'p'], // Which nodes are allowed to be kept in translations during defaultValue generation of <Trans>.

      // https://github.com/acornjs/acorn/tree/master/acorn#interface
      acorn: {
        ecmaVersion: 2020,
        sourceType: 'module', // defaults to 'module'
      },
    },
    lngs: ['en', 'ko', 'zh'],
    ns: ['translation'],
    defaultNs: 'translation',
    defaultLng: (lng) => lng,
    defaultValue: (lng, ns, key) => (lng === 'en' ? key : ''),
    resource: {
      loadPath: './src/assets/translations/{{lng}}.json',
      savePath: './src/assets/translations/{{lng}}.json',
      jsonIndent: 2,
      lineEnding: '\n',
    },
    nsSeparator: true, // namespace separator
    keySeparator: false, // key separator
    plural: true,
    interpolation: { prefix: '{{', suffix: '}}' },
    metadata: {},
    allowDynamicKeys: false,
  },
  // transform: function customTransform(file, enc, done) {
  //   const { parser } = this;
  //   const content = fs.readFileSync(file.path, enc);
  //   let count = 0;

  //   parser.parseFuncFromString(
  //     content,
  //     { list: ['i18n.t', 'i18next.t', 'i18next._', 'i18next.__'] },
  //     (key, options, ...o) => {
  //       console.log('o: ', o);
  //       const { ns } = options;
  //       parser.set(
  //         key,
  //         Object.assign({}, options, {
  //           ns: ns || DEFAULT_NS,
  //           nsSeparator: ':',
  //           keySeparator: '.',
  //         })
  //       );
  //       ++count;
  //     }
  //   );
  //   if (count > 0) {
  //     console.log(
  //       `i18next-scanner: count=${chalk.cyan(count)}, file=${chalk.yellow(
  //         JSON.stringify(file.relative)
  //       )}`
  //     );
  //   }

  //   done();
  // },
};
