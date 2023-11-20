from django.db import models


class News(models.Model):
    title = models.CharField(max_length=300)
    content = models.TextField()
    datetime = models.DateTimeField()
    url = models.CharField(max_length=500)
    thumbnail = models.CharField(max_length=500)
    media = models.CharField(max_length=300)

    class Meta:
        db_table = "news"
        managed = False


class Announcement(models.Model):
    title = models.CharField(max_length=300)
    content = models.TextField()
    datetime = models.DateTimeField()
    url = models.CharField(max_length=500)
    category = models.CharField(max_length=100)
    exchange = models.CharField(max_length=300)

    class Meta:
        db_table = "announcements"
        managed = False


class Post(models.Model):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    content = models.TextField()
    extra_data = models.JSONField()
    datetime = models.DateTimeField()
    url = models.CharField(max_length=500)
    social_media = models.CharField(max_length=100)

    class Meta:
        db_table = "posts"
        managed = False
