import i18n from 'configs/i18n';

export default function getLocalization() {
  const { t } = i18n;
  return {
    clearSearch: t('Clear search'),
    collapse: t('Collapse'),
    collapseAll: t('Collapse all'),
    expand: t('Expand'),
    expandAll: t('Expand all'),
    hideAll: t('Hide all'),
    noRecordsToDisplay: t('No records to display'),
    noResultsFound: t('No results found'),
    search: t('Search'),
    showHideSearch: t('Show/Hide search'),
    sortByColumnAsc: t('Sort by {column} ascending'),
    sortByColumnDesc: t('Sort by {column} descending'),
    sortedByColumnAsc: t('Sorted by {column} ascending'),
    sortedByColumnDesc: t('Sorted by {column} descending'),
    toggleDensity: t('Toggle density'),
    toggleFullScreen: t('Toggle full screen'),
    unsorted: t('Unsorted'),
  };
}
