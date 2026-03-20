from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from unfold.admin import ModelAdmin, StackedInline, TabularInline

from board.models import (
    Post,
    PostImage,
    PostReactions,
    Comment,
    Level,
    UserLevels,
)


class LevelAdmin(ModelAdmin):
    list_display = ["id", "level", "points"]
    search_fields = ["level", "points"]
    ordering = ["level"]
    verbose_name_plural = "Levels"


class UserLevelsAdmin(ModelAdmin):
    list_display = [
        "user",
        "community_level",
        "total_points",
        "last_updated_datetime",
    ]
    search_fields = ["user__email", "user__username", "total_points"]
    list_filter = ["community_level"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CommentsInline(TabularInline):
    model = Comment
    readonly_fields = [
        "get_id",
        "get_replies",
        "get_likes",
        "get_dislikes",
        "date_created",
    ]
    fields = [
        "get_id",
        "user",
        "content",
        "get_replies",
        "get_likes",
        "get_dislikes",
        "date_created",
    ]
    show_change_link = True
    extra = 0

    def get_id(self, obj):
        return obj.id

    get_id.short_description = "ID"
    get_id.allow_tags = True

    @admin.display(description="Replies")
    def get_replies(self, obj):
        return obj.replies.count()

    @admin.display(description="👍")
    def get_likes(self, obj):
        return obj.reactions.filter(reaction=PostReactions.LIKE).count()

    @admin.display(description="👎")
    def get_dislikes(self, obj):
        return obj.reactions.filter(reaction=PostReactions.DISLIKE).count()

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(parent__isnull=True)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class RepliesInline(CommentsInline):
    verbose_name = "Reply"
    verbose_name_plural = "Replies"

    def get_queryset(self, request):
        queryset = super(CommentsInline, self).get_queryset(request)
        return queryset.filter(parent__isnull=False)


class ImagesInline(StackedInline):
    model = PostImage
    fields = ["date_uploaded", "post", "get_thumbnail"]
    readonly_fields = ["date_uploaded", "get_thumbnail"]
    classes = ("collapse",)
    verbose_name = "Image"
    extra = 0

    def get_thumbnail(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="100px" height="100px"/>'
            )

    get_thumbnail.short_description = "Thumbnail"
    get_thumbnail.allow_tags = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class PostAdmin(ModelAdmin):
    list_display = [
        "id",
        "title",
        "show_user_link",
        "category",
        "get_comments",
        "get_likes",
        "get_dislikes",
        "get_views",
        "date_created",
    ]
    list_display_links = [
        "id",
        "title",
    ]
    list_filter = [
        "category",
    ]
    search_fields = [
        "id",
        "title",
        "user__uuid",
        "user__email",
        "user__username",
    ]
    ordering = ["id"]
    inlines = [
        ImagesInline,
        CommentsInline,
    ]

    @admin.display(description="User")
    def show_user_link(self, obj):
        url = reverse("admin:users_user_change", args=(obj.user.pk,))
        return format_html(f"<a href='{url}'>{obj.user}</a>")

    @admin.display(description="Comments")
    def get_comments(self, obj):
        return obj.comments.count()

    @admin.display(description="👍")
    def get_likes(self, obj):
        return obj.reactions.filter(reaction=PostReactions.LIKE).count()

    @admin.display(description="👎")
    def get_dislikes(self, obj):
        return obj.reactions.filter(reaction=PostReactions.DISLIKE).count()

    @admin.display(description="👁️‍🗨️")
    def get_views(self, obj):
        return obj.views.count()

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CommentAdmin(ModelAdmin):
    list_display = [
        "id",
        "show_user_link",
        "show_post_link",
        "get_content_preview",
        "show_parent_link",
        "get_replies",
        "get_likes",
        "get_dislikes",
        "date_created",
    ]
    list_display_links = [
        "id",
        "get_content_preview",
    ]
    search_fields = [
        "user__uuid",
        "user__email",
        "user__username",
        "post__id",
    ]
    ordering = ["id"]
    inlines = [RepliesInline]

    @admin.display(description="User")
    def show_user_link(self, obj):
        url = reverse("admin:users_user_change", args=(obj.user.pk,))
        return format_html(f"<a href='{url}'>{obj.user}</a>")

    @admin.display(description="Post")
    def show_post_link(self, obj):
        url = reverse("admin:board_post_change", args=(obj.post.pk,))
        return format_html(f"<a href='{url}'>{obj.post}</a>")

    @admin.display(description="Parent")
    def show_parent_link(self, obj):
        url = reverse(
            "admin:board_comment_change", args=(obj.parent.pk if obj.parent else None,)
        )
        return format_html(f"<a href='{url}'>{obj.parent}</a>") if obj.parent else "-"

    @admin.display(description="Content")
    def get_content_preview(self, obj):
        return obj.content[:100] if obj.content else obj.content

    @admin.display(description="Replies")
    def get_replies(self, obj):
        return obj.replies.count()

    @admin.display(description="👍")
    def get_likes(self, obj):
        return obj.reactions.filter(reaction=PostReactions.LIKE).count()

    @admin.display(description="👎")
    def get_dislikes(self, obj):
        return obj.reactions.filter(reaction=PostReactions.DISLIKE).count()

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Level, LevelAdmin)
admin.site.register(UserLevels, UserLevelsAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
