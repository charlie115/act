import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import {
  flexRender,
  getCoreRowModel,
  getExpandedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import useMediaQuery from '@mui/material/useMediaQuery';
import { alpha, styled, useTheme } from '@mui/material/styles';

import {
  useGetAssetsQuery,
  useGetFundingRateDiffQuery,
  usePostAssetMutation,
} from 'redux/api/drf/infocore';

import { useTranslation } from 'react-i18next';

import { usePrevious, useVisibilityChange } from '@uidotdev/usehooks';

import isEqual from 'lodash/isEqual';
import orderBy from 'lodash/orderBy';

import DropdownMenu from 'components/DropdownMenu';
import ReactTableUI from 'components/ReactTableUI';

import { EXCHANGE_LIST } from 'constants/lists';

import renderFundingRateCell from './renderFundingRateCell';
import renderFundingRateDiffCell from './renderFundingRateDiffCell';
import renderIconCell from './renderIconCell';
import renderMarketCell from './renderMarketCell';

export default function FundingRateDiffTable() {
  const tableRef = useRef();

  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [assets, setAssets] = useState([]);

  const [exchangeList, setExchangeList] = useState([]);
  const [selectedExchange, setSelectedExchange] = useState();

  const [sameExchangeChecked, setSameExchangeChecked] = useState(false);

  const [fundingRateDiffParams, setFundingRateParams] = useState();

  const { data, isLoading } = useGetFundingRateDiffQuery(
    fundingRateDiffParams,
    { skip: !fundingRateDiffParams }
  ); // TODO: add page parameter

  const { data: assetsData, isSuccess: isAssetsDataSuccess } =
    useGetAssetsQuery();
  const [postAsset] = usePostAssetMutation();

  useEffect(() => {
    tableRef.current.toggleAllRowsExpanded(true);
    setAssets(Object.keys(data || []));
  }, [data]);

  useEffect(() => {
    const exchange =
      selectedExchange?.value !== 'ALL' ? selectedExchange?.value : undefined;
    setFundingRateParams({
      exchangeX: exchange,
      exchangeY: exchange,
    });
  }, [selectedExchange?.value]);

  useEffect(() => {
    const exchanges = [{ label: t('All Exchanges'), value: 'ALL' }].concat(
      EXCHANGE_LIST.map((exchange) => ({
        label: exchange.getLabel(),
        icon: (
          <Box
            component="img"
            src={exchange.icon}
            alt={exchange.label}
            sx={{
              height: { xs: 16, md: 18 },
              width: { xs: 16, md: 18 },
            }}
          />
        ),
        value: exchange.value,
      }))
    );
    setExchangeList(exchanges);
    setSelectedExchange(exchanges[0]);
  }, [i18n.language]);

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
        size: 80,
        header: <span />,
        cell: renderIconCell,
        props: { rowSpan: 2 },
      },
      {
        accessorKey: 'symbol',
        size: isMobile ? 100 : 180,
        header: t('Symbol'),
      },
      {
        accessorKey: 'market',
        size: isMobile ? 120 : 250,
        header: t('Market'),
        cell: renderMarketCell,
      },
      {
        accessorKey: 'fundingRate',
        size: isMobile ? 100 : 180,
        header: t('Funding Rate'),
        cell: renderFundingRateCell,
      },
      {
        accessorKey: 'fundingRateDiff',
        header: t('Funding Rate Difference'),
        cell: renderFundingRateDiffCell,
        props: { rowSpan: 2 },
      },
    ],
    [i18n.language]
  );

  const tableData = useMemo(
    () =>
      orderBy(
        Object.values(data || []).flat(),
        'funding_rate_diff',
        'desc'
      ).map((item, idx) => ({
        rowId: `${item.base_asset}-${idx}`,
        name: item.base_asset,
        icon: assetsData?.[item.base_asset]?.icon,
        exchange: item.exchange_x,
        quote_asset: item.quote_asset_x,
        market: `${item.market_code_x}/${item.quote_asset_x}`,
        symbol: item.symbol_x,
        fundingTime: item.funding_time_x,
        fundingRate: item.funding_rate_x * 100,
        fundingRateDiff: item.funding_rate_diff * 100,
        subRows: [
          {
            rowId: `${item.base_asset}-${idx}`,
            icon: false,
            name: item.base_asset,
            exchange: item.exchange_y,
            quote_asset: item.quote_asset_y,
            market: `${item.market_code_y}/${item.quote_asset_y}`,
            symbol: item.symbol_y,
            fundingTime: item.funding_time_y,
            fundingRate: item.funding_rate_y * 100,
            fundingRateDiff: false,
            ...item,
          },
        ],
        ...item,
      })),
    [data, assetsData]
  );

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
            // defaultColumn: { sortingFn },
            state: {
              pagination: { pageIndex: 0, pageSize: tableData.length },
              // manualSorting: true,
            },
          }}
          showProgressBar={isLoading}
          isLoading={isLoading}
          // renderRow={(props) => <CustomRow {...props} />}
        />
      </Box>
    </>
  );
}
