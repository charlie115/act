from decimal import Decimal

from users.models import DepositHistory

SERVICE_FEE_RATE = Decimal(0.5)

PROFIT_TYPE_NET_PROFIT_FROM_TRADE = "NET_PROFIT_FROM_TRADE"
PROFIT_TYPE_FEE = DepositHistory.FEE
PROFIT_TYPE_COMMISSION = DepositHistory.COMMISSION
