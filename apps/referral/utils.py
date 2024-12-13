from decimal import Decimal
from referral.constants import (
    PROFIT_TYPE_FEE,
    PROFIT_TYPE_COMMISSION,
)

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
    parent_comm_fraction = tier.parent_commission_rate if not affiliate.is_root else Decimal('0')

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
        "user": user,
        "commission_from": None,
        "change": -user_pays,  # user pays fee, so negative from user perspective
        "type": PROFIT_TYPE_FEE,
        "description": f"User trading fee after discount, original fee: {user_fee}, discount: {user_discount}",
        "trade_uuid": trade_uuid,
    })

    # If parent_earning > 0, record parent's commission
    if parent_earning > 0 and affiliate.parent_affiliate:
        parent_aff = affiliate.parent_affiliate
        records.append({
            "user": parent_aff.user,
            "commission_from": affiliate.user,
            "change": parent_earning,
            "type": PROFIT_TYPE_COMMISSION,
            "description": "Parent affiliate commission",
            "trade_uuid": trade_uuid,
        })

    # Record affiliate commission if any
    if affiliate_earning > 0:
        records.append({
            "user": affiliate.user,
            "commission_from": user,
            "change": affiliate_earning,
            "type": PROFIT_TYPE_COMMISSION,
            "description": "Affiliate commission",
            "trade_uuid": trade_uuid,
        })

    return {
        "trade_uuid": trade_uuid,
        "records": records
    }