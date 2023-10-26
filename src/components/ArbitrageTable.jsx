import React, { useCallback, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import BlockIcon from '@mui/icons-material/Block';

import { styled, useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import formatIntlNumber from 'utils/formatIntlNumber';

import MaterialReactTable from 'components/MaterialReactTable';

const CustomChip = styled(Box)(({ theme }) => ({
  borderRadius: 2,
  color: theme.palette.dark.main,
  fontSize: 11,
  fontWeight: 700,
  padding: 2,
  textAlign: 'center',
  textTransform: 'uppercase',
}));

export default function ArbitrageTable({ data }) {
  const { i18n, t } = useTranslation();

  const theme = useTheme();

  const [expanded, setExpanded] = useState({});

  const renderStrategyCell = (row) => (
    <Stack spacing={0.5}>
      <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
        <CustomChip sx={{ bgcolor: 'warning.main' }}>Margin</CustomChip>
        <CustomChip sx={{ bgcolor: 'error.main', mr: 3 }}>S</CustomChip>
        {row.original.icon ? (
          <img
            loading="lazy"
            height="16"
            width="16"
            src={row.original.icon}
            alt={row.original.symbol}
          />
        ) : (
          <BlockIcon color="secondary" sx={{ fontSize: 16 }} />
        )}
        <Typography
          color="primary"
          fontSize="small"
          sx={{ fontWeight: 'bold' }}
        >
          {row.original.symbol}
        </Typography>
      </Stack>
      <Stack direction="row" spacing={0.5}>
        <CustomChip sx={{ bgcolor: 'info.main' }}>Future</CustomChip>
        <CustomChip sx={{ bgcolor: 'success.main' }}>L</CustomChip>
        {row.original.icon ? (
          <img
            loading="lazy"
            height="16"
            width="16"
            src={row.original.icon}
            alt={row.original.symbol}
          />
        ) : (
          <BlockIcon color="secondary" sx={{ fontSize: 16 }} />
        )}
        <Typography
          color="primary"
          fontSize="small"
          sx={{ fontWeight: 'bold' }}
        >
          {row.original.symbol}
        </Typography>
      </Stack>
    </Stack>
  );

  const columns = useMemo(
    () => [
      {
        header: t('Strategy'),
        accessorKey: 'strategy',
        size: 50,
        muiTableHeadCellProps: { align: 'left' },
        Cell: ({ row, renderedCellValue }) => renderStrategyCell(row),
      },
      {
        header: t('Price'),
        accessorKey: 'price',
        enableGlobalFilter: false,
        size: 50,
        Cell: ({ cell }) => formatIntlNumber(cell.getValue(), 4),
      },
      {
        header: t('Gap'),
        accessorKey: 'gap',
        enableGlobalFilter: false,
        size: 50,
      },
      {
        header: t('Funding Fee'),
        accessorKey: 'funding',
        enableGlobalFilter: false,
        size: 50,
      },
    ],
    [i18n.language]
  );
  return (
    <Box>
      <MaterialReactTable
        columns={columns}
        data={data || []}
        initialState={{
          columnOrder: columns.map((col) => col.accessorKey),
          columnVisibility: {},
          density: 'compact',
          showColumnFilters: false,
          // showGlobalFilter: true,
        }}
        state={{ expanded }}
        // renderDetailPanel={({ row }) => (
        //   <Box>
        //     <Collapse unmountOnExit in={row.getIsExpanded()}>
        //       <React.Suspense>
        //       </React.Suspense>
        //     </Collapse>
        //   </Box>
        // )}
        muiSearchTextFieldProps={{
          inputProps: {
            placeholder: t('Search {{size}} coins', {
              size: data.length,
            }),
          },
        }}
        muiTableHeadCellProps={{ align: 'right' }}
        muiTableBodyCellProps={{ align: 'right', sx: { fontSize: 13 } }}
        muiTableBodyRowProps={({ row }) => ({
          onClick: (e) => {
            if (
              e.target.classList.contains('MuiTableCell-root') &&
              !e.target.classList.contains('Mui-TableBodyCell-DetailPanel')
            )
              setExpanded({ ...expanded, [row.id]: !expanded[row.id] });
          },
          sx: { cursor: 'pointer' },
        })}
      />
    </Box>
  );
}
