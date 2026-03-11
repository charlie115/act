import random
import uuid

from datetime import datetime
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from api.models import Permission
from fee.models import UserFeeLevel
from socialaccounts.models import ProxySocialApp
from users.managers import UserManager

class UserRole(models.Model):
    """This table stores User.Roles just for API permission purposes"""

    ADMIN = "ADMIN"
    INTERNAL_USER = "INTERNAL"
    MANAGER = "MANAGER"
    AFFILIATE = "AFFILIATE"
    USER = "USER"
    VISITOR = "VISITOR"
    Roles = (
        (ADMIN, ADMIN),
        (INTERNAL_USER, INTERNAL_USER),
        (MANAGER, MANAGER),
        (AFFILIATE, AFFILIATE),
        (USER, USER),
        (VISITOR, VISITOR),
    )

    name = models.CharField(
        primary_key=True,
        default=VISITOR,
        choices=Roles,
    )
    api_permissions = models.ManyToManyField(
        Permission,
        verbose_name="API Permissions",
        blank=True,
        null=True,
        help_text="<em>API permissions for <b>VISITORS</b> and <b>USERS</b> are not customizable.</em><br>",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "User Role"


class User(AbstractUser):
    email = models.EmailField(
        _("email address"),
        unique=True,
    )
    uuid = models.UUIDField(
        _("UUID"),
        primary_key=False,
        default=uuid.uuid4,
        editable=False,
    )
    username = models.CharField(_("username"), max_length=100, unique=True, blank=True)
    last_username_change = models.DateTimeField(default=now)
    role = models.ForeignKey(
        UserRole,
        default=UserRole.VISITOR,
        on_delete=models.PROTECT,
        related_name="users",
    )
    telegram_chat_id = models.CharField(max_length=150, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["password"]

    def save(self, *args, **kwargs):
        pk = self.pk

        if self.username == "":
            email_username = list(self.email.split("@")[0])
            temp_username = "".join(random.sample(email_username, len(email_username)))
            self.username = f"@{temp_username}{datetime.now().microsecond}"

        super(User, self).save(*args, **kwargs)

        if pk is None:
            DepositBalance.objects.create(user=self)
            UserFeeLevel.objects.create(user=self, total_paid_fee=0)

    def __str__(self):
        return self.email

    def has_perms(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class UserSocialApps(models.Model):
    socialapp = models.ForeignKey(
        ProxySocialApp,
        on_delete=models.RESTRICT,
        related_name="users",
        verbose_name="social app",
        help_text="The Telegram bot to allocate to the user.<br>"
        "<em>The social apps available currently are telegram bots.<br>"
        "Google is also available, but is used for login.</em>",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="socialapps",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["socialapp", "user"],
                name="unique__socialapp__user",
            )
        ]
        verbose_name = "User Social App"


class UserManagement(models.Model):
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="managed_users",
        db_column="manager_user_id",
    )
    managed_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="managers",
        db_column="managed_user_id",
    )

    def __str__(self):
        return f"{self.manager.email} manages {self.managed_user.email}"

    class Meta:
        verbose_name = "User Management"
        verbose_name_plural = "User Management"


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    level = models.IntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    points = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    def __str__(self):
        return self.user.__str__()

    class Meta:
        verbose_name = "User Profile"


class UserAuthLog(models.Model):
    """Logs everytime a user uses authentication.

    Currently used for board level purposes where we track when a user logs in for the day.
    But model might be useful in the future so I'll just use endpoint column for future purposes.

    Naming followed from django_admin_log table.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        related_name="auth_logs",
    )
    endpoint = models.CharField(max_length=50)
    date_logged = models.DateTimeField(default=now)


class UserFavoriteAssets(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_assets",
    )
    base_asset = models.CharField(max_length=10)
    market_codes = ArrayField(models.CharField(max_length=150))

    def __str__(self):
        return f"{self.user.username} ({self.base_asset})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "market_codes", "base_asset"],
                name="unique__user__base_asset__market_codes",
            )
        ]
        verbose_name = "User Favorite Assets"
        verbose_name_plural = "User Favorite Assets"


class UserBlocklist(models.Model):
    target_username = models.CharField(_("username"), max_length=100)
    target_ip = models.CharField(max_length=200)
    datetime = models.DateTimeField(default=now)

    def __str__(self):
        return self.target_username

    class Meta:
        verbose_name = "User Blocklist"
        verbose_name_plural = "User Blocklist"


class DepositBalance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deposit_balance",
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_update = models.DateTimeField(default=now)

    def save(self, *args, **kwargs):
        self.last_update = datetime.now()
        super(DepositBalance, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Deposit Balance"


class DepositHistory(models.Model):
    WITHDRAW = "WITHDRAW"
    DEPOSIT = "DEPOSIT"
    FEE = "FEE"
    TRANSFER = "TRANSFER"
    COUPON = "COUPON"
    DepositTypes = (
        (WITHDRAW, WITHDRAW),
        (DEPOSIT, DEPOSIT),
        (FEE, FEE),
        (TRANSFER, TRANSFER),
        (COUPON, COUPON),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deposit_history",
    )
    change = models.DecimalField(max_digits=10, decimal_places=2)
    referral_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0) # For Fee discount from referral system
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    trade_uuid = models.UUIDField(blank=True, null=True)
    txid = models.TextField(blank=True, null=True)
    type = models.CharField(choices=DepositTypes)
    coupon = models.ForeignKey(
        "coupon.Coupon",
        on_delete=models.SET_NULL,
        related_name="deposit_history",
        blank=True,
        null=True,
    )
    pending = models.BooleanField(default=False)
    registered_datetime = models.DateTimeField(default=now)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        try:
            deposit_balance = self.user.deposit_balance
        except User.deposit_balance.RelatedObjectDoesNotExist:
            deposit_balance = DepositBalance(user=self.user)

        self.balance = deposit_balance.balance + self.change
        super(DepositHistory, self).save(*args, **kwargs)

        deposit_balance.balance = self.balance
        deposit_balance.save()

    class Meta:
        verbose_name = "Deposit History"
        verbose_name_plural = "Deposit History"

class WithdrawalRequest(models.Model):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    
    DEPOSIT = "DEPOSIT"
    COMMISSION = "COMMISSION"
    
    STATUSES = (
        (PENDING, PENDING),
        (APPROVED, APPROVED),
        (REJECTED, REJECTED),
        (COMPLETED, COMPLETED),
    )
    
    TYPES = (
        (DEPOSIT, DEPOSIT),
        (COMMISSION, COMMISSION),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='withdrawal_requests'
    )
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='authorized_withdrawal_requests',
        blank=True,
        null=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.CharField(max_length=255)  # USDT TRC20 Address
    type = models.CharField(choices=TYPES, max_length=20)
    status = models.CharField(choices=STATUSES, default=PENDING, max_length=20)
    requested_datetime = models.DateTimeField(default=now)
    approved_datetime = models.DateTimeField(blank=True, null=True)
    completed_datetime = models.DateTimeField(blank=True, null=True)
    txid = models.CharField(max_length=255, blank=True, null=True)  # Transaction ID once executed
    remark = models.TextField(blank=True, null=True)  # For admin notes or user notes
    
    def __str__(self):
        return f"WithdrawalRequest({self.user.email}, {self.amount}, {self.status})"
    
    class Meta:
        verbose_name = "Withdrawal Request"
        verbose_name_plural = "Withdrawal Requests"