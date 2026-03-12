import React from 'react';

import { useOutletContext } from 'react-router-dom';

import CapitalTable from 'components/tables/capital/CapitalTable';

export default function Capital() {
  const props = useOutletContext();

  return <CapitalTable {...props} />;
}
