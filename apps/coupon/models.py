from django.db import models
from django.utils import timezone
from django.conf import settings
import string
import random
from users.models import User

def short_code_generator(length=12):
    """
    Generates a random short code of given length from uppercase letters and digits.
    Adjust as needed for uniqueness checks (e.g., loop until unique).
    """
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True, default=short_code_generator)
    name = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def is_expired(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    def __str__(self):
        return f"Coupon {self.name} - {'Active' if self.is_active else 'Inactive'}"


class CouponRedemption(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_redemptions')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='redemptions')
    redeemed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'coupon')

    def __str__(self):
        return f"{self.user} redeemed {self.coupon.code} at {self.redeemed_at}"