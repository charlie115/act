from django.contrib import admin

from unfold.admin import ModelAdmin, TabularInline

from board.models import PostCategory, Post, Comment


class PostCategoryAdmin(ModelAdmin):
    list_display = ["id", "name", "code"]
    search_fields = ["name", "code"]


class RepliesInline(TabularInline):
    model = Comment
    fields = ["get_id", "user", "content", "date_created"]
    readonly_fields = ["get_id", "date_created"]
    verbose_name = "Reply"
    verbose_name_plural = "Replies"
    show_change_link = True
    extra = 0

    def get_id(self, obj):
        return obj.id

    get_id.short_description = "ID"
    get_id.allow_tags = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(parent__isnull=False)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CommentsInline(TabularInline):
    model = Comment
    readonly_fields = ["get_id", "date_created"]
    fields = ["get_id", "user", "content", "date_created"]
    show_change_link = True
    extra = 0

    def get_id(self, obj):
        return obj.id

    get_id.short_description = "ID"
    get_id.allow_tags = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(parent__isnull=True)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class PostAdmin(ModelAdmin):
    list_display = [
        "id",
        "title",
        "user",
        "date_created",
        "category",
        "get_comments",
        "get_likes",
        "get_views",
    ]

    list_filter = [
        "category",
    ]
    search_fields = [
        "title",
        "user",
    ]
    ordering = ["id"]
    inlines = [CommentsInline]

    def get_comments(self, obj):
        return len(obj.comments.all())

    get_comments.short_description = "Comments"
    get_comments.allow_tags = True

    def get_likes(self, obj):
        return len(obj.likes.all())

    get_likes.short_description = "Likes"
    get_likes.allow_tags = True

    def get_views(self, obj):
        return len(obj.views.all())

    get_views.short_description = "Views"
    get_views.allow_tags = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CommentAdmin(ModelAdmin):
    list_display = [
        "id",
        "user",
        "post",
        "parent",
        "date_created",
    ]
    search_fields = [
        "user",
        "post",
    ]
    ordering = ["id"]
    inlines = [RepliesInline]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(PostCategory, PostCategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
