import React, { useMemo, useState } from 'react';
import {
  Box,
  CircularProgress,
  Container,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Table,
  TableHead,
  TableBody,
  TableCell,
  TableRow,
  TableContainer,
  Paper,
  Typography,
  TableSortLabel,
  Stack,
  TablePagination
} from '@mui/material';
import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';

import { useGetCommissionHistoryQuery, useGetSubAffiliatesQuery, useGetAffiliateTierQuery } from 'redux/api/drf/referral';

export default function CommissionHistory() {
  const { t } = useTranslation();
  const { user } = useSelector((state) => state.auth);
  const affiliateId = user?.affiliate?.id;

  const { data: commissionHistoryData, isLoading: historyLoading } = useGetCommissionHistoryQuery();
  const { data: subAffiliatesData = [], isLoading: subAffiliatesLoading } = useGetSubAffiliatesQuery(affiliateId, {
    skip: !affiliateId,
  });
  const { data: tierData, isLoading: tierLoading } = useGetAffiliateTierQuery();
  const userTier = tierData?.find((tier) => tier.id === user?.affiliate?.tier) || null;

  // Filter State
  const [filterAffiliateId, setFilterAffiliateId] = useState('all'); 
  // Sorting State with tri-state logic: none -> asc -> desc -> none
  const [orderBy, setOrderBy] = useState('created_at');
  const [order, setOrder] = useState('none'); // start with no sorting

  // Pagination State
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const handleSort = (field) => {
    if (orderBy === field) {
      // Cycle through: none -> asc -> desc -> none
      if (order === 'none') {
        setOrder('asc');
      } else if (order === 'asc') {
        setOrder('desc');
      } else if (order === 'desc') {
        setOrder('none');
      }
    } else {
      // New field, start with asc
      setOrderBy(field);
      setOrder('asc');
    }
  };

  const affiliateNameMap = useMemo(() => {
    const map = {};
    if (affiliateId) {
      map[affiliateId] = t('본인');
    }
    subAffiliatesData.forEach((sub) => {
      map[sub.id] = sub.user;
    });
    return map;
  }, [subAffiliatesData, affiliateId, t]);

  const affiliateTierMap = useMemo(() => {
    const map = {};
    // Add my tier
    if (affiliateId) {
      map[affiliateId] = userTier?.name || '-';
    }
    subAffiliatesData.forEach((sub) => {
      map[sub.id] = sub.tier;
    });
    return map;
  }, [subAffiliatesData]);

  const filteredHistory = useMemo(() => {
    if (!commissionHistoryData) return [];
    let filtered = commissionHistoryData;

    // Filter
    if (filterAffiliateId === 'self') {
      filtered = filtered.filter((h) => h.affiliate === affiliateId);
    } else if (filterAffiliateId !== 'all') {
      const subId = parseInt(filterAffiliateId, 10);
      filtered = filtered.filter((h) => h.affiliate === subId);
    }

    // Sort if order !== 'none'
    if (order !== 'none') {
      filtered = filtered.slice().sort((a, b) => {
        let cmp = 0;
        if (orderBy === 'created_at') {
          cmp = new Date(a.created_at) - new Date(b.created_at);
        } else if (orderBy === 'change') {
          cmp = parseFloat(a.change) - parseFloat(b.change);
        }
        return order === 'asc' ? cmp : -cmp;
      });
    }

    return filtered;
  }, [commissionHistoryData, filterAffiliateId, affiliateId, orderBy, order]);

  const totalCommission = useMemo(
    () => filteredHistory.reduce(
      (sum, h) => h.type === 'COMMISSION' ? sum + parseFloat(h.change) : sum,
      0
    ),
    [filteredHistory]
  );

  // Paginate
  const paginatedHistory = useMemo(
    () => filteredHistory.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage),
    [filteredHistory, page, rowsPerPage]
  );

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (historyLoading || subAffiliatesLoading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  // Determine the TableSortLabel direction
  const sortDirection = (column) =>
    orderBy === column && order !== 'none' ? order : 'asc';

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4, mb: 2 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
          <Typography variant="h4">{t('Commission History')}</Typography>
          <Box display="flex" alignItems="center" gap={2}>
            {/* Filter by affiliate */}
            <FormControl variant="outlined" size="small">
              <InputLabel>{t('Affiliate')}</InputLabel>
              <Select
                label={t('Affiliate')}
                value={filterAffiliateId}
                onChange={(e) => {
                  setFilterAffiliateId(e.target.value);
                  setPage(0); // reset to first page on filter change
                }}
              >
                <MenuItem value="all">{t('All')}</MenuItem>
                <MenuItem value="self">{t('본인')}</MenuItem>
                {subAffiliatesData.map((sub) => (
                  <MenuItem key={sub.id} value={String(sub.id)}>
                    {sub.user}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Stack>

        <Paper sx={{ mb: 2 }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t('Affiliate')}</TableCell>
                  <TableCell>{t('Tier')}</TableCell>
                  <TableCell>{t('Type')}</TableCell>
                  <TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={orderBy === 'change' && order !== 'none'}
                      direction={order !== 'none' ? order : 'asc'}
                      onClick={() => handleSort('change')}
                    >
                      {t('Change')}
                    </TableSortLabel>
                  </TableCell>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={orderBy === 'created_at' && order !== 'none'}
                      direction={order !== 'none' ? order : 'asc'}
                      onClick={() => handleSort('created_at')}
                    >
                      {t('Created At')}
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>{t('Service Type')}</TableCell>
                  <TableCell>{t('Trade UUID')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedHistory.length > 0 ? (
                  paginatedHistory.map((h) => (
                    <TableRow key={h.id}>
                      <TableCell>{affiliateNameMap[h.affiliate] || h.affiliate}</TableCell>
                      <TableCell>{affiliateTierMap[h.affiliate] || h.affiliate}</TableCell>
                      <TableCell>{h.type}</TableCell>
                      <TableCell>{h.change}</TableCell>
                      <TableCell>{new Date(h.created_at).toLocaleString()}</TableCell>
                      <TableCell>{h.service_type || '-'}</TableCell>
                      <TableCell>{h.trade_uuid || '-'}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      {t('No commission history found.')}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={filteredHistory.length}
            page={page}
            onPageChange={handleChangePage}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </Paper>

        <Box sx={{ textAlign: 'right' }}>
          <Typography variant="h6">
            {t('Total Earned Commission')}: {totalCommission.toFixed(8)}
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}