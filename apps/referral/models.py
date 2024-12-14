from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError
from users.models import User
import uuid

class AffiliateTier(models.Model):
    """
    Defines the rules for an affiliate tier.
    - base_commission_rate: The rate of the user's discounted fee the affiliate can earn.
    - parent_commission_rate: The rate of the affiliate’s earned commission that must be passed up to the parent if the affiliate is a sub-affiliate.
    """
    name = models.CharField(max_length=150, unique=True)
    base_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="rate of discounted fee the affiliate can earn as commission."
    )
    parent_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="If sub-affiliate, rate of affiliate's commission to pass to parent."
    )
    
    required_total_commission = models.DecimalField(
        max_digits=8, decimal_places=0, default=0,
        help_text="total commission required to be earned by affiliate to be eligible for this tier"
    )

    def __str__(self):
        return self.name
    
class Affiliate(models.Model):
    """
    Represents an affiliate (either root or sub).
    - parent_affiliate: Null if root affiliate, else points to a root affiliate.
    - affiliate_code: A unique code identifying this affiliate in a hierarchy.
    - tier: Defines what tier this affiliate belongs to.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='affiliate')
    parent_affiliate = models.ForeignKey('self', null=True, blank=True, related_name='sub_affiliates', on_delete=models.SET_NULL)
    affiliate_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tier = models.ForeignKey(AffiliateTier, on_delete=models.CASCADE, related_name='affiliates')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.is_root:
            return f"Root Affiliate {self.user.username} (Tier: {self.tier.name})"
        else:
            return f"Sub-Affiliate {self.user.username} under {self.parent_affiliate.user.username} (Tier: {self.tier.name})"

    @property
    def is_root(self):
        return self.parent_affiliate is None
    
class ReferralCode(models.Model):
    """
    Codes created by affiliates for their referred users.
    Each referral code can define:
    - user_discount_rate: How much discount the user gets on fees.
    - self_commission_rate: Out of the allowed commission from the tier, how much this affiliate takes.
      For example, if tier gives 30% total, the affiliate might say "User gets 10% discount, I keep 80% from the base_commission".
      Actually, user discount is first applied to fee, and then from the discounted fee, affiliate gets their commission.
      self_commission_rate here represents how the affiliate splits their allowed commission pool. 
      
      This may need clarification: 
      Usually you'd store user discount and affiliate’s share separately:
        - user_discount_rate: discount on user fee
        - self_commission_portion: portion of the affiliate's allowed commission after paying parent.
    """
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='referral_codes')
    code = models.CharField(max_length=100, unique=True)
    user_discount_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.05,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Discount rate for the user signing up with this code."
    )
    self_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.95,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Out of the allowed affiliate commission, what rate affiliate keeps."
    )
    created_at = models.DateTimeField(default=timezone.now)
    
    def clean(self):
        # Automatically set self_commission_rate based on user_discount_rate
        self.self_commission_rate = Decimal('1') - self.user_discount_rate

        # Validate the sum
        total = self.user_discount_rate + self.self_commission_rate
        # Using quantize to avoid floating point issues, or just compare directly since Decimal is exact.
        if total != Decimal('1'):
            raise ValidationError(
                f"The sum of user_discount_rate and self_commission_rate must be exactly 1. "
                f"Currently: {self.user_discount_rate} + {self.self_commission_rate} = {total}"
            )

    def save(self, *args, **kwargs):
        # Call clean() before save to ensure fields are correct.
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ReferralCode {self.code} by {self.affiliate.user.username}"

class Referral(models.Model):
    """
    Represents a user who registered using a referral code.
    """
    referred_user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='referral'
    )
    referral_code = models.ForeignKey(ReferralCode, on_delete=models.CASCADE, related_name='referrals')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.referred_user.username} referred by {self.referral_code.code}"
    
class AffiliateRequest(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'PENDING'),
        (STATUS_APPROVED, 'APPROVED'),
        (STATUS_REJECTED, 'REJECTED'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='affiliate_requests')
    contact = models.CharField(null=True, blank=True, max_length=100, help_text="Contact details of the user")
    url = models.URLField(null=True, blank=True, help_text="URL of the user's website or social media profile")
    description = models.TextField(null=True, blank=True, help_text="Description of the user's platform and how they plan to promote us")
    parent_affiliate_code = models.CharField(null=True, blank=True, max_length=100, help_text="Code of the parent affiliate")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    authorized_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='authorized_affiliate_requests')
    requested_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(null=True, blank=True, help_text="Reason for approval/rejection")

    def __str__(self):
        return f"AffiliateRequest from {self.user} - Status: {self.status}"
    
