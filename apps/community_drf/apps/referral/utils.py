from decimal import Decimal
from referral.constants import (
    PROFIT_TYPE_FEE,
)
from referral.models import CommissionHistory

def calculate_fee_and_commission_for_trade(user, user_fee, referral, trade_uuid=None):
    """
    Calculate how the fee and commission are distributed using the logic you specified:
    
    Steps:
    1. Calculate base commission pool (user_fee * base_commission_rate).
    2. If sub-affiliate, pay parent affiliate from that pool.
    3. With the remainder, apply the user discount and affiliate commission split:
       remainder_for_affiliate * user_discount_rate = user_discount
       remainder_for_affiliate * self_commission_rate = affiliate_earning
    4. The final fee user pays is original_fee - user_discount.
    
    Returns a dict:
    {
        "trade_uuid": trade_uuid,
        "data_type": "deposit_history", # or "commission_history"
        "records": [
            {
                "user": <User instance>,
                "commission_from": <User instance or None>,
                "change": <Decimal>,
                "type": <str>,
                "description": <str>,
                "trade_uuid": trade_uuid
            },
            ...
        ]
    }
    """
    rcode = referral.referral_code
    affiliate = rcode.affiliate
    tier = affiliate.tier

    base_commission_fraction = tier.base_commission_rate
    # check whether parent_affiliate exists
    parent_affiliate = affiliate.parent_affiliate
    if parent_affiliate:
        parent_affiliate_tier = parent_affiliate.tier
        parent_comm_fraction = parent_affiliate_tier.parent_commission_rate
    else:
        parent_comm_fraction = Decimal('0')

    user_discount_rate = rcode.user_discount_rate
    self_commission_rate = rcode.self_commission_rate

    # 1. Base commission pool
    base_commission_pool = user_fee * base_commission_fraction

    # 2. Pay parent if sub-affiliate
    parent_earning = base_commission_pool * parent_comm_fraction
    remainder_for_affiliate = base_commission_pool - parent_earning

    # 3. Calculate user discount and affiliate commission from the remainder
    user_discount = remainder_for_affiliate * user_discount_rate
    affiliate_earning = remainder_for_affiliate * self_commission_rate

    # 4. User pays final fee (original_fee - user_discount)
    user_pays = user_fee - user_discount

    records = []

    # Record: user paying fee
    records.append({
        "data_type": "deposit_history",
        "user": user,
        "change": -user_pays,  # user pays fee, so negative from user perspective
        "referral_discount": user_discount,
        "type": PROFIT_TYPE_FEE,
        "description": f"User trading fee after discount, original fee: {float(user_fee)}, discount: {float(user_discount)}",
        "trade_uuid": trade_uuid,
    })

    # If parent_earning > 0, record parent's commission
    if parent_earning > 0 and affiliate.parent_affiliate:
        parent_aff = affiliate.parent_affiliate
        records.append({
            "data_type": "commission_history",
            "affiliate": parent_aff,
            "child_affiliate": affiliate,
            "user_who_paid": user,
            "service_type": None,
            "type": CommissionHistory.COMMISSION,
            "trade_uuid": trade_uuid,
            "change": parent_earning,            
        })

    # Record affiliate commission if any
    if affiliate_earning > 0:
        records.append({
            "data_type": "commission_history",
            "affiliate": affiliate,
            "child_affiliate": None,
            "user_who_paid": user,
            "service_type": None,
            "type": CommissionHistory.COMMISSION,
            "trade_uuid": trade_uuid,
            "change": affiliate_earning,
        })

    return {
        "trade_uuid": trade_uuid,
        "records": records
    }
    
def get_all_affiliate_ids(affiliate):
    """
    Recursively get all affiliate ids including the affiliate itself and its descendants.
    Uses a visited set to prevent infinite loops from data cycles.
    """
    visited = set()
    ids = []
    stack = [affiliate]
    while stack:
        current = stack.pop()
        if current.id in visited:
            continue
        visited.add(current.id)
        ids.append(current.id)
        for sub in current.sub_affiliates.all():
            if sub.id not in visited:
                stack.append(sub)
    return ids