const getCoinIcons = () => {
  const icons = require.context(
    'assets/icons/coinicon',
    true,
    /coinicon\/.*.png$/
  );

  return icons
    .keys()
    .reduce((a, v) => ({ ...a, [v.split('/').slice(-1)]: v }), {});
};

const getTranslations = () => {
  const translations = require.context(
    'assets/translations',
    true,
    /translations\/.*.json$/
  );

  return translations
    .keys()
    .reduce((a, v) => ({ ...a, [v.split('/').slice(-1)]: v }), {});
};

export const coinicons = getCoinIcons();
export const translations = getTranslations();
