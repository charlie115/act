import random
import uuid

from datetime import datetime
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from users.managers import UserManager


class User(AbstractUser):
    VISITOR = "visitor"
    USER = "user"
    INTERNAL_USER = "internal"
    UserRoles = (
        (VISITOR, "Visitor"),
        (USER, "User"),
        (INTERNAL_USER, "Internal"),
    )

    email = models.EmailField(_("email address"), unique=True)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100, unique=True, blank=True)
    telegram_id = models.CharField(max_length=150, blank=True, null=True)
    last_username_change = models.DateTimeField(default=now)
    role = models.CharField(default=VISITOR, choices=UserRoles)

    managers = models.ManyToManyField(
        "self",
        through="UserManagers",
        symmetrical=False,
        related_name="managed_users",
        blank=True,
    )

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
        verbose_name_plural = "Users"


class UserManagers(models.Model):
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="managed_user",
        db_column="manager_user_id",
    )
    managed_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="manager",
        db_column="managed_user_id",
    )

    def __str__(self):
        return f"{self.manager.username} manages {self.managed_user.username}"

    class Meta:
        verbose_name_plural = "User managers"


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
        verbose_name_plural = "User profiles"


class UserFavoriteSymbols(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_symbols",
    )
    market_name_1 = models.CharField(max_length=150)
    market_name_2 = models.CharField(max_length=150)
    base_symbol = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.user.username} ({self.base_symbol})"

    class Meta:
        verbose_name_plural = "User favorite symbols"
