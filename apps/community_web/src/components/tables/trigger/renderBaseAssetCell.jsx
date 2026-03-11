import React from 'react';

export default function renderBaseAssetCell({ cell, table }) {
  const isMobile = table.options.meta?.isMobile;
  return (
    <span style={{ 
      fontWeight: isMobile ? '500' : 'normal'
    }}>
      {cell.getValue()}
    </span>
  );
}