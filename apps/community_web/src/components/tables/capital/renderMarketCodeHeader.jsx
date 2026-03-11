import React from 'react';

export default function renderMarketCodeHeader({ column, table }) {
  const { marketCodes } = table.options.meta;
  const marketCode = marketCodes[column.id];
  return (
    <>
      {marketCode.icon} {marketCode.getLabel()}
    </>
  );
}
