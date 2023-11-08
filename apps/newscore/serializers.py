from rest_framework import serializers

from newscore.models import News


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
