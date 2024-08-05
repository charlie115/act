import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt';
import RemoveIcon from '@mui/icons-material/Remove';
import StarIcon from '@mui/icons-material/Star';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';

import { useTheme } from '@mui/material/styles';

import { useGetFundingRateQuery } from 'redux/api/drf/infocore';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';
import { useSelector } from 'react-redux';

import isUndefined from 'lodash/isUndefined';
import orderBy from 'lodash/orderBy';

import { DateTime } from 'luxon';

import { useTranslation } from 'react-i18next';

import ChartDataTypeSelector from 'components/ChartDataTypeSelector';
import ExchangeWalletNetworks from 'components/ExchangeWalletNetworks';
import IntervalSelector from 'components/IntervalSelector';

import { MARKET_CODE_LIST } from 'constants/lists';
import { USER_ROLE } from 'constants';

import LightWeightAvgFundingRateDiffChart from 'components/charts/LightWeightAvgFundingRateDiffChart';
import LightWeightPremiumKlineChart from 'components/charts/LightWeightPremiumKlineChart';
import LightWeightFundingRateChart from 'components/charts/LightWeightFundingRateChart';
import LightWeightFundingRateDiffChart from 'components/charts/LightWeightFundingRateDiffChart';

const PremiumDataChartViewer = forwardRef(
  (
    {
      baseAssetData,
      marketCodes,
      defaultChartDataType,
      defaultDisabledChartDataType,
      isKimpExchange,
      isTetherPriceView,
      onIntervalChange,
      onAddFavoriteAsset,
      onRemoveFavoriteAsset,
      queryKey,
      showExchangeWallets,
      showAvgFundingRateDiff,
      showFundingRate,
      showFundingRateDiff,
      showMarketCodes,
      triggerConfig,
    },
    ref
  ) => {
    const {
      name: baseAsset,
      favoriteAssetId,
      walletNetworks,
      walletStatus,
    } = baseAssetData;

    const { timezone: tz } = useSelector((state) => state.app);

    const { loggedin, user } = useSelector((state) => state.auth);
    const isAuthorized = loggedin && user.role !== USER_ROLE.visitor;

    const theme = useTheme();

    const { t } = useTranslation();

    const wrapperRef = useRef();

    const premiumKlineChartRef = useRef();

    useImperativeHandle(
      ref,
      () => ({
        getKlineChartRef: () => premiumKlineChartRef,
      }),
      []
    );

    const [title, setTitle] = useState();

    const [klineInterval, setKlineInterval] = useState('1T');

    const [chartDataType, setChartDataType] = useState(defaultChartDataType);
    const [disabledChartDataType, setDisabledChartDataType] = useState();

    const [subtrahend, setSubtrahend] = useState('origin');

    const [isFundingRateValid, setIsFundingRateValid] = useState(false);

    const { targetMarketCode, originMarketCode } = useMemo(
      () => ({
        targetMarketCode: MARKET_CODE_LIST.find(
          (o) => o.value === marketCodes?.targetMarketCode
        ) ?? {
          ...MARKET_CODE_LIST.find(
            (o) => o.exchange === marketCodes?.targetMarketCode?.split('_')[0]
          ),
          getLabel: () => marketCodes?.targetMarketCode,
          value: marketCodes?.targetMarketCode,
        },
        originMarketCode: MARKET_CODE_LIST.find(
          (o) => o.value === marketCodes?.originMarketCode
        ) ?? {
          ...MARKET_CODE_LIST.find(
            (o) => o.exchange === marketCodes?.originMarketCode?.split('_')[0]
          ),
          getLabel: () => marketCodes?.originMarketCode,
          value: marketCodes?.originMarketCode,
        },
      }),
      [marketCodes]
    );

    const { data } = useGetRealTimeKlineQuery(
      {
        ...marketCodes,
        interval: klineInterval,
        queryKey,
      },
      { skip: !marketCodes }
    );

    const { data: apiTargetData } = useGetFundingRateQuery(
      {
        baseAsset,
        tz,
        marketCode: marketCodes.targetMarketCode,
        lastN: 3,
      },
      { skip: !showAvgFundingRateDiff }
    );
    const { data: apiOriginData } = useGetFundingRateQuery(
      {
        baseAsset,
        tz,
        marketCode: marketCodes.originMarketCode,
        lastN: 3,
      },
      { skip: !showAvgFundingRateDiff }
    );

    useEffect(() => {
      const value = marketCodes?.targetMarketCode;
      setTitle(`${baseAsset} / ${value?.split('/').pop()}`);
      if (marketCodes) setKlineInterval('1T');
    }, [marketCodes]);

    useEffect(() => {
      if (
        data &&
        !data.disconnected &&
        !chartDataType &&
        !defaultDisabledChartDataType
      ) {
        if (data?.[baseAsset]?.tp === null) {
          setChartDataType('LS');
          setDisabledChartDataType({ tp: true });
        } else setChartDataType('tp');
      }
    }, [data?.[baseAsset]?.tp, chartDataType, defaultDisabledChartDataType]);

    useEffect(() => {
      if (chartDataType === 'FRD' || chartDataType === 'AFRD')
        setSubtrahend('origin');
      else setSubtrahend();
    }, [chartDataType]);

    useEffect(() => {
      if (onIntervalChange) onIntervalChange(klineInterval);
    }, [klineInterval]);

    useEffect(() => {
      if (defaultDisabledChartDataType)
        setDisabledChartDataType(defaultDisabledChartDataType);
    }, [defaultDisabledChartDataType]);

    useEffect(() => {
      if (apiTargetData?.[baseAsset] && apiOriginData?.[baseAsset]) {
        const fundingRateData = {};
        apiTargetData?.[baseAsset]?.forEach((target) => {
          if (!fundingRateData[target.funding_time]) {
            const origin = apiOriginData?.[baseAsset]?.find(
              (o) => o.funding_time === target.funding_time
            );
            if (origin)
              fundingRateData[target.funding_time] = {
                target,
                origin,
              };
          }
        });
        const isValid = orderBy(
          Object.keys(fundingRateData ?? {}),
          (o) => DateTime.fromISO(o).toMillis(),
          'asc'
        ).reduce((acc, value) => {
          const { target, origin } = fundingRateData[value];
          return acc && origin?.funding_time === target?.funding_time;
        }, true);
        setIsFundingRateValid(isValid);
      }
    }, [apiTargetData?.[baseAsset], apiOriginData?.[baseAsset]]);

    const isFavorite = !isUndefined(favoriteAssetId);

    return (
      <Card
        ref={wrapperRef}
        onClick={(e) => e.stopPropagation()}
        sx={{ borderRadius: 0 }}
      >
        <Box sx={{ bgcolor: 'background.paper' }}>
          {showExchangeWallets && (
            <Box>
              {(targetMarketCode?.value.includes('SPOT') ||
                originMarketCode?.value.includes('SPOT')) && (
                <Box sx={{ p: 2 }}>
                  <ExchangeWalletNetworks
                    direction={
                      targetMarketCode.value.includes('SPOT') &&
                      originMarketCode.value.includes('SPOT') &&
                      targetMarketCode.exchange !== originMarketCode.exchange
                        ? 'right'
                        : 'all'
                    }
                    targetMarketCode={targetMarketCode}
                    originMarketCode={originMarketCode}
                    walletNetworks={walletNetworks}
                    walletStatus={walletStatus}
                  />
                  {targetMarketCode.value.includes('SPOT') &&
                    originMarketCode.value.includes('SPOT') &&
                    targetMarketCode.exchange !== originMarketCode.exchange && (
                      <ExchangeWalletNetworks
                        direction="left"
                        targetMarketCode={targetMarketCode}
                        originMarketCode={originMarketCode}
                        walletNetworks={walletNetworks}
                        walletStatus={walletStatus}
                      />
                    )}
                </Box>
              )}
            </Box>
          )}
          <Grid container sx={{ p: 1 }}>
            <Grid
              item
              xs={6}
              sm={3}
              sx={{ display: 'flex', alignItems: 'center' }}
            >
              {onAddFavoriteAsset && onRemoveFavoriteAsset && (
                <Tooltip
                  title={
                    isFavorite
                      ? t('Remove from favorites')
                      : t('Add to favorites')
                  }
                >
                  <StarIcon
                    color={isFavorite ? 'accent' : 'secondary'}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (isFavorite) onRemoveFavoriteAsset(favoriteAssetId);
                      else onAddFavoriteAsset(baseAsset);
                    }}
                    sx={{
                      ':hover': {
                        color: theme.palette.accent.main,
                        opacity: 0.5,
                      },
                    }}
                  />
                </Tooltip>
              )}
              <Typography sx={{ fontWeight: 700, ml: 2 }}>{title}</Typography>
            </Grid>
            <Grid
              item
              xs={3}
              sm={6}
              sx={{ display: 'flex', justifyContent: 'center' }}
            >
              {chartDataType !== 'FR' &&
                chartDataType !== 'FRD' &&
                chartDataType !== 'AFRD' && (
                  <IntervalSelector
                    defaultValue={klineInterval}
                    disabled={!isAuthorized}
                    onChange={(value) => {
                      premiumKlineChartRef?.current?.reinitialize();
                      setKlineInterval(value);
                    }}
                  />
                )}
            </Grid>
            <Grid
              item
              xs={3}
              sm={3}
              sx={{ display: 'flex', justifyContent: 'end' }}
            >
              {chartDataType && (
                <ChartDataTypeSelector
                  defaultValue={chartDataType}
                  disabled={disabledChartDataType}
                  isFundingRateValid={isFundingRateValid}
                  isKimpExchange={isKimpExchange}
                  isTetherPriceView={isTetherPriceView}
                  showAvgFundingRateDiff={showAvgFundingRateDiff}
                  showFundingRate={
                    showFundingRate &&
                    (!targetMarketCode.value.includes('SPOT') ||
                      !originMarketCode.value.includes('SPOT'))
                  }
                  showFundingRateDiff={
                    showFundingRateDiff &&
                    !targetMarketCode.value.includes('SPOT') &&
                    !originMarketCode.value.includes('SPOT')
                  }
                  onChange={(value) => setChartDataType(value)}
                />
              )}
            </Grid>
          </Grid>
          <ChartRenderer
            triggerConfig={triggerConfig}
            chartDataType={chartDataType}
            klineInterval={klineInterval}
            targetMarketCode={targetMarketCode}
            originMarketCode={originMarketCode}
            marketCodes={marketCodes}
            baseAsset={baseAsset}
            subtrahend={subtrahend}
            isKimpExchange={isKimpExchange}
            isTetherPriceView={isTetherPriceView}
            queryKey={queryKey}
            showMarketCodes={showMarketCodes}
            premiumKlineChartRef={premiumKlineChartRef}
            onSwapMarketCodes={() =>
              setSubtrahend((state) =>
                state === 'origin' ? 'target' : 'origin'
              )
            }
          />
        </Box>
      </Card>
    );
  }
);

function MarketCodesRenderer({
  leftMarket,
  rightMarket,
  chartDataType,
  onSwapMarketCodes,
}) {
  const { t } = useTranslation();
  return (
    <Stack
      direction="row"
      alignItems="center"
      justifyContent="center"
      spacing={1}
      mt={2}
    >
      <Box
        component="img"
        src={leftMarket.icon}
        alt={leftMarket.getLabel()}
        sx={{ height: { xs: 16, md: 18 }, width: { xs: 16, md: 18 } }}
      />
      <Box>{leftMarket.getLabel()}</Box>
      {chartDataType === 'FRD' ? <RemoveIcon /> : <ArrowRightAltIcon />}
      <Box
        component="img"
        src={rightMarket.icon}
        alt={rightMarket.getLabel()}
        sx={{ height: { xs: 16, md: 18 }, width: { xs: 16, md: 18 } }}
      />
      <Box>{rightMarket.getLabel()}</Box>
      <Tooltip title={t('Swap')}>
        <IconButton onClick={onSwapMarketCodes}>
          <SwapHorizIcon color="info" />
        </IconButton>
      </Tooltip>
    </Stack>
  );
}

function ChartRenderer({
  triggerConfig,
  chartDataType,
  klineInterval,
  targetMarketCode,
  originMarketCode,
  marketCodes,
  baseAsset,
  subtrahend,
  isKimpExchange,
  isTetherPriceView,
  showMarketCodes,
  queryKey,
  premiumKlineChartRef,
  onSwapMarketCodes,
}) {
  switch (chartDataType) {
    case 'FR':
      return (
        <Grid container>
          {!targetMarketCode.value.includes('SPOT') && (
            <Grid
              item
              xs={12}
              md={originMarketCode.value.includes('SPOT') ? 12 : 6}
            >
              <Typography align="center">
                {targetMarketCode.getLabel()}
              </Typography>
              <LightWeightFundingRateChart
                baseAsset={baseAsset}
                marketCode={targetMarketCode.value}
              />
            </Grid>
          )}
          {!originMarketCode.value.includes('SPOT') && (
            <Grid
              item
              xs={12}
              md={targetMarketCode.value.includes('SPOT') ? 12 : 6}
            >
              <Typography align="center">
                {originMarketCode.getLabel()}
              </Typography>
              <LightWeightFundingRateChart
                baseAsset={baseAsset}
                marketCode={originMarketCode.value}
              />
            </Grid>
          )}
        </Grid>
      );
    case 'FRD':
      return (
        <>
          <MarketCodesRenderer
            {...(chartDataType !== 'FRD'
              ? { leftMarket: targetMarketCode, rightMarket: originMarketCode }
              : {
                  leftMarket:
                    subtrahend === 'origin'
                      ? targetMarketCode
                      : originMarketCode,
                  rightMarket:
                    subtrahend === 'origin'
                      ? originMarketCode
                      : targetMarketCode,
                })}
            onSwapMarketCodes={onSwapMarketCodes}
          />
          <LightWeightFundingRateDiffChart
            baseAsset={baseAsset}
            marketCodes={{
              targetMarketCode: targetMarketCode.value,
              originMarketCode: originMarketCode.value,
            }}
            subtrahend={subtrahend}
          />
        </>
      );
    case 'AFRD':
      return (
        <>
          <MarketCodesRenderer
            {...(chartDataType !== 'AFRD'
              ? { leftMarket: targetMarketCode, rightMarket: originMarketCode }
              : {
                  leftMarket:
                    subtrahend === 'origin'
                      ? targetMarketCode
                      : originMarketCode,
                  rightMarket:
                    subtrahend === 'origin'
                      ? originMarketCode
                      : targetMarketCode,
                })}
            onSwapMarketCodes={onSwapMarketCodes}
          />
          <LightWeightAvgFundingRateDiffChart
            baseAsset={baseAsset}
            marketCodes={{
              targetMarketCode: targetMarketCode.value,
              originMarketCode: originMarketCode.value,
            }}
            subtrahend={subtrahend}
          />
        </>
      );
    case 'SL':
    case 'LS':
    case 'tp':
      return (
        <>
          {showMarketCodes && (
            <MarketCodesRenderer
              {...(chartDataType !== 'FRD'
                ? {
                    leftMarket: targetMarketCode,
                    rightMarket: originMarketCode,
                  }
                : {
                    leftMarket:
                      subtrahend === 'origin'
                        ? targetMarketCode
                        : originMarketCode,
                    rightMarket:
                      subtrahend === 'origin'
                        ? originMarketCode
                        : targetMarketCode,
                  })}
              onSwapMarketCodes={onSwapMarketCodes}
            />
          )}
          <LightWeightPremiumKlineChart
            ref={premiumKlineChartRef}
            baseAsset={baseAsset}
            triggerConfig={triggerConfig}
            dataType={chartDataType}
            interval={klineInterval}
            marketCodes={marketCodes}
            queryKey={queryKey}
            isKimpExchange={isKimpExchange}
            isTetherPriceView={isTetherPriceView}
          />
        </>
      );
    default:
      return <LinearProgress />;
  }
}

export default PremiumDataChartViewer;
