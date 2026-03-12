import React from 'react';
import { useOutletContext } from 'react-router-dom';

import ScannerTable from 'components/tables/scanner/ScannerTable';

export default function Scanner() {
  const props = useOutletContext();

  return <ScannerTable {...props} />;
} 