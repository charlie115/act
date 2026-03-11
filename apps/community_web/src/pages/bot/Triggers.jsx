import React from 'react';

import { useOutletContext } from 'react-router-dom';

import TriggersTable from 'components/tables/trigger/TriggersTable';

export default function Triggers() {
  const props = useOutletContext();

  return <TriggersTable {...props} />;
}
