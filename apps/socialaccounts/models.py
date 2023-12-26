from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken


class ProxySocialAccount(SocialAccount):
    def __str__(self):
        return f"{self.user} ({self.provider})"

    class Meta:
        proxy = True
        verbose_name = "Social Account"


class ProxySocialApp(SocialApp):
    def __str__(self):
        return f"{self.name} ({self.provider})"

    class Meta:
        proxy = True
        verbose_name = "Social App"


class ProxySocialToken(SocialToken):
    class Meta:
        proxy = True
        verbose_name = "Social Token"
