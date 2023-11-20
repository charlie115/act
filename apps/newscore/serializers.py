from rest_framework import serializers

from newscore.models import Announcement, News, Post


class NewsSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=300)
    subtitle = serializers.SerializerMethodField()
    content = serializers.CharField()
    datetime = serializers.DateTimeField()
    url = serializers.CharField(max_length=500)
    thumbnail = serializers.CharField(max_length=500)
    media = serializers.CharField(max_length=300)

    def get_subtitle(self, obj):
        return obj.content.split("\n")[0]

    class Meta:
        model = News
        fields = "__all__"


class AnnouncementSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=300)
    content = serializers.CharField()
    datetime = serializers.DateTimeField()
    url = serializers.CharField(max_length=500)
    category = serializers.CharField(max_length=100)
    exchange = serializers.CharField(max_length=300)

    class Meta:
        model = Announcement
        fields = "__all__"


class PostSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=100)
    content = serializers.CharField()
    extra_data = serializers.JSONField()
    datetime = serializers.DateTimeField()
    url = serializers.CharField(max_length=500)
    social_media = serializers.CharField(max_length=100)

    class Meta:
        model = Post
        fields = "__all__"
