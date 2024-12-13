from decimal import Decimal

from users.models import DepositHistory

# PROFIT_TYPE_NET_PROFIT_FROM_TRADE = "NET_PROFIT_FROM_TRADE" # This is not needed. Since net profit is is their own wallets.
PROFIT_TYPE_FEE = DepositHistory.FEE
PROFIT_TYPE_COMMISSION = DepositHistory.COMMISSION
