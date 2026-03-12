import React from 'react';

import { useOutletContext } from 'react-router-dom';

import PositionTable from 'components/tables/position/PositionTable';

export default function Position() {
  const props = useOutletContext();

  return <PositionTable {...props} />;
}
