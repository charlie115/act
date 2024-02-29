import React, {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import { flexRender } from '@tanstack/react-table';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import Stack from '@mui/material/Stack';

import CheckBoxIcon from '@mui/icons-material/CheckBox';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InsightsIcon from '@mui/icons-material/Insights';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import {
  useGetAssetsQuery,
  useGetFundingRateDiffQuery,
  useGetMarketCodesQuery,
  usePostAssetMutation,
} from 'redux/api/drf/infocore';

import { useTranslation } from 'react-i18next';

import { usePrevious } from '@uidotdev/usehooks';

import isEqual from 'lodash/isEqual';
import orderBy from 'lodash/orderBy';
import uniq from 'lodash/uniq';
import uniqBy from 'lodash/uniqBy';

import DropdownMenu from 'components/DropdownMenu';
import PremiumDataChartViewer from 'components/PremiumDataChartViewer';
import ReactTableUI, { TableCell, TableRow } from 'components/ReactTableUI';

import { EXCHANGE_LIST } from 'constants/lists';

import renderExpandCell from 'components/tables/common/renderExpandCell';
import renderIconCell from 'components/tables/common/renderIconCell';
import renderFundingRateCell from './renderFundingRateCell';
import renderFundingRateDiffCell from './renderFundingRateDiffCell';
import renderMarketCell from './renderMarketCell';

const DEFAULT_PAGE_SIZE = 100;

export default function FundingRateDiffTable() {
  const tableRef = useRef();

  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [assets, setAssets] = useState([]);

  const [exchangeList, setExchangeList] = useState([]);
  const [selectedExchange, setSelectedExchange] = useState();

  const [marketCodes, setMarketCodes] = useState();
  const [selectedRow, setSelectedRow] = useState();

  const [sameExchangeChecked, setSameExchangeChecked] = useState(false);

  const [expanded, setExpanded] = useState({});
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: DEFAULT_PAGE_SIZE,
  });

  const [skipMarketCodesQuery, setSkipMarketCodesQuery] = useState(false);

  const { data, isLoading } = useGetFundingRateDiffQuery(
    {},
    { pollingInterval: 1000 * 60 }
  );

  const { data: marketCodesData, isSuccess } = useGetMarketCodesQuery(
    {},
    { skip: skipMarketCodesQuery }
  );

  const { data: assetsData, isSuccess: isAssetsDataSuccess } =
    useGetAssetsQuery();
  const [postAsset] = usePostAssetMutation();

  useEffect(() => {
    setAssets(uniqBy(data, 'base_asset').map((item) => item.base_asset));
  }, [data]);

  useEffect(() => {
    const exchanges = [
      { label: t('All Exchanges'), value: 'ALL', icon: <CheckBoxIcon /> },
    ].concat(
      uniq(
        data?.reduce((acc, v) => acc.concat([v.exchange_x, v.exchange_y]), [])
      ).map((item) => {
        const exchange = EXCHANGE_LIST.find((o) => o.value === item);
        return {
          label: exchange?.getLabel() || item,
          value: exchange?.value || item,
          icon: (
            <Box
              component="img"
              src={exchange?.icon}
              alt={exchange?.label || item}
              sx={{
                height: { xs: 16, md: 18 },
                width: { xs: 16, md: 18 },
              }}
            />
          ),
        };
      })
    );
    setExchangeList(exchanges);
    if (!selectedExchange) setSelectedExchange(exchanges[0]);
  }, [data, selectedExchange, i18n.language]);

  useEffect(() => {
    if (isSuccess) {
      if (selectedRow) {
        let matchedMarketCodes;
        const { marketX, marketY, quoteAssetX, quoteAssetY } =
          selectedRow.original;
        const marketCodeX = `${marketX}/${quoteAssetX}`;
        const marketCodeY = `${marketY}/${quoteAssetY}`;
        if (Object.keys(marketCodesData).includes(marketCodeX)) {
          if (marketCodesData[marketCodeX].includes(marketCodeY))
            matchedMarketCodes = {
              targetMarketCode: marketCodeX,
              originMarketCode: marketCodeY,
            };
        } else if (Object.keys(marketCodesData).includes(marketCodeY)) {
          if (marketCodesData[marketCodeY].includes(marketCodeX))
            matchedMarketCodes = {
              targetMarketCode: marketCodeY,
              originMarketCode: marketCodeX,
            };
        }
        setMarketCodes(matchedMarketCodes);
        selectedRow?.toggleExpanded(true);
      }
      setSkipMarketCodesQuery(true);
    }
  }, [marketCodesData, isSuccess]);

  const prevAssets = usePrevious(assets);
  const prevIsAssetsDataSuccess = usePrevious(isAssetsDataSuccess);
  useEffect(() => {
    if (!prevIsAssetsDataSuccess && isAssetsDataSuccess)
      if (!isEqual(prevAssets, assets))
        assets.forEach((asset) => {
          if (!assetsData?.[asset]) postAsset({ symbol: asset });
        });
  }, [assets, assetsData, isAssetsDataSuccess]);

  const columns = useMemo(
    () => [
      {
        accessorKey: 'icon',
        enableGlobalFilter: false,
        enableSorting: false,
        maxSize: isMobile ? 15 : 80,
        header: <span />,
        cell: renderIconCell,
        props: { rowSpan: 2 },
      },
      {
        accessorKey: 'symbolX',
        maxSize: isMobile ? 75 : 180,
        header: t('Symbol'),
        props: isMobile ? { sx: { fontSize: 10 } } : undefined,
      },
      {
        accessorKey: 'symbolY',
        maxSize: isMobile ? 75 : 180,
        header: t('Symbol'),
        props: isMobile ? { sx: { fontSize: 10 } } : undefined,
      },
      {
        accessorKey: 'marketX',
        maxSize: isMobile ? 95 : 250,
        header: t('Market'),
        cell: renderMarketCell,
      },
      {
        accessorKey: 'marketY',
        maxSize: isMobile ? 95 : 250,
        header: t('Market'),
        cell: renderMarketCell,
      },
      {
        accessorKey: 'fundingRateX',
        maxSize: isMobile ? 65 : 180,
        header: t('Funding Rate'),
        cell: renderFundingRateCell,
      },
      {
        accessorKey: 'fundingRateY',
        maxSize: isMobile ? 65 : 180,
        header: t('Funding Rate'),
        cell: renderFundingRateCell,
      },
      {
        accessorKey: 'fundingRateDiff',
        maxSize: isMobile ? 60 : undefined,
        header: t('Funding Rate Difference'),
        cell: renderFundingRateDiffCell,
        props: {
          rowSpan: 2,
          sx: { justifyContent: 'center', textAlign: 'center' },
        },
      },
      {
        accessorKey: 'chart',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 11,
        cell: renderExpandCell,
        header: <span />,
        props: {
          rowSpan: 2,
          sx: { justifyContent: 'center', textAlign: 'center' },
        },
      },
    ],
    [isMobile, i18n.language]
  );

  const tableData = useMemo(
    () =>
      orderBy(
        data?.filter((item) => {
          let flag = selectedExchange?.value === 'ALL';
          if (selectedExchange?.value !== 'ALL')
            flag =
              item.exchange_x === selectedExchange?.value &&
              item.exchange_y === selectedExchange?.value;
          if (sameExchangeChecked)
            flag = flag && item.exchange_x === item.exchange_y;
          return flag;
        }),
        'funding_rate_diff',
        'desc'
      ).map((item, idx) => ({
        rowId: `${item.base_asset}-${idx}`,
        name: item.base_asset,
        baseAsset: item.base_asset,
        icon: assetsData?.[item.base_asset]?.icon,
        exchangeX: item.exchange_x,
        exchangeY: item.exchange_y,
        marketX: item.market_code_x,
        marketY: item.market_code_y,
        quoteAssetX: item.quote_asset_x,
        quoteAssetY: item.quote_asset_y,
        symbolX: item.symbol_x,
        symbolY: item.symbol_y,
        fundingTimeX: item.funding_time_x,
        fundingTimeY: item.funding_time_y,
        fundingRateX: item.funding_rate_x * 100,
        fundingRateY: item.funding_rate_y * 100,
        fundingRateDiff: item.funding_rate_diff * 100,
        ...item,
      })) || [],
    [data, assetsData, sameExchangeChecked, selectedExchange?.value]
  );

  const renderRow = useCallback(
    ({ row, table, renderSubComponent, getCellProps, getRowProps }) => (
      <Fragment key={row.id}>
        <TableRow {...(getRowProps ? getRowProps(row) : {})}>
          {row.getVisibleCells().map((cell) => (
            <TableCell
              key={cell.id}
              {...(getCellProps ? getCellProps(cell) : {})}
              {...cell.column.columnDef.props}
            >
              {flexRender(cell.column.columnDef.cell, {
                ...cell.getContext(),
                ...table.options.meta,
              })}
            </TableCell>
          ))}
        </TableRow>
        <TableRow {...(getRowProps ? getRowProps(row) : {})}>
          {row
            .getAllCells()
            .filter((cell) => !cell.column.getIsVisible())
            .map((cell) => (
              <TableCell
                key={`${cell.id}-sub-row`}
                {...(getCellProps ? getCellProps(cell) : {})}
                {...cell.column.columnDef.props}
              >
                {flexRender(cell.column.columnDef.cell, {
                  ...cell.getContext(),
                  ...table.options.meta,
                  isMobile,
                  theme,
                })}
              </TableCell>
            ))}
        </TableRow>
        {row.getIsExpanded() && renderSubComponent && (
          <TableRow key={`${row.id}-expand-panel`}>
            <TableCell colSpan={row.getVisibleCells().length}>
              {renderSubComponent({ row, meta: table.options.meta })}
            </TableCell>
          </TableRow>
        )}
      </Fragment>
    ),
    []
  );

  const renderSubComponent = useCallback(
    ({ row, meta }) => (
      <Box>
        <PremiumDataChartViewer
          showFundingRate
          showFundingRateDiff
          showMarketCodes
          baseAssetData={row.original}
          marketCodes={
            marketCodes ?? {
              targetMarketCode: `${row.original.marketX}/${row.original.quoteAssetX}`,
              originMarketCode: `${row.original.marketY}/${row.original.quoteAssetY}`,
            }
          }
          defaultChartDataType={!marketCodes ? 'FR' : undefined}
          defaultDisabledChartDataType={
            !marketCodes ? { tp: true, LS: true, SL: true } : null
          }
          {...meta}
        />
      </Box>
    ),
    [marketCodes]
  );

  const rows = tableRef.current?.getRowModel().rows;

  return (
    <>
      <Stack direction="row" spacing={{ xs: 1, sm: 2 }} sx={{ mb: 2 }}>
        <DropdownMenu
          value={selectedExchange}
          options={exchangeList}
          onSelectItem={setSelectedExchange}
          buttonStyle={{ justifyContent: 'flex-start' }}
        />
        <FormControlLabel
          control={<Checkbox />}
          label={t('Within the same exchange')}
          onChange={(e) => setSameExchangeChecked(e.target.checked)}
        />
      </Stack>
      <Box sx={{ boxShadow: 2 }}>
        <ReactTableUI
          ref={tableRef}
          columns={columns}
          data={tableData}
          renderRow={renderRow}
          renderSubComponent={renderSubComponent}
          options={{
            getRowId: (row) => row.rowId,
            state: {
              columnVisibility: {
                fundingRateY: false,
                marketY: false,
                symbolY: false,
              },
              expanded,
              pagination,
            },
            onExpandedChange: setExpanded,
            onPaginationChange: setPagination,
            meta: { theme, isMobile, expandIcon: InsightsIcon },
          }}
          getRowProps={(row) => ({
            onClick: () => {
              if (!row.getIsExpanded()) {
                tableRef.current.toggleAllRowsExpanded(false);
                setMarketCodes();
                setSelectedRow(row);
                setSkipMarketCodesQuery(false);
              } else {
                row.toggleExpanded(false);
                setSelectedRow();
              }
            },
            sx: {
              cursor: 'pointer',
              ...(row.getIsExpanded()
                ? { bgcolor: theme.palette.background.paper }
                : {}),
            },
          })}
          showProgressBar={isLoading}
          isLoading={isLoading}
        />
        {rows?.length >= DEFAULT_PAGE_SIZE && (
          <Box sx={{ textAlign: 'center' }}>
            <Button
              color={
                tableRef.current?.getCanNextPage() ? 'primary' : 'secondary'
              }
              endIcon={
                tableRef.current?.getCanNextPage() ? (
                  <ExpandMoreIcon />
                ) : (
                  <ExpandLessIcon />
                )
              }
              onClick={() => {
                tableRef.current?.setPageSize(
                  tableRef.current?.getCanNextPage()
                    ? pagination.pageSize + DEFAULT_PAGE_SIZE
                    : DEFAULT_PAGE_SIZE
                );
                if (!tableRef.current?.getCanNextPage()) window.scrollTo(0, 0);
              }}
              sx={{
                fontSize: '0.85rem',
                fontStyle: 'italic',
                letterSpacing: '0.085em',
                textTransform: 'none',
                ':hover': { backgroundColor: 'unset' },
              }}
            >
              {tableRef.current?.getCanNextPage()
                ? t('See more')
                : t('See less')}
            </Button>
          </Box>
        )}
      </Box>
    </>
  );
}
