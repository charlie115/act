from datetime import datetime, timedelta
from django.utils.html import strip_tags
from rest_framework import exceptions, serializers

from lib.datetime import DATE_TIME_TZ_FORMAT, TZ_ASIA_SEOUL
from board.models import (
    Post,
    PostImage,
    PostReactions,
    PostViews,
    Comment,
    CommentReactions,
)
from users.models import User
from users.serializers import UserProfileSerializer


class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = PostImage
        fields = ["image", "date_uploaded"]


class PostSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        source="user",
        slug_field="uuid",
        read_only=True,
    )
    category = serializers.ChoiceField(choices=Post.Categories)
    image = serializers.ListField(
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

    def validate_content(self, value):
        """Strip HTML tags to prevent XSS attacks."""
        if value:
            return strip_tags(value)
        return value

    def validate_title(self, value):
        """Strip HTML tags to prevent XSS attacks."""
        if value:
            return strip_tags(value)
        return value

    def create(self, validated_data):
        images = validated_data.pop("image")

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
        return obj.comments.count()

    def get_likes(self, obj):
        return obj.reactions.filter(reaction=PostReactions.LIKE).count()

    def get_dislikes(self, obj):
        return obj.reactions.filter(reaction=PostReactions.DISLIKE).count()

    def get_views(self, obj):
        return obj.views.count()

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
        ):
            reaction = (
                self.context["request"]
                .user.board_post_reactions.filter(post=obj)
                .first()
            )
            if reaction:
                return PostReactionsSerializer(reaction).data
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
            "image",
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
        slug_field="uuid",
        read_only=True,
    )
    date_updated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PostReactions
        fields = ("id", "user", "post", "reaction", "date_updated")


class PostViewsSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field="uuid",
        read_only=True,
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
        user = self.context["request"].user
        latest_view = self.get_user_latest_view(user=user, post=attrs["post"])

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
        source="user",
        slug_field="uuid",
        read_only=True,
    )
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    author_profile = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()

    def validate_content(self, value):
        """Strip HTML tags to prevent XSS attacks."""
        if value:
            return strip_tags(value)
        return value

    def get_fields(self):
        fields = super(CommentSerializer, self).get_fields()
        fields["replies"] = CommentSerializer(many=True, read_only=True)
        return fields

    def get_likes(self, obj):
        return obj.reactions.filter(reaction=CommentReactions.LIKE).count()

    def get_dislikes(self, obj):
        return obj.reactions.filter(reaction=CommentReactions.DISLIKE).count()

    def get_user_reaction(self, obj):
        if (
            "request" in self.context
            and hasattr(self.context["request"], "user")
            and isinstance(self.context["request"].user, User)
        ):
            reaction = (
                self.context["request"]
                .user.board_comment_reactions.filter(comment=obj)
                .first()
            )
            if reaction:
                return CommentReactionsSerializer(reaction).data
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
        slug_field="uuid",
        read_only=True,
    )
    date_updated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CommentReactions
        fields = ("id", "user", "comment", "reaction", "date_updated")
