from datetime import datetime, timedelta
from rest_framework import exceptions, serializers

from lib.datetime import TZ_ASIA_SEOUL
from board.models import PostCategory, Post, Comment, PostLikes, PostViews
from users.models import User


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="uuid",
        write_only=True,
    )
    username = serializers.StringRelatedField()
    replies = serializers.SerializerMethodField()

    def get_replies(self, instance):
        if instance.replies:
            return CommentSerializer(instance.replies.all(), many=True).data
        else:
            return []

    class Meta:
        model = Comment
        fields = (
            "id",
            "user",
            "username",
            "date_created",
            "content",
            "post",
            "parent",
            "replies",
        )


class PostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCategory
        fields = ("id", "name", "code")


class PostSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="uuid",
        write_only=True,
    )
    username = serializers.StringRelatedField()
    category = serializers.SlugRelatedField(
        queryset=PostCategory.objects.all(), slug_field="code"
    )
    comments = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    viewed = serializers.SerializerMethodField()

    def get_comments(self, instance):
        return len(instance.comments.all())

    def get_likes(self, instance):
        return len(instance.likes.all())

    def get_views(self, instance):
        return len(instance.views.all())

    def get_liked(self, instance):
        return (
            "request" in self.context
            and hasattr(self.context["request"], "user")
            and isinstance(self.context["request"].user, User)
            and bool(
                self.context["request"].user.liked_posts.filter(post=instance).first()
            )
        )

    def get_viewed(self, instance):
        return (
            "request" in self.context
            and hasattr(self.context["request"], "user")
            and isinstance(self.context["request"].user, User)
            and PostViewsSerializer().has_user_viewed_post_today(
                post=instance, user=self.context["request"].user
            )
        )

    class Meta:
        model = Post
        fields = (
            "id",
            "user",
            "username",
            "title",
            "date_created",
            "category",
            "content",
            "comments",
            "likes",
            "views",
            "liked",
            "viewed",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "date_created": {"read_only": True},
        }


class PostLikesSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="uuid",
        write_only=True,
    )
    date_liked = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PostLikes
        fields = ("id", "user", "post", "date_liked")


class PostViewsSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="uuid",
        write_only=True,
    )
    date_viewed = serializers.DateTimeField(read_only=True)

    def has_user_viewed_post_today(self, post, user):
        today = datetime.now(tz=TZ_ASIA_SEOUL)

        try:
            PostViews.objects.get(
                post=post,
                user=user,
                date_viewed__gte=today.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
                date_viewed__lte=today.replace(
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=timedelta.max.microseconds,
                ),
            )
        except PostViews.DoesNotExist:
            return False

        return True

    def validate(self, attrs):
        if self.has_user_viewed_post_today(user=attrs["user"], post=attrs["post"]):
            raise exceptions.ValidationError(
                {"post": "User has already viewed Post today."}
            )
        return super().validate(attrs)

    class Meta:
        model = PostViews
        fields = ("id", "user", "post", "date_viewed")
