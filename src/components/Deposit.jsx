import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';

import AddCardIcon from '@mui/icons-material/AddCard';
import HistoryIcon from '@mui/icons-material/History';
import MoneyIcon from '@mui/icons-material/Money';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';
import _i18n from 'configs/i18n';

import DepositHistory from 'components/DepositHistory';
import DropdownMenu from 'components/DropdownMenu';
import TopUpDeposit from 'components/TopUpDeposit';
import WithdrawDeposit from 'components/WithdrawDeposit';

const COMPONENTS = [
  {
    getLabel: () => _i18n.t('Top-up Deposit'),
    value: 'topUpDeposit',
    icon: AddCardIcon,
    component: TopUpDeposit,
  },
  {
    getLabel: () => _i18n.t('Deposit History'),
    value: 'depositHistory',
    icon: HistoryIcon,
    component: DepositHistory,
  },
  {
    getLabel: () => _i18n.t('Withdraw Deposit'),
    value: 'withdrawDeposit',
    icon: MoneyIcon,
    component: WithdrawDeposit,
  },
];

export default function Deposit({ marketCodeCombination }) {
  const { i18n } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [componentList, setComponentList] = useState([]);
  const [selectedComponent, setSelectedComponent] = useState();

  useEffect(() => {
    const components = COMPONENTS.map((comp) => ({
      label: comp.getLabel(),
      value: comp.value,
      icon: <comp.icon />,
      component: comp.component,
      disabled: comp.value === 'withdrawDeposit',
    }));
    setComponentList(components);
    if (!selectedComponent) setSelectedComponent(components[0]);
  }, [selectedComponent, i18n.language]);

  const { tradeConfigUuid } = marketCodeCombination;

  return (
    <Box sx={{ p: 2 }}>
      <DropdownMenu
        value={selectedComponent}
        options={componentList}
        onSelectItem={setSelectedComponent}
        buttonStyle={{
          justifyContent: 'flex-start',
          minWidth: isMobile ? 190 : 240,
        }}
      />
      {selectedComponent && (
        <selectedComponent.component tradeConfigUuid={tradeConfigUuid} />
      )}
      {/* <TopUpDeposit tradeConfigUuid={tradeConfigUuid} /> */}
    </Box>
  );
}
