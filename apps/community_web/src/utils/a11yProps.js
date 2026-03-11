export default ({ name, id }) => ({
  id: `${name}-tab-${id}`,
  'aria-controls': `${name}-tabpanel-${id}`,
});
