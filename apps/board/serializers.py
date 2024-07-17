from datetime import datetime, timedelta
from rest_framework import exceptions, serializers

from lib.datetime import DATE_TIME_TZ_FORMAT, TZ_ASIA_SEOUL
from board.models import PostCategory, Post, PostImage, Comment, PostLikes, PostViews
from users.models import User
from users.serializers import UserProfileSerializer


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="uuid",
        write_only=True,
    )
    replies = serializers.SerializerMethodField()
    user_profile = serializers.SerializerMethodField()

    def get_replies(self, instance):
        if instance.replies:
            return CommentSerializer(instance.replies.all(), many=True).data
        else:
            return []

    def get_user_profile(self, obj):
        return UserProfileSerializer(obj.user.profile).data

    class Meta:
        model = Comment
        fields = (
            "id",
            "user",
            "date_created",
            "content",
            "post",
            "parent",
            "replies",
            "user_profile",
        )


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
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
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
    liked = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()
    last_view = serializers.SerializerMethodField()
    user_profile = serializers.SerializerMethodField()

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

    def get_last_view(self, instance):
        latest_view = None

        if (
            "request" in self.context
            and hasattr(self.context["request"], "user")
            and isinstance(self.context["request"].user, User)
        ):
            latest_view = PostViewsSerializer().get_user_latest_view(
                post=instance,
                user=self.context["request"].user,
            )
            if latest_view:
                latest_view = latest_view.date_viewed.strftime(DATE_TIME_TZ_FORMAT)

        return latest_view

    def get_user_profile(self, obj):
        return UserProfileSerializer(obj.user.profile).data

    def to_representation(self, instance):
        images = PostImageSerializer(
            instance.post_images.all(),
            many=True,
            context={"request": self.context["request"]},
        ).data

        data = super().to_representation(instance)

        data["images"] = images

        return data

    class Meta:
        model = Post
        fields = (
            "id",
            "user",
            "title",
            "date_created",
            "category",
            "content",
            "images",
            "comments",
            "likes",
            "liked",
            "views",
            "last_view",
            "user_profile",
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

    def get_user_latest_view(self, post, user):
        return PostViews.objects.filter(
            post=post,
            user=user,
        ).latest("date_viewed")

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
