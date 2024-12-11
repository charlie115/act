from decimal import Decimal
from django.db.models import Sum, Q

def get_user_withdrawable_balance(user):
    # Example logic:
    # Include only DEPOSIT types as positive contributions.
    # Subtract FEE.
    # Ignore coupon, commission, transfer, etc.
    
    deposit_sum = user.deposit_history.filter(type='DEPOSIT').aggregate(total=Sum('change'))['total'] or Decimal('0')
    commission_sum = user.deposit_history.filter(type='COMMISSION').aggregate(total=Sum('change'))['total'] or Decimal('0')
    fee_sum = user.deposit_history.filter(type='FEE').aggregate(total=Sum('change'))['total'] or Decimal('0')
    
    # If fee is represented as a negative change already, adjust accordingly.
    # If the fee is a negative change (e.g. -0.5), summing it would already reduce deposit_sum.
    # If fee is stored as positive numbers that represent a deduction, then subtract them manually.
    
    # Let's assume fee entries are negative changes in deposit history (like -0.5).
    # If fees are stored as negative `change`, deposit_sum + fee_sum would already represent net deposit - fee.
    # If fee entries are positive changes representing a deduction, do:
    # net = deposit_sum - fee_sum
    # For now, let's assume fee entries are negative amounts, so just sum them together:
    net = user.deposit_history.filter(type__in=['DEPOSIT', 'FEE']).aggregate(total=Sum('change'))['total'] or Decimal('0')
    # If coupons or commissions are credited to user but not withdrawable, do not include them in net calculation.
    # If they are in deposit balance but should not be withdrawable, you must exclude them from net.

    # The net above might be your withdrawable. 
    # Adjust logic based on your actual deposit/fee structure.
    return net

def get_user_withdrawable_commission(user):
    commission_sum = user.deposit_history.filter(type='COMMISSION').aggregate(total=Sum('change'))['total'] or Decimal('0')
    return commission_sum

def get_user_spent_fee(user):
    fee_sum = user.deposit_history.filter(type='FEE').aggregate(total=Sum('change'))['total'] or Decimal('0')
    return fee_sum