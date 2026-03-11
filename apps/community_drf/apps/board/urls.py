from rest_framework import routers

from lib.views import BaseAPIListView
from board.views import (
    PostViewSet,
    PostReactionsViewSet,
    PostViewsViewSet,
    CommentViewSet,
    CommentReactionsViewSet,
)


class BoardAPIListView(BaseAPIListView):
    """
    List of Board APIs
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = BoardAPIListView
    root_view_name = "board-root"


app_name = "board"

router = DocumentedRouter()
router.register(r"posts", PostViewSet)
router.register(r"post-reactions", PostReactionsViewSet)
router.register(r"post-views", PostViewsViewSet)
router.register(r"comments", CommentViewSet)
router.register(r"comment-reactions", CommentReactionsViewSet)

urlpatterns = router.urls
