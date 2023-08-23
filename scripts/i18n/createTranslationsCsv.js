/* eslint-disable import/no-extraneous-dependencies */
const fs = require('fs');
const path = require('path');

const csv = require('fast-csv');

const src = path.resolve(process.env.PWD, 'src', 'assets', 'translations');
const files = fs.readdirSync(src);

const headers = ['key'];
const output = fs.createWriteStream(
  path.resolve(__dirname, 'translations.csv')
);

const stream = csv.format({ headers: true });
stream.pipe(output).on('end', () => process.exit());

const translations = {};

files.forEach((filename) => {
  headers.push(filename);

  const file = path.resolve(src, filename);
  const content = fs.readFileSync(file, 'utf8');

  const json = JSON.parse(content);
  Object.entries(json).forEach(([key, value]) => {
    if (!translations[key]) translations[key] = {};
    translations[key][filename] = value;
  });
});

Object.entries(translations).forEach(([key, value]) => {
  stream.write({ key, ...value });
});

stream.end();
