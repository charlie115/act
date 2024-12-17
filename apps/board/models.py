from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class Post(models.Model):
    ANNOUNCEMENT = "Announcement"
    FREEWRITING = "Freewriting"
    QUESTION = "Question"
    INVESTMENT_STRATEGY = "Investment Strategy"
    INFORMATION = "Information"
    USER_GUIDE = "User Guide"
    Categories = (
        (ANNOUNCEMENT, ANNOUNCEMENT),
        (FREEWRITING, FREEWRITING),
        (QUESTION, QUESTION),
        (INVESTMENT_STRATEGY, INVESTMENT_STRATEGY),
        (INFORMATION, INFORMATION),
        (USER_GUIDE, USER_GUIDE),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="board_authored_posts",
    )
    title = models.CharField(max_length=500)
    category = models.CharField(choices=Categories)
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
        related_name="board_authored_comments",
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
        related_name="board_post_reactions",
    )
    reaction = models.CharField(choices=Reactions, default=LIKE)
    date_updated = models.DateTimeField(_("date updated"), default=now)

    def save(self, *args, **kwargs):
        super(PostReactions, self).save(*args, **kwargs)

        if self.reaction == PostReactions.LIKE:
            UserLevels().update_level(
                user=self.post.user,
                points=UserLevels.LIKE_POINTS,
            )

        if self.reaction == PostReactions.DISLIKE:
            UserLevels().update_level(
                user=self.post.user,
                points=UserLevels.DISLIKE_POINTS,
            )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"],
                name="unique__post_reactions__post__user",
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
        related_name="board_viewed_posts",
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
        related_name="board_comment_reactions",
    )
    reaction = models.CharField(choices=Reactions, default=LIKE)
    date_updated = models.DateTimeField(_("date updated"), default=now)

    def save(self, *args, **kwargs):
        super(CommentReactions, self).save(*args, **kwargs)

        if self.reaction == CommentReactions.LIKE:
            UserLevels().update_level(
                user=self.comment.user,
                points=UserLevels.LIKE_POINTS,
            )

        if self.reaction == CommentReactions.DISLIKE:
            UserLevels().update_level(
                user=self.comment.user,
                points=UserLevels.DISLIKE_POINTS,
            )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "user"],
                name="unique__comment_reactions__comment__user",
            )
        ]
        verbose_name_plural = "Comment Reactions"


class Level(models.Model):
    level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
    )
    points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(3000)],
    )

    def __str__(self):
        return f"Level {self.level}"


class UserLevels(models.Model):
    LOGIN_POINTS = 5
    LIKE_POINTS = 1
    DISLIKE_POINTS = -1

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_level",
    )
    community_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
    )
    total_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(3000)],
    )
    last_updated_datetime = models.DateTimeField(
        default=now
    )  # just following fee level naming...

    def update_level(self, user, points=1):
        # Get or create User community_level
        try:
            user_community_level = UserLevels.objects.get(user=user)
        except UserLevels.DoesNotExist:
            user_community_level = UserLevels.objects.create(user=user)

        user_community_level.total_points += points

        # Get User's new level based on the updated points
        if user_community_level.total_points < 0:
            community_level = Level.objects.get(points__lte=0)
        else:
            community_level = Level.objects.filter(
                points__lte=user_community_level.total_points
            ).last()

        # Set User's new community_level
        user_community_level.community_level = community_level.level
        user_community_level.last_updated_datetime = now()
        user_community_level.save()

    def __str__(self):
        return (
            f"{self.user.email}: level {self.community_level} ({self.total_points} pts)"
        )

    class Meta:
        verbose_name_plural = "Levels"
