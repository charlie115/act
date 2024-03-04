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
from users.managers import UserManager
from socialaccounts.models import ProxySocialApp


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
        if self.username == "":
            email_username = list(self.email.split("@")[0])
            temp_username = "".join(random.sample(email_username, len(email_username)))
            self.username = f"@{temp_username}{datetime.now().microsecond}"

        super(User, self).save(*args, **kwargs)

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
    referral = models.CharField(max_length=150, blank=True, null=True)
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
    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"
    COMMISSION = "commission"
    FEE = "fee"
    TRANSFER = "transfer"
    COUPON = "coupon"
    DepositTypes = (
        (WITHDRAW, "Withdraw"),
        (DEPOSIT, "Deposit"),
        (COMMISSION, "Commission"),
        (FEE, "Fee"),
        (TRANSFER, "Transfer"),
        (COUPON, "Coupon"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deposit_history",
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    txid = models.TextField(blank=True, null=True)
    type = models.CharField(choices=DepositTypes)
    pending = models.BooleanField(default=False)
    registered_datetime = models.DateTimeField(default=now)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super(DepositHistory, self).save(*args, **kwargs)

        if hasattr(self.user, "deposit_balance"):
            self.user.deposit_balance.balance = self.balance
            self.user.deposit_balance.save()
        else:
            DepositBalance.objects.create(user=self.user, balance=self.balance)

    class Meta:
        verbose_name = "Deposit History"
        verbose_name_plural = "Deposit History"
