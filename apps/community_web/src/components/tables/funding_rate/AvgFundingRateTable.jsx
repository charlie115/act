import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';

import CheckBoxIcon from '@mui/icons-material/CheckBox';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InsightsIcon from '@mui/icons-material/Insights';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import {
  useGetAssetsQuery,
  useGetAverageFundingRateQuery,
  usePostAssetMutation,
} from 'redux/api/drf/infocore';

import { useTranslation } from 'react-i18next';

import { useDebounce, usePrevious } from '@uidotdev/usehooks';

import isEqual from 'lodash/isEqual';
import orderBy from 'lodash/orderBy';
import uniqBy from 'lodash/uniqBy';

import AssetSearchInput from 'components/AssetSearchInput';
import DropdownMenu from 'components/DropdownMenu';
import LightWeightFundingRateChart from 'components/charts/LightWeightFundingRateChart';
import ReactTableUI from 'components/ReactTableUI';

import { EXCHANGE_LIST } from 'constants/lists';

import renderAssetIconCell from 'components/tables/common/renderAssetIconCell';
import renderExpandCell from 'components/tables/common/renderExpandCell';
import renderFundingRateCell from './renderFundingRateCell';
import renderMarketCell from './renderMarketCell';

const DEFAULT_PAGE_SIZE = 50;

export default function AvgFundingRateTable() {
  const tableRef = useRef();

  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [assets, setAssets] = useState([]);
  const [expanded, setExpanded] = useState({});

  const [searchValue, setSearchValue] = useState('');
  const globalFilter = useDebounce(searchValue, 300);

  const [marketList, setMarketList] = useState([]);
  const [selectedMarket, setSelectedMarket] = useState();

  const [avgFundingRateParams, setAvgFundingRateParams] = useState({ n: 10 });
  const [n, setN] = useState(10);

  const debouncedN = useDebounce(n, 1000);

  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: DEFAULT_PAGE_SIZE,
  });

  const { data, isLoading } = useGetAverageFundingRateQuery(
    avgFundingRateParams,
    { pollingInterval: 1000 * 60, skip: !avgFundingRateParams }
  );

  const { data: assetsData, isSuccess: isAssetsDataSuccess } =
    useGetAssetsQuery();
  const [postAsset] = usePostAssetMutation();

  useEffect(() => {
    setAssets(uniqBy(data, 'base_asset').map((item) => item.base_asset));
    const markets = [
      { label: t('All Markets'), value: 'ALL', icon: <CheckBoxIcon /> },
    ].concat(
      uniqBy(data, 'market_code').map((item) => {
        const icon = EXCHANGE_LIST.find(
          (exchange) => exchange.value === item.market_code.split('_')?.[0]
        )?.icon;
        return {
          label: item.market_code,
          value: item.market_code,
          icon: (
            <Box
              component="img"
              src={icon}
              alt={item.market_code}
              sx={{
                height: { xs: 16, md: 18 },
                width: { xs: 16, md: 18 },
              }}
            />
          ),
        };
      })
    );
    setMarketList(markets);
    if (!selectedMarket) setSelectedMarket(markets[0]);
  }, [data, selectedMarket, i18n.language]);

  useEffect(() => {
    if (debouncedN) setAvgFundingRateParams({ n: debouncedN });
  }, [debouncedN]);

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
        size: isMobile ? 20 : 40,
        header: <span />,
        cell: renderAssetIconCell,
      },
      {
        accessorKey: 'symbol',
        size: isMobile ? 110 : 200,
        header: t('Symbol'),
        props: isMobile ? { sx: { fontSize: 10 } } : undefined,
      },
      {
        accessorKey: 'market',
        size: isMobile ? 120 : 250,
        header: t('Market'),
        cell: renderMarketCell,
      },
      {
        accessorKey: 'fundingRate',
        size: isMobile ? 80 : 180,
        header: `${t('Avg. of the Last {{n}} Funding Rates', {
          n: avgFundingRateParams?.n,
          // n: debouncedN,
        })} (N)`,
        cell: renderFundingRateCell,
      },
      {
        accessorKey: 'chart',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 11,
        cell: renderExpandCell,
        header: <span />,
      },
    ],
    [avgFundingRateParams, i18n.language, isMobile]
  );

  const tableData = useMemo(
    () =>
      orderBy(
        data?.filter(
          (item) =>
            selectedMarket?.value === 'ALL' ||
            item.market_code === selectedMarket?.value
        ),
        'funding_rate',
        'desc'
      ).map((item, idx) => ({
        rowId: `${item.base_asset}-${idx}`,
        name: item.base_asset,
        icon: assetsData?.[item.base_asset]?.icon,
        market: item.market_code,
        quoteAsset: item.quote_asset,
        symbol: item.symbol,
        exchange: item.market_code.split('_')?.[0],
        fundingRate: item.funding_rate * 100,
        ...item,
      })) || [],
    [data, assetsData, selectedMarket?.value]
  );

  const renderSubComponent = useCallback(({ row, meta }) => (
    <Box>
      <LightWeightFundingRateChart
        symbol={row.original.symbol}
        baseAsset={row.original.name}
        marketCode={`${row.original.market}/${row.original.quoteAsset}`}
        {...meta}
      />
    </Box>
  ));

  const rows = tableRef.current?.getRowModel().rows;

  return (
    <>
      <Stack direction="row" spacing={{ xs: 1, sm: 2 }} sx={{ mb: 2 }}>
        <DropdownMenu
          value={selectedMarket}
          options={marketList}
          onSelectItem={setSelectedMarket}
          buttonStyle={{
            justifyContent: 'flex-start',
            minWidth: isMobile ? 190 : 220,
          }}
        />
        <TextField
          id="n-value"
          label="N"
          variant="outlined"
          type="number"
          error={!n}
          value={`${n}`}
          onChange={(e) => {
            if (e.target.value) {
              const value = parseInt(e.target.value, 10);
              setN(value);
            } else setN();
          }}
          inputProps={{ sx: { p: 1.25 } }}
          sx={{ mr: 'auto!important', width: isMobile ? 80 : 120 }}
        />
        <AssetSearchInput
          customList={assets}
          onChange={(value) => setSearchValue(value)}
        />
      </Stack>
      <Box sx={{ boxShadow: 2 }}>
        <ReactTableUI
          ref={tableRef}
          columns={columns}
          data={tableData}
          options={{
            state: { expanded, globalFilter, pagination },
            onExpandedChange: (newExpanded) => setExpanded(newExpanded()),
            onPaginationChange: setPagination,
            meta: { theme, isMobile, expandIcon: InsightsIcon },
          }}
          renderSubComponent={renderSubComponent}
          getCellProps={() => ({ onClick: () => {}, sx: { height: 40 } })}
          getRowProps={(row) => ({
            onClick: () => row.toggleExpanded(!row.getIsExpanded()),
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
