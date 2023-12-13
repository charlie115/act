import React, { useEffect, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import Stack from '@mui/material/Stack';

import CheckBoxIcon from '@mui/icons-material/CheckBox';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import {
  useGetAssetsQuery,
  useGetFundingRateDiffQuery,
  usePostAssetMutation,
} from 'redux/api/drf/infocore';

import { useTranslation } from 'react-i18next';

import { usePrevious } from '@uidotdev/usehooks';

import isEqual from 'lodash/isEqual';
import orderBy from 'lodash/orderBy';
import uniq from 'lodash/uniq';
import uniqBy from 'lodash/uniqBy';

import DropdownMenu from 'components/DropdownMenu';
import ReactTableUI from 'components/ReactTableUI';

import { EXCHANGE_LIST } from 'constants/lists';

import renderFundingRateCell from './renderFundingRateCell';
import renderFundingRateDiffCell from './renderFundingRateDiffCell';
import renderIconCell from './renderIconCell';
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

  const [sameExchangeChecked, setSameExchangeChecked] = useState(false);

  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: DEFAULT_PAGE_SIZE,
  });

  const { data, isLoading } = useGetFundingRateDiffQuery(
    {},
    { pollingInterval: 1000 * 60 }
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
        maxSize: isMobile ? 25 : 80,
        header: <span />,
        cell: renderIconCell,
        props: { rowSpan: 2 },
      },
      {
        accessorKey: 'symbol',
        maxSize: isMobile ? 75 : 180,
        header: t('Symbol'),
        props: isMobile ? { sx: { fontSize: 10 } } : undefined,
      },
      {
        accessorKey: 'market',
        maxSize: isMobile ? 95 : 250,
        header: t('Market'),
        cell: renderMarketCell,
      },
      {
        accessorKey: 'fundingRate',
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
        icon: assetsData?.[item.base_asset]?.icon,
        exchange: item.exchange_x,
        quote_asset: item.quote_asset_x,
        market: item.market_code_x,
        symbol: item.symbol_x,
        fundingTime: item.funding_time_x,
        fundingRate: item.funding_rate_x * 100,
        fundingRateDiff: item.funding_rate_diff * 100,
        subRows: [
          {
            rowId: `${item.base_asset}-${idx}-sub`,
            icon: false,
            name: item.base_asset,
            exchange: item.exchange_y,
            quote_asset: item.quote_asset_y,
            market: item.market_code_y,
            symbol: item.symbol_y,
            fundingTime: item.funding_time_y,
            fundingRate: item.funding_rate_y * 100,
            fundingRateDiff: false,
            ...item,
          },
        ],
        ...item,
      })) || [],
    [data, assetsData, sameExchangeChecked, selectedExchange?.value]
  );

  useEffect(() => {
    tableRef.current.toggleAllRowsExpanded(true);
  }, [tableData]);

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
          options={{
            getRowId: (row) => row.rowId,
            state: { pagination },
            onPaginationChange: setPagination,
          }}
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
