from decimal import Decimal
from django.db.models import Sum, Q

def get_user_withdrawable_balance(user):
    # Include only DEPOSIT types as positive contributions.
    # Subtract FEE and WITHDRAW.
    # Ignore coupon, commission, transfer, etc.

    net = user.deposit_history.filter(type__in=['DEPOSIT', 'FEE', 'WITHDRAW']).aggregate(total=Sum('change'))['total'] or Decimal('0')

    # Subtract pending/approved withdrawal requests that haven't been completed yet
    # (completed withdrawals are already reflected in deposit history as WITHDRAW type)
    from users.models import WithdrawalRequest
    pending_withdrawals = WithdrawalRequest.objects.filter(
        user=user,
        type=WithdrawalRequest.DEPOSIT,
        status__in=[WithdrawalRequest.PENDING, WithdrawalRequest.APPROVED],
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    net = net - pending_withdrawals

    net = max(net, Decimal('0'))
    return net

def get_user_withdrawable_commission(user):
    from referral.models import CommissionBalance
    from users.models import WithdrawalRequest

    # Read commission balance from CommissionBalance (via affiliate)
    try:
        commission_sum = CommissionBalance.objects.get(affiliate__user=user).balance
    except CommissionBalance.DoesNotExist:
        commission_sum = Decimal('0')

    # Subtract pending/approved commission withdrawal requests
    pending_commission_withdrawals = WithdrawalRequest.objects.filter(
        user=user,
        type=WithdrawalRequest.COMMISSION,
        status__in=[WithdrawalRequest.PENDING, WithdrawalRequest.APPROVED],
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    commission_sum = commission_sum - pending_commission_withdrawals

    return max(commission_sum, Decimal('0'))

def get_user_spent_fee(user):
    fee_sum = user.deposit_history.filter(type='FEE').aggregate(total=Sum('change'))['total'] or Decimal('0')
    return fee_sum