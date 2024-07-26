from datetime import datetime, timedelta
from rest_framework import exceptions, serializers

from lib.datetime import DATE_TIME_TZ_FORMAT, TZ_ASIA_SEOUL
from board.models import (
    PostCategory,
    Post,
    PostImage,
    PostReactions,
    PostViews,
    Comment,
    CommentReactions,
)
from users.models import User
from users.serializers import UserProfileSerializer


class PostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCategory
        fields = ("id", "name", "code")


class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = PostImage
        fields = ["image", "date_uploaded"]


class PostSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        source="user",
        slug_field="uuid",
        write_only=True,
    )
    category = serializers.SlugRelatedField(
        queryset=PostCategory.objects.all(), slug_field="name"
    )
    images = serializers.ListField(
        default=[],
        write_only=True,
        child=serializers.ImageField(),
    )
    comments = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    author_profile = serializers.SerializerMethodField()
    user_view = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()

    def create(self, validated_data):
        images = validated_data.pop("images")

        post = super().create(validated_data)

        new_content = post.content

        for img in images:
            post_image = PostImage.objects.create(image=img, post=post)
            new_content = new_content.replace(
                f'img src="{img.name}"', f'img src="{post_image.image.url}"'
            )

        post.content = new_content
        post.save()

        return post

    def get_comments(self, obj):
        return len(obj.comments.all())

    def get_likes(self, obj):
        return len(obj.reactions.filter(reaction=PostReactions.LIKE))

    def get_dislikes(self, obj):
        return len(obj.reactions.filter(reaction=PostReactions.DISLIKE))

    def get_views(self, obj):
        return len(obj.views.all())

    def get_images(self, obj):
        return PostImageSerializer(
            obj.post_images.all(),
            many=True,
            context={"request": self.context["request"]},
        ).data

    def get_user_reaction(self, obj):
        if (
            "request" in self.context
            and hasattr(self.context["request"], "user")
            and isinstance(self.context["request"].user, User)
            and self.context["request"].user.post_reactions.filter(post=obj).first()
        ):
            return PostReactionsSerializer(
                self.context["request"].user.post_reactions.filter(post=obj).first()
            ).data
        return None

    def get_user_view(self, obj):
        latest_view = None

        if (
            "request" in self.context
            and hasattr(self.context["request"], "user")
            and isinstance(self.context["request"].user, User)
        ):
            latest_view = PostViewsSerializer().get_user_latest_view(
                post=obj,
                user=self.context["request"].user,
            )
            if latest_view:
                latest_view = latest_view.date_viewed.strftime(DATE_TIME_TZ_FORMAT)

        return latest_view

    def get_author_profile(self, obj):
        return UserProfileSerializer(obj.user.profile).data

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "title",
            "category",
            "content",
            "comments",
            "likes",
            "dislikes",
            "views",
            "images",
            "date_created",
            "author_profile",
            "user_reaction",
            "user_view",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "date_created": {"read_only": True},
        }


class PostReactionsSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="uuid",
        write_only=True,
    )
    date_updated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PostReactions
        fields = ("id", "user", "post", "reaction", "date_updated")


class PostViewsSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="uuid",
        write_only=True,
    )
    date_viewed = serializers.DateTimeField(read_only=True)

    def get_user_latest_view(self, post, user):
        return (
            PostViews.objects.filter(
                post=post,
                user=user,
            )
            .order_by("date_viewed")
            .last()
        )

    def validate(self, attrs):
        latest_view = self.get_user_latest_view(user=attrs["user"], post=attrs["post"])

        today = datetime.now(tz=TZ_ASIA_SEOUL)
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=timedelta.max.microseconds,
        )
        if latest_view and today_start <= latest_view.date_viewed <= today_end:
            raise exceptions.ValidationError(
                {"post": "User has already viewed Post today."}
            )
        return super().validate(attrs)

    class Meta:
        model = PostViews
        fields = ("id", "user", "post", "date_viewed")


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        source="user",
        slug_field="uuid",
        write_only=True,
    )
    replies = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    author_profile = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()

    def get_replies(self, obj):
        if obj.replies:
            return CommentSerializer(obj.replies.all(), many=True).data
        else:
            return []

    def get_likes(self, obj):
        return len(obj.reactions.filter(reaction=CommentReactions.LIKE))

    def get_dislikes(self, obj):
        return len(obj.reactions.filter(reaction=CommentReactions.DISLIKE))

    def get_user_reaction(self, obj):
        if (
            "request" in self.context
            and hasattr(self.context["request"], "user")
            and isinstance(self.context["request"].user, User)
            and self.context["request"]
            .user.comment_reactions.filter(comment=obj)
            .first()
        ):
            return CommentReactionsSerializer(
                self.context["request"]
                .user.comment_reactions.filter(comment=obj)
                .first()
            ).data
        return None

    def get_author_profile(self, obj):
        return UserProfileSerializer(obj.user.profile).data

    class Meta:
        model = Comment
        fields = (
            "id",
            "author",
            "content",
            "post",
            "parent",
            "replies",
            "likes",
            "dislikes",
            "date_created",
            "author_profile",
            "user_reaction",
        )


class CommentReactionsSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="uuid",
        write_only=True,
    )
    date_updated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CommentReactions
        fields = ("id", "user", "comment", "reaction", "date_updated")
