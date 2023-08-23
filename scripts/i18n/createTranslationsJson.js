/* eslint-disable import/no-extraneous-dependencies */
/* eslint-disable no-console */

const fs = require('fs');
const path = require('path');

const csv = require('fast-csv');

let languages = [];
const rows = [];

csv
  .parseFile(path.resolve(__dirname, 'translations.csv'), { headers: true })
  .on('error', (error) => console.error(error))
  .on('headers', (headers) => {
    languages = headers.filter((h) => h !== 'key');
  })
  .on('data', (row) => rows.push(row))
  .on('end', () => {
    languages.forEach((language) => {
      const json = {};
      rows.forEach((row) => {
        json[row.key] = row[language];
      });

      const output = path.resolve(
        process.env.PWD,
        'src',
        'assets',
        'translations',
        language
      );

      // fs.copyFileSync(output, path.resolve(__dirname, 'old', language));

      fs.writeFileSync(output, JSON.stringify(json, null, 2));
    });
  });
