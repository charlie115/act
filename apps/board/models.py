from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class PostCategory(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Post Category"
        verbose_name_plural = "Post Categories"


class Post(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_posts",
    )
    title = models.CharField(max_length=500)
    category = models.ForeignKey(
        PostCategory,
        on_delete=models.CASCADE,
        related_name="category_posts",
    )
    content = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(_("date created"), default=now)

    def __str__(self):
        return f"Post #{self.pk}"


class PostImage(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="post_images",
    )
    image = models.ImageField(upload_to="posts/images/")
    date_uploaded = models.DateTimeField(_("date uploaded"), default=now)


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_comments",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    content = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(_("date created"), default=now)

    def __str__(self):
        return f"Comment #{self.pk}"


class PostReactions(models.Model):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"
    Reactions = (
        (LIKE, LIKE),
        (DISLIKE, DISLIKE),
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_reactions",
    )
    reaction = models.CharField(choices=Reactions, default=LIKE)
    date_updated = models.DateTimeField(_("date updated"), default=now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"],
                name="unique_reactions__post__user",
            )
        ]
        verbose_name_plural = "Post Reactions"


class PostViews(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="views",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="viewed_posts",
    )
    date_viewed = models.DateTimeField(_("date viewed"), default=now)

    class Meta:
        verbose_name_plural = "Post Views"


class CommentReactions(models.Model):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"
    Reactions = (
        (LIKE, LIKE),
        (DISLIKE, DISLIKE),
    )

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_reactions",
    )
    reaction = models.CharField(choices=Reactions, default=LIKE)
    date_updated = models.DateTimeField(_("date updated"), default=now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "user"],
                name="unique_reactions__comment__user",
            )
        ]
        verbose_name_plural = "Comment Reactions"
