import React from 'react';

export default function renderAutoRepeatStatusCell({ cell, table }) {
  const isMobile = table.options.meta?.isMobile;
  return (
    <span style={{ 
      fontSize: isMobile ? '0.4rem' : 'inherit',
      fontWeight: isMobile ? '500' : 'normal'
    }}>
      {cell.getValue()}
    </span>
  );
}