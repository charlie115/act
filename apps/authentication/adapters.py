from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter


class CustomGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        login = super().complete_login(request, app, token, **kwargs)
        login.user.username = login.user.email

        return login
