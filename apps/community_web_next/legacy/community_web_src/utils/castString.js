import isNaN from 'lodash/isNaN';

export default (value) => {
  // prettier-ignore
  const casts = {
    'false': false,
    'true': true,
    'NaN': NaN,
    'null': null,
    'undefined': undefined,
    'Infinity': Infinity,
    '-Infinity': -Infinity,
  };
  if (value in casts) return casts[value];

  const v = Number(value);
  return !isNaN(v) ? v : value;
};
